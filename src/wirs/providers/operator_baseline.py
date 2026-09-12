"""Provider de baseline do operador: mapping path→manifest (WIRS-066).

Componente mapeado é verificado com o comparator (#49): tudo match vira
`covers` (absolve como baseline confiável); divergência vira FileIntegrity
para findings. Diretório de plugin/theme sem mapping vira UNVERIFIED com
nota acionável — nunca "malicioso".
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path

from wirs.domain import BaselineManifest, Target, compare_baseline
from wirs.domain.errors import ProviderInvalidOutput
from wirs.domain.integrity import IntegrityState
from wirs.infrastructure.baseline import BaselineBuilder
from wirs.ports.checksum import ComponentIntegrity

PROVIDER_ID = "operator-baseline"

_COMPONENT_DIRS = ("wp-content/plugins", "wp-content/themes")


def load_baseline_mapping(path: Path) -> dict[str, Path]:
    """Lê mapping JSON {dir-relativo: manifest}. Erro vira ValueError."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise ValueError(f"mapping ilegível: {path} ({e})") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"mapping inválido: {path} ({e})") from e
    if not isinstance(data, dict):
        raise ValueError(f"mapping precisa ser objeto: {path}")
    mapping: dict[str, Path] = {}
    for rel, manifest in data.items():
        if not isinstance(rel, str) or not isinstance(manifest, str):
            raise ValueError(f"entrada inválida no mapping: {rel!r}")
        normalizado = rel.replace("\\", "/").strip("/")
        if not normalizado or normalizado.startswith(".") or ".." in normalizado.split("/"):
            raise ValueError(f"dir fora do contrato no mapping: {rel!r}")
        mapping[normalizado] = Path(manifest)
    return mapping


def _load_manifest(path: Path) -> BaselineManifest:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise ProviderInvalidOutput(f"manifest ilegível: {path} ({e})") from e
    except json.JSONDecodeError as e:
        raise ProviderInvalidOutput(f"manifest inválido: {path} ({e})") from e
    try:
        manifest = BaselineManifest.from_dict(data)
    except (ValueError, KeyError, TypeError) as e:
        raise ProviderInvalidOutput(f"manifest fora do schema: {path} ({e})") from e
    return manifest


def _slug(rel: str) -> str:
    nome = rel.split("/")[-1]
    kind = "plugin" if rel.startswith("wp-content/plugins/") else "theme"
    return f"{kind}:{nome}"


class OperatorBaselineIntegrity:
    """Adapter mapping do operador → seam IntegrityProvider (montado via --baseline)."""

    id = PROVIDER_ID
    platforms: tuple[str, ...] = ("wordpress",)

    def __init__(self, mapping: Mapping[str, Path]) -> None:
        self._mapping = dict(mapping)
        self._builder = BaselineBuilder()

    def verify(self, target: Target) -> list[ComponentIntegrity]:
        out: list[ComponentIntegrity] = []
        for rel, manifest_path in sorted(self._mapping.items()):
            manifest = _load_manifest(manifest_path)
            atual = self._builder.build(
                target.root / rel, component_id=manifest.component_id, version=manifest.version
            )
            files = tuple(
                item
                for item in compare_baseline(manifest, dict(atual.files))
                if item.state is not IntegrityState.MATCH
            )
            out.append(
                ComponentIntegrity(
                    provider_id=PROVIDER_ID,
                    provider_version=None,
                    component=_slug(rel),
                    files=files,
                    covers=(f"{rel}/",),
                    trust=manifest.trust,
                )
            )
        for rel in sorted(_sem_mapping(target, self._mapping)):
            out.append(
                ComponentIntegrity(
                    provider_id=PROVIDER_ID,
                    provider_version=None,
                    component=_slug(rel),
                    unverified=True,
                )
            )
        return out


def _sem_mapping(target: Target, mapping: Mapping[str, Path]) -> list[str]:
    """Dirs de plugin/theme sem manifest mapeado (UNVERIFIED explícito)."""
    achados: list[str] = []
    for base in _COMPONENT_DIRS:
        try:
            entries = sorted(os.scandir(target.root / base), key=lambda e: e.name)
        except OSError:
            continue
        for entry in entries:
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError:
                continue
            if not is_dir:
                continue
            rel = f"{base}/{entry.name}"
            if rel not in mapping:
                achados.append(rel)
    return achados
