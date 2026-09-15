"""Manifesto e fonte de artifacts para Incident Bundle local (WIRS-130)."""

from __future__ import annotations

import json
import os
import stat
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from wirs.domain import Artifact, ArtifactKind, BaselineTrust, SafePath, Target, TargetKind
from wirs.domain.errors import SecurityBoundaryError, TargetError
from wirs.infrastructure.filesystem import InventoryGap, LocalArtifactSource

BUNDLE_MANIFEST = "wirs-bundle.json"
BUNDLE_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class BundleSource:
    source_ref: str
    path: str
    role: str
    origin: str
    sha256: str
    trust: BaselineTrust

    def to_dict(self) -> dict[str, str]:
        return {
            "source_ref": self.source_ref,
            "path": self.path,
            "role": self.role,
            "origin": self.origin,
            "sha256": self.sha256,
            "trust": self.trust.value,
        }


@dataclass(frozen=True)
class BundleManifest:
    root: Path
    sources: tuple[BundleSource, ...]
    schema_version: str = BUNDLE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "sources": [source.to_dict() for source in self.sources],
        }


def _relative_source_path(root: Path, value: str) -> Path:
    normalized = value.replace("\\", "/")
    candidate = Path(normalized)
    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    if (
        candidate.is_absolute()
        or normalized.startswith("/")
        or not parts
        or any(part == ".." for part in parts)
    ):
        raise SecurityBoundaryError(f"source path fora do bundle: {value!r}")
    relative = Path(*parts)
    source_path = root / relative
    try:
        resolved = source_path.resolve(strict=False)
    except OSError as exc:
        raise SecurityBoundaryError(f"source path não pode ser resolvido: {value!r}") from exc
    if resolved != root and root not in resolved.parents:
        raise SecurityBoundaryError(f"source path escapa do bundle: {value!r}")
    if source_path.is_symlink():
        raise SecurityBoundaryError(f"source path é symlink: {value!r}")
    return relative


def _parse_source(root: Path, raw: Mapping[str, Any]) -> BundleSource:
    try:
        source_ref = str(raw["source_ref"])
        relative = _relative_source_path(root, str(raw["path"]))
        role = str(raw["role"])
        origin = str(raw["origin"])
        digest = str(raw["sha256"]).lower()
        trust = BaselineTrust(str(raw["trust"]).lower())
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"source inválida no manifesto: {raw!r}") from exc
    if not source_ref or any(char in source_ref for char in "/\\:"):
        raise ValueError(f"source_ref inválido: {source_ref!r}")
    valid_digest = len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)
    if not role or not origin or not valid_digest:
        raise ValueError(f"metadados inválidos para source: {source_ref!r}")
    return BundleSource(source_ref, relative.as_posix(), role, origin, digest, trust)


def load_bundle(root: str | Path) -> BundleManifest:
    """Lê e valida o manifesto, sem ler nem modificar as fontes declaradas."""
    bundle_root = Path(root).expanduser()
    manifest_path = bundle_root / BUNDLE_MANIFEST
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TargetError(f"manifesto do bundle ilegível: {manifest_path}") from exc
    if data.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        raise ValueError(f"schema_version de bundle incompatível: {data.get('schema_version')!r}")
    raw_sources = data.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ValueError("manifesto precisa de uma lista não vazia de sources")
    sources = tuple(_parse_source(bundle_root, raw) for raw in raw_sources)
    refs = [source.source_ref for source in sources]
    if len(set(refs)) != len(refs):
        raise ValueError("source_ref duplicado no manifesto")
    return BundleManifest(bundle_root.resolve(), sources)


def bundle_target(manifest: BundleManifest) -> Target:
    return Target(
        kind=TargetKind.INCIDENT_BUNDLE,
        root=manifest.root,
        metadata={"source_manifest": manifest.to_dict()},
    )


class BundleArtifactSource:
    """Combina fontes declaradas, mantendo namespace lógico por source_ref."""

    def __init__(self, manifest: BundleManifest) -> None:
        self.manifest = manifest
        self._local = LocalArtifactSource()

    def iter_artifacts(self, target: Target) -> Iterator[Artifact | InventoryGap]:
        for source in self.manifest.sources:
            source_path = self.manifest.root / source.path
            try:
                st = os.stat(source_path, follow_symlinks=False)
            except OSError:
                yield InventoryGap(SafePath(target.root, source.path), "stat_failed")
                continue
            if stat.S_ISDIR(st.st_mode):
                source_target = Target(kind=TargetKind.LOCAL_DIRECTORY, root=source_path)
                for item in self._local.iter_artifacts(source_target):
                    if isinstance(item, InventoryGap):
                        yield item
                    else:
                        yield replace(item, source_ref=source.source_ref, id="")
            elif stat.S_ISREG(st.st_mode):
                path = SafePath(target.root, source.path)
                yield Artifact.from_stat(ArtifactKind.FILE, path, st, source_ref=source.source_ref)
            else:
                path = SafePath(target.root, source.path)
                yield Artifact.from_stat(
                    ArtifactKind.SPECIAL, path, st, source_ref=source.source_ref
                )
