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
from collections.abc import Sequence
from enum import IntEnum
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from wirs import __version__
from wirs.adapters.wordpress.discovery import WordPressAdapter
from wirs.adapters.wordpress.policies import UploadsExecutablePolicy
from wirs.application.orchestrator import run_scan
from wirs.cli.progress import CliProgress, GuiProgress
from wirs.detectors.builtin import IocDetector, PhpHeuristicsDetector
from wirs.domain import IOC, IOCKind, LocalDirectoryTarget, Severity, TargetError
from wirs.infrastructure import ArtifactReader, LocalArtifactSource
from wirs.infrastructure.baseline import BaselineBuilder
from wirs.infrastructure.reader import ReadBudget
from wirs.ports.checksum import IntegrityProvider
from wirs.ports.detection import Detector
from wirs.providers.operator_baseline import OperatorBaselineIntegrity, load_baseline_mapping
from wirs.providers.wp_checksum import WpCliCoreIntegrity, WpCliPluginIntegrity
from wirs.reporting import CanonicalReport, render_report, write_text_atomic

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


baseline_app = typer.Typer(
    name="baseline",
    help="Baselines do operador: criar e inspecionar manifests (WIRS-042).",
    no_args_is_help=True,
)
app.add_typer(baseline_app, name="baseline")


@baseline_app.command("create")
def baseline_create(
    directory: Path = typer.Argument(..., help="Diretório limpo a fingerprintar."),
    name: str = typer.Option(..., "--name", help="ID do componente no manifest."),
    version: str = typer.Option("0.0.0", "--version", help="Versão do componente."),
    output: Path | None = typer.Option(None, "--output", help="Arquivo do manifest."),
) -> None:
    """Gera manifest SHA-256 de um diretório (só lê; symlink não entra)."""
    try:
        manifest = BaselineBuilder().build(directory, component_id=name, version=version)
    except (TargetError, ValueError) as e:
        console.print(f"[red]Baseline inválido:[/red] {e}")
        raise typer.Exit(code=ExitCode.INVALID_TARGET) from e
    dest = output or Path(f"{name}-baseline.json")
    try:
        import json

        dest.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8")
    except OSError as e:
        console.print(f"[red]Não consegui escrever:[/red] {dest} ({e})")
        raise typer.Exit(code=ExitCode.INTERNAL_ERROR) from e
    console.print(f"manifest: {dest} ({len(manifest.files)} arquivos)")


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


def build_detectors(ioc_list: Sequence[IOC]) -> list[Detector]:
    """Detectores do scan; IOC só entra com lista (evita 2ª leitura à toa)."""
    detectors: list[Detector] = [PhpHeuristicsDetector(), UploadsExecutablePolicy()]
    if ioc_list:
        detectors.insert(0, IocDetector(list(ioc_list)))
    return detectors


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
    baseline: Path | None = typer.Option(
        None, "--baseline", help="Mapping JSON dir->manifest (WIRS-066)."
    ),
    report_file: Path | None = typer.Option(
        None, "--report", help="Grava o JSON canônico neste arquivo (WIRS-119)."
    ),
    gui: bool = typer.Option(False, "--gui", help="Tela de acompanhamento (WIRS-139)."),
    cli: bool = typer.Option(False, "--cli", help="Guia visual em texto (padrão)."),
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
    if gui and cli:
        console.print("[red]Escolha um: --gui ou --cli[/red]")
        raise typer.Exit(code=ExitCode.INVALID_TARGET)
    monitor = GuiProgress() if gui else CliProgress()
    report_dest: Path | None = None
    if report_file is not None:
        candidate = Path(report_file).expanduser()
        if _dentro_do_target(candidate, tgt.root):
            console.print(
                f"[red]Report dentro do target (scan não escreve no alvo):[/red] {candidate}"
            )
            raise typer.Exit(code=ExitCode.INVALID_TARGET)
        report_dest = candidate
    integrity_providers: list[IntegrityProvider] = [WpCliCoreIntegrity(), WpCliPluginIntegrity()]
    if baseline is not None:
        try:
            mapping = load_baseline_mapping(baseline)
        except ValueError as e:
            console.print(f"[red]Baseline inválido:[/red] {e}")
            raise typer.Exit(code=ExitCode.INVALID_TARGET) from e
        integrity_providers.append(OperatorBaselineIntegrity(mapping))
    result = run_scan(
        tgt,
        profile=profile,
        source=LocalArtifactSource(),
        adapters=[WordPressAdapter()],
        reader=ArtifactReader(),
        budget=ReadBudget(max_bytes=PROFILE_BUDGETS[profile]),
        detectors=build_detectors(ioc_list),
        integrity=integrity_providers,
        on_event=monitor,
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
    payload = report.to_json()  # uma serialização: stdout e arquivo idênticos
    if format_ == "json":
        console.print_json(payload)
    else:
        _print_terminal(report, kinds)
    if report_dest is not None:
        try:
            write_text_atomic(report_dest, payload)
        except OSError as e:
            console.print(f"[red]Não consegui gravar o report:[/red] {e}")
            raise typer.Exit(code=ExitCode.INTERNAL_ERROR) from e
        if format_ != "json":
            console.print(f"report: {report_dest}")
    order = ["info", "low", "medium", "high", "critical"]
    worst = max([order.index(f.severity.value) for f in result.findings], default=-1)
    raise typer.Exit(
        code=ExitCode.FINDINGS_OVER_THRESHOLD
        if worst >= order.index(threshold.value)
        else ExitCode.OK
    )


def _dentro_do_target(candidate: Path, root: Path) -> bool:
    """Report nunca mora no alvo (invariante 1: scan não escreve no target)."""
    try:
        resolved = candidate.resolve()
    except OSError:
        return False
    return resolved == root or root in resolved.parents


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
