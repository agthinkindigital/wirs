"""Extração segura de ZIP para baseline (WIRS-043). Só stdlib.

Defesas (spec 16.7 + 16.11):
- zip-slip: entry absoluta ou com `..` é rejeitada (SecurityBoundaryError);
- symlink entry nunca é materializada como link (vira arquivo regular só se for
  conteúdo real? não — é ignorada: baseline é hash de conteúdo regular);
- bomba: limites de arquivos e bytes expandidos (BudgetExceeded);
- nunca executa nada: extração copia bytes, sem lifecycle script.
"""

from __future__ import annotations

import shutil
import stat
import zipfile
from pathlib import Path

from wirs.domain.errors import BudgetExceeded, SecurityBoundaryError

MAX_ARCHIVE_FILES = 50_000
MAX_ARCHIVE_BYTES = 1 << 30


def _destino_seguro(dest: Path, nome: str) -> Path:
    puro = nome.replace("\\", "/").lstrip("/")
    partes = [p for p in puro.split("/") if p not in ("", ".")]
    if not partes or any(p == ".." for p in partes):
        raise SecurityBoundaryError(f"entry fora do destino: {nome!r}")
    return dest.joinpath(*partes)


def extract_zip_safely(
    archive: Path,
    dest: Path,
    *,
    max_files: int = MAX_ARCHIVE_FILES,
    max_bytes: int = MAX_ARCHIVE_BYTES,
) -> Path:
    """Extrai ZIP em `dest` (criado se preciso). Retorna `dest`."""
    try:
        zf = zipfile.ZipFile(archive)
    except (zipfile.BadZipFile, OSError) as e:
        raise SecurityBoundaryError(f"archive ilegível: {archive} ({e})") from e
    with zf:
        infos = zf.infolist()
        if len(infos) > max_files:
            raise BudgetExceeded(f"archive com {len(infos)} entries (limite {max_files})")
        total = 0
        for info in infos:
            total += info.file_size
            if total > max_bytes:
                raise BudgetExceeded(f"expansão além de {max_bytes} bytes", bytes_read=total)
        dest.mkdir(parents=True, exist_ok=True)
        for info in infos:
            alvo = _destino_seguro(dest, info.filename)
            if info.is_dir():
                alvo.mkdir(parents=True, exist_ok=True)
                continue
            if stat.S_ISLNK((info.external_attr >> 16) & 0o170000):
                continue  # symlink entry: nunca materializa link fora/dentro
            alvo.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as src, open(alvo, "wb") as out:
                shutil.copyfileobj(src, out)
    return dest
