"""Entry point Typer do WIRS.

Exit codes (Seção 10.8 do spec):
  0   scan completo, nenhum finding no fail threshold
  1   scan completo, finding atingiu fail threshold
  2   target/argumento/config inválido
  3   scan incompleto por falha crítica de coleta
  4   erro interno do scanner
  5   rule pack/configuração inválida
  130 interrompido pelo operador
"""

from __future__ import annotations

import uuid
from collections import Counter
from enum import IntEnum
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from wirs import __version__
from wirs.domain import (
    Artifact,
    CoverageEntry,
    CoverageState,
    LocalDirectoryTarget,
    TargetError,
)
from wirs.infrastructure import InventoryGap, LocalArtifactSource
from wirs.reporting import CanonicalReport, render_report

# Budgets provisórios por perfil até WIRS-034 (large-file policy).
PROFILE_BUDGETS = {"soft": 64 << 20, "balanced": 256 << 20, "fast": 1 << 30}

app = typer.Typer(
    name="wirs",
    help="WordPress Incident Response Scanner — scan read-only, evidence-first.",
    no_args_is_help=True,
)
console = Console()


class ExitCode(IntEnum):
    OK = 0
    FINDINGS_OVER_THRESHOLD = 1
    INVALID_TARGET = 2
    INCOMPLETE = 3
    INTERNAL_ERROR = 4
    INVALID_RULEPACK = 5


@app.command()
def version() -> None:
    """Exibe a versão do scanner."""
    console.print(f"wirs {__version__}")


@app.command()
def doctor() -> None:
    """Verifica runtime, providers disponíveis e configuração (WIRS-112)."""
    import shutil
    import sys

    console.print(f"[bold]wirs[/bold] {__version__} — Python {sys.version.split()[0]}")
    for tool in ("wp", "yara", "wordfence"):
        found = shutil.which(tool)
        state = f"[green]available[/green] ({found})" if found else "[yellow]unavailable[/yellow]"
        console.print(f"  {tool}: {state}")


@app.command()
def scan(
    target: Path = typer.Argument(..., help="Diretório local ou snapshot a analisar."),
    profile: str = typer.Option("soft", help="Perfil de recursos: soft, balanced, fast."),
    format_: str = typer.Option("terminal", "--format", help="Formato de saída: terminal, json."),
) -> None:
    """Executa um scan read-only sobre o target (Fase A: inventory + report)."""
    if profile not in PROFILE_BUDGETS:
        console.print(f"[red]Perfil inválido:[/red] {profile}")
        raise typer.Exit(code=ExitCode.INVALID_TARGET)
    if format_ not in ("terminal", "json"):
        console.print(f"[red]Formato inválido:[/red] {format_}")
        raise typer.Exit(code=ExitCode.INVALID_TARGET)
    try:
        tgt = LocalDirectoryTarget(target)
    except TargetError as e:
        console.print(f"[red]Target inválido:[/red] {e}")
        raise typer.Exit(code=ExitCode.INVALID_TARGET) from e

    kinds: Counter[str] = Counter()
    gaps = 0
    for item in LocalArtifactSource().iter_artifacts(tgt):
        if isinstance(item, Artifact):
            kinds[item.kind.value] += 1
        elif isinstance(item, InventoryGap):
            gaps += 1
    verified = sum(kinds.values())
    coverage = CoverageEntry(
        capability="filesystem",
        state=CoverageState.PARTIAL if gaps else CoverageState.COMPLETE,
        applicable_checks=verified + gaps,
        verified=verified,
        failed=gaps,
        note="detection em construção (Fase A)" if gaps else "",
    )
    report = CanonicalReport(
        scan_id=f"scan_{uuid.uuid4().hex[:12]}",
        target_root=str(tgt.root),
        profile=profile,
        findings=(),
        coverage=(coverage,),
        note="Fase A: inventory + report. Detecção chega na Fase B.",
    )
    if format_ == "json":
        console.print_json(report.to_json())
    else:
        _print_terminal(report, kinds)
    # Pipeline incompleto por construção: detectores ainda não existem.
    raise typer.Exit(code=ExitCode.INCOMPLETE)


def _print_terminal(report: CanonicalReport, kinds: Counter[str]) -> None:
    console.print(
        f"[bold]wirs[/bold] {__version__} · Target: {report.target_root} "
        f"· Profile: {report.profile} · Mode: read-only"
    )
    inventory = Table(title="Inventory")
    inventory.add_column("Kind")
    inventory.add_column("Count", justify="right")
    for kind in sorted(kinds):
        inventory.add_row(kind, str(kinds[kind]))
    console.print(inventory)
    render_report(report, console)
    console.print("[yellow]Scan incompleto:[/yellow] detecção em construção (Fase A).")


def main() -> None:
    app()
