"""Terminal reporter (WIRS-091): summary, finding cards, coverage, sem cor-só."""

from __future__ import annotations

from rich.console import Console

from wirs.domain import (
    Confidence,
    ConfidenceClass,
    CoverageEntry,
    CoverageState,
    Finding,
    Severity,
)
from wirs.reporting.terminal import render_report


def _report():
    from wirs.reporting.canonical import CanonicalReport

    return CanonicalReport(
        scan_id="s",
        target_root="/t",
        profile="soft",
        findings=(
            Finding(
                rule_id="WP.CORE.HASH_MISMATCH",
                title="t",
                category="integrity",
                severity=Severity.CRITICAL,
                confidence=Confidence(ConfidenceClass.DETERMINISTIC),
                artifact_ref="art_1",
                evidence_refs=("ev_1", "ev_2"),
            ),
        ),
        coverage=(
            CoverageEntry(
                capability="filesystem",
                state=CoverageState.COMPLETE,
                applicable_checks=10,
                verified=10,
            ),
        ),
    )


def test_summary_e_coverage_visiveis() -> None:
    console = Console(record=True, width=100)
    render_report(_report(), console=console)
    text = console.export_text()

    for nivel in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        assert nivel in text  # todos os níveis, mesmo zerados
    assert "filesystem" in text and "complete" in text
    assert "1" in text  # contagem do critical


def test_conteudo_hostil_neutralizado() -> None:
    from wirs.reporting.canonical import CanonicalReport

    hostil = Finding(
        rule_id="X",
        title="\x1b[2Jlimpo [bold]não-negrito[/bold] <script>\nlinha2",
        category="integrity",
        severity=Severity.HIGH,
        confidence=Confidence(ConfidenceClass.HIGH),
        artifact_ref="art_\x1b[31mx",
        evidence_refs=("ev_1",),
    )
    console = Console(record=True, width=120)
    render_report(
        CanonicalReport(
            scan_id="s", target_root="/t", profile="soft", findings=(hostil,), coverage=()
        ),
        console=console,
    )
    text = console.export_text()

    assert "\x1b" not in text  # nenhum escape ANSI sobrevive
    assert "[bold]" in text  # markup aparece como texto, não formata
    assert "?" in text  # newline virou caractere visível
    assert "HIGH" in text and "high" in text.lower()  # severidade em texto


def test_card_mostra_arquivo_nao_so_id() -> None:
    from wirs.reporting.canonical import CanonicalReport

    com_path = Finding(
        rule_id="WP.UPLOAD.EXECUTABLE",
        title="t",
        category="policy",
        severity=Severity.HIGH,
        confidence=Confidence(ConfidenceClass.HIGH),
        artifact_ref="art_abc",
        evidence_refs=("ev_1",),
        attributes={"path": "wp-content/uploads/evil.php", "zone": "wp-content-uploads"},
    )
    console = Console(record=True, width=120)
    render_report(
        CanonicalReport(
            scan_id="s", target_root="/t", profile="soft", findings=(com_path,), coverage=()
        ),
        console=console,
    )
    text = console.export_text()

    assert "wp-content/uploads/evil.php" in text
    assert "art_abc" not in text  # ID interno não vaza quando há path
