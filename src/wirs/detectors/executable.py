"""Detectores internos de conteúdo (genéricos, sem conceito de plataforma).

`looks_executable` responde "este conteúdo parece executável?" — *onde* isso
é proibido é decisão de policy do adapter (ex.: uploads no WordPress).
"""

from __future__ import annotations


def looks_executable(head: bytes) -> bool:
    """Heurística barata sobre os primeiros bytes. `<?xml` não é PHP."""
    text = head.lstrip()[:64].lower()
    if not text:
        return False
    if text.startswith((b"<?php", b"<?=", b"#!", b"<script")):
        return True
    return text.startswith(b"<?") and not text.startswith(b"<?xml")
