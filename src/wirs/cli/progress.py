"""Progresso do scan: --cli (linhas em stderr) e --gui (tela Rich Live).

Regras (WIRS-139 + ui-ux-pro-max: step indicators, sem UI congelada):
- stdout é sagrado (JSON parseável): tudo visual vai para stderr;
- paths do alvo são neutralizados (sanitize) antes de exibir;
- throttle por tempo: sem flood em árvore grande;
- sem TTY, o --gui degrada para saída simples sem quebrar.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field

from rich.console import Console
from rich.live import Live
from rich.table import Table

from wirs.application.orchestrator import ProgressEvent
from wirs.reporting import sanitize

_FASES = ("inventory", "discovery", "integrity", "detect", "done")


@dataclass
class CliProgress:
    """Guia visual mínimo em stderr: fases + arquivo atual (throttle)."""

    console: Console | None = None
    intervalo_s: float = 2.0
    _ultimo: float = field(default=0.0, init=False, repr=False)
    _total: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.console is None:
            self.console = Console(file=sys.stderr, highlight=False)

    def __call__(self, evento: ProgressEvent) -> None:
        console = self.console or Console(file=sys.stderr, highlight=False)
        if evento.phase == "inventory":
            console.print(f"\\[1/4] inventory … {evento.current} artifacts")
        elif evento.phase == "discovery":
            console.print(f"\\[2/4] discovery … {sanitize(evento.detail)}")
        elif evento.phase == "integrity":
            console.print(f"\\[3/4] integrity … {evento.current}/{evento.total}")
        elif evento.phase == "detect":
            self._total = evento.total
            agora = time.monotonic()
            if agora - self._ultimo >= self.intervalo_s:
                self._ultimo = agora
                atual = sanitize(evento.detail)
                console.print(f"\\[4/4] detect … {evento.current}/{evento.total} · {atual}")
        elif evento.phase == "done":
            console.print(f"\\[done] {evento.current} findings em {self._total} arquivos")


@dataclass
class GuiProgress:
    """Tela de acompanhamento Rich Live em stderr (opt-in via --gui)."""

    console: Console | None = None
    cap_findings: int = 50
    _fases: dict[str, str] = field(default_factory=dict, init=False, repr=False)
    _atual: str = field(default="", init=False, repr=False)
    _live: Live | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.console is None:
            self.console = Console(file=sys.stderr, highlight=False)

    def _tabela(self) -> Table:
        tabela = Table(title="wirs · scan em andamento", show_header=True)
        tabela.add_column("Etapa")
        tabela.add_column("Estado")
        for fase in _FASES:
            tabela.add_row(fase, self._fases.get(fase, "…"))
        tabela.add_row("arquivo atual", self._atual or "…")
        return tabela

    def __call__(self, evento: ProgressEvent) -> None:
        console = self.console or Console(file=sys.stderr, highlight=False)
        if self._live is None:
            self._live = Live(self._tabela(), console=console, refresh_per_second=4)
            self._live.start()
        if evento.phase == "detect":
            self._atual = sanitize(evento.detail)
            self._fases["detect"] = f"{evento.current}/{evento.total}"
        else:
            self._fases[evento.phase] = evento.detail or f"{evento.current}/{evento.total}"
        live = self._live
        if live is not None:
            live.update(self._tabela())
            if evento.phase == "done":
                live.stop()
                self._live = None
        if evento.phase == "done":
            console.print(f"\\[done] {evento.current} findings")
