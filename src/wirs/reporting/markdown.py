"""Markdown reporter: view para tickets e documentação (WIRS-093). Só stdlib.

Segurança: além do `sanitize` (ANSI/controles), escapa a sintaxe Markdown em
todo conteúdo do alvo (link injection `[x](http...)`, títulos, ênfase).
"""

from __future__ import annotations

from collections import Counter

from wirs.domain import Severity
from wirs.reporting.canonical import CanonicalReport
from wirs.reporting.terminal import sanitize

_MD_ESPECIAIS = ("\\", "`", "*", "_", "{", "}", "[", "]", "(", ")", "#", "!", "|", "<", ">")


def md_safe(text: str) -> str:
    """Conteúdo do alvo como texto inerte (sem sintaxe ativa)."""
    limpo = sanitize(text)
    for ch in _MD_ESPECIAIS:
        limpo = limpo.replace(ch, f"\\{ch}")
    return limpo


def render_markdown(report: CanonicalReport) -> str:
    """Documento Markdown do report canônico."""
    linhas = [
        f"# WIRS scan `{md_safe(report.target_root)}`",
        "",
        f"Profile: {md_safe(report.profile)} · findings: {len(report.findings)}",
        "",
        "## Summary",
        "",
        "| Severity | Count |",
        "|---|---|",
    ]
    counts: Counter[str] = Counter()
    for finding in report.findings:
        counts[finding.severity.value] += 1
    for severity in Severity:
        linhas.append(f"| {severity.name} | {counts.get(severity.value, 0)} |")

    for finding in report.findings:
        linhas += [
            "",
            f"## \\[{finding.severity.name}] {md_safe(finding.rule_id)}",
            "",
            f"Title: {md_safe(finding.title)}",
            "",
            f"Category: {md_safe(finding.category)}",
            "",
            f"Confidence: {finding.confidence.class_.value.upper()}",
            "",
        ]
        caminho = finding.attributes.get("path")
        if isinstance(caminho, str) and caminho:
            linhas += [f"File: `{md_safe(caminho)}`", ""]
        else:
            linhas += [f"Artifact: `{md_safe(finding.artifact_ref)}`", ""]
        for key in sorted(finding.attributes):
            if key == "path":
                continue
            linhas += [f"{md_safe(key)}: {md_safe(str(finding.attributes[key]))}", ""]

    linhas += ["## Coverage", "", "| Capability | State | Verified | Failed |", "|---|---|---|---|"]
    for entry in report.coverage:
        linhas.append(
            f"| {md_safe(entry.capability)} | {entry.state.value} "
            f"| {entry.verified} | {entry.failed} |"
        )
    return "\n".join(linhas) + "\n"
