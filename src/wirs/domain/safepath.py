"""SafePath: path relativo canônico confinado ao root (ADR-008). Só stdlib.

Confinamento é LEXICAL (sem tocar o filesystem): `..` que escapa, path
absoluto, drive (`C:...`) e UNC são rejeitados com SecurityBoundaryError.
Escape via symlink é tratado no inventory (lstat, nunca follow) — aqui o
`full` é construído por junção, nunca resolvido.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from wirs.domain.errors import SecurityBoundaryError

_ABSOLUTE = re.compile(r"^(?:/|[A-Za-z]:|\\\\)")


def _confine(raw: str) -> str:
    if "\x00" in raw:
        raise SecurityBoundaryError("path contém byte NUL")
    normalized = unicodedata.normalize("NFC", raw)
    if _ABSOLUTE.match(normalized.replace("\\", "/")):
        raise SecurityBoundaryError(f"path absoluto fora do root: {raw!r}")
    parts: list[str] = []
    for seg in normalized.replace("\\", "/").split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if not parts:
                raise SecurityBoundaryError(f"escape do root: {raw!r}")
            parts.pop()
            continue
        parts.append(seg)
    return "/".join(parts)


@dataclass(frozen=True)
class SafePath:
    root: Path
    relative: str

    def __init__(self, root: str | Path, raw: str) -> None:
        anchor = Path(root)
        if not anchor.is_absolute():
            raise SecurityBoundaryError(f"root precisa ser absoluto: {root!r}")
        object.__setattr__(self, "root", anchor)
        object.__setattr__(self, "relative", _confine(raw))

    @property
    def full(self) -> Path:
        # Construção por concatenação em parse ÚNICO e ancorado: joinpath
        # descarta o root quando um segmento parece absoluto para o OS
        # (ex.: `::` no Windows vira drive e `C:x` é drive-relative).
        # Como `relative` nunca começa com `/` nem contém `..`, o resultado
        # fica lexicalmente contido no root qualquer que seja o segmento.
        if not self.relative:
            return self.root
        return Path(f"{self.root}/{self.relative}")

    def __str__(self) -> str:
        return self.relative
