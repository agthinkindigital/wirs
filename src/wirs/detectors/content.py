"""Hints de conteúdo no passo único de leitura (WIRS-054).

Um passo sobre os bytes serve N hints: `executable` reutiliza
`looks_executable` (nada duplicado) e `is_text` decide texto/binário.
O scheduler futuro pluga esta função no stream compartilhado; a assinatura
já é a final: bytes entram, hints imutáveis saem.
"""

from __future__ import annotations

from dataclasses import dataclass

from wirs.detectors.executable import looks_executable


@dataclass(frozen=True)
class ContentHints:
    is_text: bool
    executable: bool


def _is_text(head: bytes) -> bool:
    if b"\x00" in head:
        return False
    try:
        head.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def extract_hints(head: bytes) -> ContentHints:
    return ContentHints(is_text=_is_text(head), executable=looks_executable(head))
