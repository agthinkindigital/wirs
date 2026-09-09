"""Golden test do JSON canônico (WIRS-090).

O fixture `canonical_report_v1.json` foi revisado manualmente. Qualquer mudança
no output exige revisão explícita do diff e atualização consciente do golden —
nunca `--overwrite` cego.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from wirs.domain import (
    Confidence,
    ConfidenceClass,
    CoverageEntry,
    CoverageState,
    Finding,
    Severity,
)
from wirs.reporting.canonical import CanonicalReport

GOLDEN = Path(__file__).parent / "canonical_report_v1.json"


def build_golden_report() -> CanonicalReport:
    return CanonicalReport(
        scan_id="scan_golden_01",
        target_root="/srv/www/site",
        profile="soft",
        findings=(
            Finding(
                rule_id="WP.UPLOAD.EXECUTABLE",
                title="Conteúdo executável em zona de uploads",
                category="policy",
                severity=Severity.HIGH,
                confidence=Confidence(ConfidenceClass.HIGH),
                artifact_ref="art_uploads",
                evidence_refs=("ev_uploads",),
            ),
            Finding(
                rule_id="WP.CORE.HASH_MISMATCH",
                title="Arquivo do core diverge do baseline confiável",
                category="integrity",
                severity=Severity.CRITICAL,
                confidence=Confidence(ConfidenceClass.DETERMINISTIC),
                artifact_ref="art_core",
                evidence_refs=("ev_core",),
                attributes={"expected_hash": "aaa", "actual_hash": "bbb"},
            ),
        ),
        coverage=(
            CoverageEntry(
                capability="plugin_baseline",
                state=CoverageState.PARTIAL,
                applicable_checks=14,
                verified=12,
                unavailable=2,
                note="2 plugins premium sem baseline",
            ),
            CoverageEntry(
                capability="core_baseline",
                state=CoverageState.COMPLETE,
                applicable_checks=1600,
                verified=1600,
            ),
        ),
        generated_at=datetime(2026, 9, 9, 12, 0, 0),
        note="golden v1",
    )


def test_golden_byte_a_byte() -> None:
    assert build_golden_report().to_json() + "\n" == GOLDEN.read_text(encoding="utf-8")
