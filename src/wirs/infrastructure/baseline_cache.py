"""Cache local de manifests (WIRS-045). Só stdlib.

Layout: `<root>/<component_id>/<version>.json` com envelope
{manifest, cached_at, origin}. Nomes validados (sem travessia).
Staleness é dado (idade), não expiração: quem consome declara a idade.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wirs.domain import BaselineManifest

_SEGMENTO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def default_cache_dir() -> Path:
    return Path.home() / ".wirs" / "cache" / "baselines"


@dataclass(frozen=True)
class CachedBaseline:
    manifest: BaselineManifest
    cached_at: datetime
    origin: str

    @property
    def age_days(self) -> int:
        return max(0, (datetime.now(UTC) - self.cached_at).days)


def _segmento(valor: str, o_que: str) -> str:
    if not _SEGMENTO.match(valor):
        raise ValueError(f"{o_que} fora do contrato para cache: {valor!r}")
    return valor


class BaselineCache:
    def __init__(self, root: Path | None = None) -> None:
        self._root = Path(root) if root is not None else default_cache_dir()

    def store(self, manifest: BaselineManifest, *, origin: str) -> Path:
        """Guarda manifest com provenance. Retorna o arquivo (escrita atômica)."""
        if not origin.strip():
            raise ValueError("origin obrigatória (provenance do cache)")
        dest = (
            self._root
            / _segmento(manifest.component_id, "component_id")
            / f"{_segmento(manifest.version, 'version')}.json"
        )
        envelope = {
            "manifest": manifest.to_dict(),
            "cached_at": datetime.now(UTC).isoformat(),
            "origin": origin.strip(),
        }
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=dest.name + ".", dir=dest.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(envelope, fh, indent=2, ensure_ascii=False)
            os.replace(tmp_name, dest)
        except OSError:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        return dest

    def load(self, component_id: str, version: str) -> CachedBaseline | None:
        """Lê do cache. Ausente/corrompido = None (chamador decide o fallback)."""
        dest = (
            self._root
            / _segmento(component_id, "component_id")
            / f"{_segmento(version, 'version')}.json"
        )
        try:
            envelope: dict[str, Any] = json.loads(dest.read_text(encoding="utf-8"))
            manifest = BaselineManifest.from_dict(envelope["manifest"])
            cached_at = datetime.fromisoformat(str(envelope["cached_at"]))
            origin = str(envelope["origin"])
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return None
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=UTC)
        return CachedBaseline(manifest=manifest, cached_at=cached_at, origin=origin)
