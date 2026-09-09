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

from collections import Counter
from enum import IntEnum
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from wirs import __version__
from wirs.adapters.wordpress.discovery import WordPressAdapter
from wirs.adapters.wordpress.policies import UploadsExecutablePolicy
from wirs.application.orchestrator import run_scan
from wirs.detectors.builtin import IocDetector, PhpHeuristicsDetector
from wirs.domain import IOC, IOCKind, LocalDirectoryTarget, Severity, TargetError
from wirs.infrastructure import ArtifactReader, LocalArtifactSource
from wirs.infrastructure.reader import ReadBudget
from wirs.providers.wp_checksum import WpCliCoreIntegrity, WpCliPluginIntegrity
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


def load_iocs_file(path: Path) -> list[IOC]:
    """Lê `kind:value` por linha (# comenta, vazias ignoram). Erro vira ValueError."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ValueError(f"arquivo de IOCs ilegível: {path} ({e})") from e
    iocs: list[IOC] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        kind_name, sep, value = line.partition(":")
        try:
            kind = IOCKind(kind_name.strip().lower())
        except ValueError:
            raise ValueError(f"{path}:{lineno}: kind desconhecido: {kind_name!r}") from None
        if not sep or not value.strip():
            raise ValueError(f"{path}:{lineno}: esperado `kind:valor`")
        try:
            iocs.append(IOC(kind=kind, value=value.strip()))
        except ValueError as e:
            raise ValueError(f"{path}:{lineno}: {e}") from e
    return iocs


@app.command()
def scan(
    target: Path = typer.Argument(..., help="Diretório local ou snapshot a analisar."),
    profile: str = typer.Option("soft", help="Perfil de recursos: soft, balanced, fast."),
    format_: str = typer.Option("terminal", "--format", help="Formato de saída: terminal, json."),
    fail_on: str = typer.Option("high", "--fail-on", help="Severidade mínima para exit 1."),
    ioc: Path | None = typer.Option(None, "--ioc", help="Arquivo de IOCs kind:value."),
) -> None:
    """Executa um scan read-only sobre o target (orquestrador v1)."""
    if profile not in PROFILE_BUDGETS:
        console.print(f"[red]Perfil inválido:[/red] {profile}")
        raise typer.Exit(code=ExitCode.INVALID_TARGET)
    if format_ not in ("terminal", "json"):
        console.print(f"[red]Formato inválido:[/red] {format_}")
        raise typer.Exit(code=ExitCode.INVALID_TARGET)
    try:
        threshold = Severity(fail_on)
    except ValueError:
        console.print(f"[red]fail-on inválido:[/red] {fail_on}")
        raise typer.Exit(code=ExitCode.INVALID_TARGET) from None
    try:
        tgt = LocalDirectoryTarget(target)
    except TargetError as e:
        console.print(f"[red]Target inválido:[/red] {e}")
        raise typer.Exit(code=ExitCode.INVALID_TARGET) from e
    ioc_list: list[IOC] = []
    if ioc is not None:
        try:
            ioc_list = load_iocs_file(ioc)
        except ValueError as e:
            console.print(f"[red]IOCs inválidos:[/red] {e}")
            raise typer.Exit(code=ExitCode.INVALID_TARGET) from e

    kinds: Counter[str] = Counter()
    result = run_scan(
        tgt,
        profile=profile,
        source=LocalArtifactSource(),
        adapters=[WordPressAdapter()],
        reader=ArtifactReader(),
        budget=ReadBudget(max_bytes=PROFILE_BUDGETS[profile]),
        detectors=[IocDetector(ioc_list), PhpHeuristicsDetector(), UploadsExecutablePolicy()],
        integrity=[WpCliCoreIntegrity(), WpCliPluginIntegrity()],
    )
    for artifact in result.artifacts:
        kinds[artifact.kind.value] += 1
    report = CanonicalReport(
        scan_id=result.scan_id,
        target_root=result.target_root,
        profile=profile,
        findings=result.findings,
        coverage=result.coverage,
        note="Orquestrador v1: inventory + detection + checksum (degrade gracioso).",
    )
    if format_ == "json":
        console.print_json(report.to_json())
    else:
        _print_terminal(report, kinds)
    order = ["info", "low", "medium", "high", "critical"]
    worst = max([order.index(f.severity.value) for f in result.findings], default=-1)
    raise typer.Exit(
        code=ExitCode.FINDINGS_OVER_THRESHOLD
        if worst >= order.index(threshold.value)
        else ExitCode.OK
    )


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


def main() -> None:
    app()
