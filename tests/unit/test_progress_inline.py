"""Progresso mesma-linha no terminal (melhoria #55)."""

from __future__ import annotations

import io

from rich.console import Console

from wirs.application.orchestrator import ProgressEvent
from wirs.cli.progress import CliProgress


def test_detect_sobrescreve_mesma_linha_no_terminal() -> None:
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, width=100, highlight=False)
    prog = CliProgress(console=console, intervalo_s=0)
    prog(ProgressEvent(phase="detect", current=1, total=3, detail="a.php"))
    prog(ProgressEvent(phase="detect", current=2, total=3, detail="b.php"))

    out = buf.getvalue()
    assert "\n" not in out
    assert "\r" in out
    assert "b.php" in out


def test_piped_mantem_linhas() -> None:
    buf = io.StringIO()
    prog = CliProgress(console=Console(file=buf, force_terminal=False, width=100), intervalo_s=0)
    prog(ProgressEvent(phase="detect", current=1, total=3, detail="a.php"))
    prog(ProgressEvent(phase="detect", current=2, total=3, detail="b.php"))

    linhas = [ln for ln in buf.getvalue().splitlines() if ln.strip()]
    assert len(linhas) == 2
