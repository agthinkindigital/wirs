"""Terminal reporter: view operacional do CanonicalReport (WIRS-091).

Regras: severidade e confiança sempre em texto (cor nunca sozinha), coverage
tão visível quanto findings, e todo conteúdo do alvo passa por `sanitize`
(ANSI neutralizado, markup do Rich escapado, controles visíveis).
"""

from __future__ import annotations

import re
from collections import Counter

from rich.console import Console
from rich.markup import escape
from rich.table import Table

from wirs.domain import Severity
from wirs.reporting.canonical import CanonicalReport

_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_CONTROLS = re.compile(r"[\x00-\x1f\x7f]")

_SEVERITY_STYLE = {
    Severity.CRITICAL: "bold red",
    Severity.HIGH: "red",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "blue",
    Severity.INFO: "dim",
}


def sanitize(text: str) -> str:
    """Neutraliza ANSI, escapa markup Rich e torna controles visíveis."""
    return escape(_CONTROLS.sub("?", _ANSI.sub("", text)))


def render_report(report: CanonicalReport, console: Console | None = None) -> None:
    console = console or Console()
    counts: Counter[str] = Counter()
    for finding in report.findings:
        counts[finding.severity.value] += 1

    summary = Table(title="Summary")
    summary.add_column("Severity")
    summary.add_column("Count", justify="right")
    for severity in Severity:
        summary.add_row(
            f"[{_SEVERITY_STYLE[severity]}]{severity.name}[/]",
            str(counts.get(severity.value, 0)),
        )
    console.print(summary)

    for finding in report.findings:
        card = Table(
            title=f"[{_SEVERITY_STYLE[finding.severity]}]"
            f"{finding.severity.name}[/] {sanitize(finding.rule_id)}",
            show_header=False,
        )
        card.add_column("Campo")
        card.add_column("Valor")
        card.add_row("Title", sanitize(finding.title))
        card.add_row("Category", sanitize(finding.category))
        card.add_row("Confidence", finding.confidence.class_.value.upper())
        card.add_row("Artifact", sanitize(finding.artifact_ref))
        card.add_row("Evidence", ", ".join(sanitize(r) for r in finding.evidence_refs))
        for key in sorted(finding.attributes):
            card.add_row(sanitize(f"attr:{key}"), sanitize(str(finding.attributes[key])))
        console.print(card)

    coverage = Table(title="Coverage")
    coverage.add_column("Capability")
    coverage.add_column("State")
    coverage.add_column("Verified", justify="right")
    coverage.add_column("Failed", justify="right")
    for entry in report.coverage:
        coverage.add_row(
            sanitize(entry.capability), entry.state.value, str(entry.verified), str(entry.failed)
        )
    console.print(coverage)
