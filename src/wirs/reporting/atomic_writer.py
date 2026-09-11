"""Writer atômico de reports (WIRS-094/WIRS-119). Só stdlib.

Garante: arquivo incompleto nunca é apresentado como final — escreve em
temporário no mesmo diretório e renomeia (operação atômica no mesmo
filesystem). Falha no meio = só o temporário (removido na limpeza).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def write_text_atomic(dest: Path, text: str) -> None:
    """Grava texto em `dest` atomicamente. Erro vira OSError sem parcial."""
    dest = Path(dest)
    parent = dest.parent
    try:
        fd, tmp_name = tempfile.mkstemp(prefix=dest.name + ".", dir=parent)
    except OSError as e:
        raise OSError(f"não consegui escrever em {parent} ({e})") from e
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp_name, dest)
    except OSError:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
