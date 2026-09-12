"""Markdown reporter (WIRS-093)."""

from __future__ import annotations

from wirs.domain import (
    Confidence,
    ConfidenceClass,
    CoverageEntry,
    CoverageState,
    Finding,
    Severity,
)
from wirs.reporting.markdown import render_markdown


def _finding() -> Finding:
    return Finding(
        rule_id="WP.UPLOAD.EXECUTABLE",
        title="t",
        category="policy",
        severity=Severity.HIGH,
        confidence=Confidence(ConfidenceClass.HIGH),
        artifact_ref="art_1",
        evidence_refs=("ev_1",),
        attributes={"path": "wp-content/uploads/evil.php"},
    )


def _report():
    from wirs.reporting.canonical import CanonicalReport

    return CanonicalReport(
        scan_id="s",
        target_root="/t",
        profile="soft",
        findings=(_finding(),),
        coverage=(
            CoverageEntry(
                capability="filesystem",
                state=CoverageState.COMPLETE,
                applicable_checks=10,
                verified=10,
            ),
        ),
    )


def test_markdown_com_findings_e_coverage() -> None:
    texto = render_markdown(_report())

    assert "WP.UPLOAD.EXECUTABLE" in texto
    assert "wp-content/uploads/evil.php" in texto
    assert "filesystem" in texto
    assert "HIGH" in texto


def test_hostil_nao_ativa_sintaxe() -> None:
    from wirs.reporting.canonical import CanonicalReport

    hostil = _finding()
    object.__setattr__(
        hostil,
        "attributes",
        {"path": "[clique](http://evil.example/x)", "zone": "<script>`code`</script>"},
    )
    texto = render_markdown(
        CanonicalReport(
            scan_id="s", target_root="/t", profile="soft", findings=(hostil,), coverage=()
        )
    )

    assert "[clique](http://evil.example/x)" not in texto
    assert "<script>" not in texto and "`code`" not in texto
    assert "evil.example" in texto  # conteúdo visível, sintaxe morta
