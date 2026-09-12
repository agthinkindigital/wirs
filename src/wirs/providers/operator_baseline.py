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
from wirs.domain.integrity import FileIntegrity, IntegrityState
from wirs.infrastructure.baseline import BaselineBuilder
from wirs.infrastructure.baseline_cache import BaselineCache, CachedBaseline
from wirs.infrastructure.baseline_sign import (
    SignatureInvalid,
    SignatureMissing,
    SignatureNotChecked,
    check_signature,
    sig_path,
)
from wirs.ports.checksum import ComponentIntegrity

PROVIDER_ID = "operator-baseline"

_COMPONENT_DIRS = ("wp-content/plugins", "wp-content/themes")


def load_baseline_mapping(path: Path) -> dict[str, str]:
    """Lê mapping JSON {dir-relativo: manifest-arquivo | cache:id:versão}."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise ValueError(f"mapping ilegível: {path} ({e})") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"mapping inválido: {path} ({e})") from e
    if not isinstance(data, dict):
        raise ValueError(f"mapping precisa ser objeto: {path}")
    mapping: dict[str, str] = {}
    for rel, manifest in data.items():
        if not isinstance(rel, str) or not isinstance(manifest, str):
            raise ValueError(f"entrada inválida no mapping: {rel!r}")
        normalizado = rel.replace("\\", "/").strip("/")
        if not normalizado or normalizado.startswith(".") or ".." in normalizado.split("/"):
            raise ValueError(f"dir fora do contrato no mapping: {rel!r}")
        if not manifest.strip():
            raise ValueError(f"manifest vazio no mapping para {rel!r}")
        mapping[normalizado] = manifest.strip()
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

    def __init__(
        self,
        mapping: Mapping[str, str],
        cache: BaselineCache | None = None,
        sign_key: bytes | None = None,
    ) -> None:
        self._mapping = dict(mapping)
        self._builder = BaselineBuilder()
        self._cache = cache
        self._sign_key = sign_key

    def _resolve(self, ref: str) -> tuple[BaselineManifest, str]:
        """Manifest de arquivo ou `cache:id:versão`. Retorna (manifest, staleness)."""
        if ref.startswith("cache:"):
            if self._cache is None:
                raise ProviderInvalidOutput(f"mapping usa cache sem cache configurado: {ref!r}")
            try:
                _, component_id, version = ref.split(":", 2)
                cached: CachedBaseline | None = self._cache.load(component_id, version)
            except ValueError as e:
                raise ProviderInvalidOutput(f"ref de cache inválida: {ref!r} ({e})") from e
            if cached is None:
                raise ProviderInvalidOutput(f"cache sem {ref!r} (rode `baseline cache-store`)")
            return cached.manifest, f"cache de {cached.age_days}d, origem {cached.origin}"
        manifest = _load_manifest(Path(ref))
        sig = sig_path(Path(ref))
        if sig.exists():
            if self._sign_key is None:
                raise SignatureNotChecked(f"assinatura presente mas sem chave (--sign-key): {ref}")
            try:
                check_signature(Path(ref), self._sign_key)
            except (SignatureMissing, SignatureInvalid) as e:
                raise ProviderInvalidOutput(str(e)) from e
        return manifest, ""

    def verify(self, target: Target) -> list[ComponentIntegrity]:
        out: list[ComponentIntegrity] = []
        for rel, ref in sorted(self._mapping.items()):
            try:
                manifest, staleness = self._resolve(ref)
            except SignatureNotChecked as e:
                out.append(
                    ComponentIntegrity(
                        provider_id=PROVIDER_ID,
                        provider_version=None,
                        component=_slug(rel),
                        unverified=True,
                        note=str(e),
                    )
                )
                continue
            atual = self._builder.build(
                target.root / rel, component_id=manifest.component_id, version=manifest.version
            )
            compared = compare_baseline(manifest, dict(atual.files))
            files = tuple(
                FileIntegrity(
                    path=item.path,
                    state=item.state,
                    expected=item.expected,
                    actual=item.actual,
                    note=(f"{staleness}; {item.note}".strip("; ") if staleness else item.note),
                )
                for item in compared
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


def _sem_mapping(target: Target, mapping: Mapping[str, str]) -> list[str]:
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
