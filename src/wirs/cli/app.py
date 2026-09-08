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

import json
from enum import IntEnum
from pathlib import Path

import typer
from rich.console import Console

from wirs import __version__

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
    """Executa um scan read-only sobre o target (pipeline completo — em construção)."""
    if profile not in ("soft", "balanced", "fast"):
        console.print(f"[red]Perfil inválido:[/red] {profile}")
        raise typer.Exit(code=ExitCode.INVALID_TARGET)
    if not target.exists() or not target.is_dir():
        console.print(f"[red]Target inválido:[/red] {target} (diretório inexistente)")
        raise typer.Exit(code=ExitCode.INVALID_TARGET)

    # Skeleton honesto (Fase A): engine ainda não implementada — scan incompleto,
    # coverage explícito, sem nenhum finding fabricado.
    skeleton = {
        "schema_version": "1.0",
        "scanner_version": __version__,
        "status": "incomplete",
        "target": str(target),
        "profile": profile,
        "findings": [],
        "coverage": {"filesystem": "NOT_APPLICABLE"},
        "note": "ScanOrchestrator ainda não implementado (Fase A — Skeleton).",
    }
    if format_ == "json":
        console.print_json(json.dumps(skeleton))
    else:
        console.print("[yellow]Scan incompleto:[/yellow] engine em construção (Fase A).")
        console.print(f"Target: {target} | Profile: {profile} | Coverage: NOT_APPLICABLE")
    raise typer.Exit(code=ExitCode.INCOMPLETE)


def main() -> None:
    app()
