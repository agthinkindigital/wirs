"""Baseline Manifest: expectativa confiável para comparação (spec 3.6). Só stdlib.

Paths sempre relativos posix canônicos: `..`, absoluto, NUL e vazio são
rejeitados na construção (manifest hostil não atravessa na leitura).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any

from wirs.domain.integrity import FileIntegrity, IntegrityState

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class BaselineTrust(Enum):
    TRUSTED_UPSTREAM = "trusted_upstream"
    TRUSTED_OPERATOR = "trusted_operator"
    TRUSTED_SIGNED_INTERNAL = "trusted_signed_internal"
    UNVERIFIED_REFERENCE = "unverified_reference"


def _canonical_path(raw: str) -> str:
    if not raw or "\x00" in raw:
        raise ValueError(f"path de manifest inválido: {raw!r}")
    normalized = raw.replace("\\", "/")
    if normalized.startswith("/") or normalized.startswith("~"):
        raise ValueError(f"path absoluto fora do manifest: {raw!r}")
    parts: list[str] = []
    for seg in normalized.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if not parts:
                raise ValueError(f"travessia em manifest: {raw!r}")
            parts.pop()
            continue
        parts.append(seg)
    if not parts:
        raise ValueError(f"path vazio após normalização: {raw!r}")
    return "/".join(parts)


def _hex64(value: str, what: str) -> str:
    lowered = value.lower()
    if not _HEX64.match(lowered):
        raise ValueError(f"{what} exige 64 hex: {value!r:.40}")
    return lowered


@dataclass(frozen=True)
class BaselineManifest:
    component_id: str
    version: str
    source: str
    trust: BaselineTrust
    files: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    package_hash: str = ""
    created_at: datetime | None = None
    id: str = ""

    def __post_init__(self) -> None:
        if not self.component_id:
            raise ValueError("component_id obrigatório")
        normalized: dict[str, str] = {}
        for raw_path, digest in dict(self.files).items():
            path = _canonical_path(raw_path)
            if path in normalized:
                raise ValueError(f"path duplicado no manifest: {path!r}")
            normalized[path] = _hex64(digest, f"hash de {path!r}")
        object.__setattr__(self, "files", MappingProxyType(normalized))
        if self.package_hash:
            object.__setattr__(self, "package_hash", _hex64(self.package_hash, "package_hash"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "component_id": self.component_id,
            "version": self.version,
            "source": self.source,
            "trust": self.trust.value,
            "files": dict(self.files),
            "package_hash": self.package_hash,
            "created_at": None if self.created_at is None else self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BaselineManifest:
        created = data.get("created_at")
        return cls(
            component_id=str(data["component_id"]),
            version=str(data.get("version", "")),
            source=str(data.get("source", "")),
            trust=BaselineTrust(str(data["trust"])),
            files=dict(data.get("files", {})),
            package_hash=str(data.get("package_hash", "")),
            created_at=None if created is None else datetime.fromisoformat(str(created)),
            id=str(data.get("id", "")),
        )


def compare_baseline(
    manifest: BaselineManifest, actual: Mapping[str, str]
) -> tuple[FileIntegrity, ...]:
    """Compara manifest contra hashes reais: match/mismatch/missing/unexpected."""
    restante = dict(actual)
    resultado: list[FileIntegrity] = []
    for path, expected in manifest.files.items():
        digest = restante.pop(path, None)
        if digest is None:
            resultado.append(
                FileIntegrity(path=path, state=IntegrityState.MISSING, expected=expected)
            )
        elif digest == expected:
            resultado.append(
                FileIntegrity(
                    path=path, state=IntegrityState.MATCH, expected=expected, actual=digest
                )
            )
        else:
            resultado.append(
                FileIntegrity(
                    path=path, state=IntegrityState.MISMATCH, expected=expected, actual=digest
                )
            )
    for path, digest in restante.items():
        resultado.append(FileIntegrity(path=path, state=IntegrityState.UNEXPECTED, actual=digest))
    return tuple(resultado)
