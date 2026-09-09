"""JSON canônico (WIRS-090, ADR-004)."""

from __future__ import annotations

from datetime import datetime

from wirs import __version__
from wirs.domain import (
    Confidence,
    ConfidenceClass,
    CoverageEntry,
    CoverageState,
    Finding,
    Severity,
)
from wirs.reporting.canonical import CanonicalReport

FIXED_AT = datetime(2026, 9, 9, 12, 0, 0)


def _report() -> CanonicalReport:
    return CanonicalReport(
        scan_id="scan_01",
        target_root="/srv/www/site",
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
        generated_at=FIXED_AT,
    )


def _finding() -> Finding:
    return Finding(
        rule_id="WP.CORE.HASH_MISMATCH",
        title="t",
        category="integrity",
        severity=Severity.CRITICAL,
        confidence=Confidence(ConfidenceClass.DETERMINISTIC),
        artifact_ref="art_abc",
        evidence_refs=("ev_01",),
    )


def test_schema_e_scanner_separados_e_ordem_estavel() -> None:
    report = _report()
    data = report.to_dict()

    assert data["schema_version"] == "1.0"
    assert data["scanner_version"] == __version__
    assert data["schema_version"] != data["scanner_version"]
    assert report.to_json() == _report().to_json()  # duas construções → string idêntica


def _finding_com_id(rule: str, ref: str) -> Finding:
    return Finding(
        rule_id=rule,
        title="t",
        category="integrity",
        severity=Severity.HIGH,
        confidence=Confidence(ConfidenceClass.HIGH),
        artifact_ref=ref,
        evidence_refs=("ev_1",),
    )


def test_ordem_de_entrada_nao_muda_saida() -> None:
    fora_de_ordem = CanonicalReport(
        scan_id="s",
        target_root="/t",
        profile="soft",
        findings=(_finding_com_id("Z.RULE", "art_b"), _finding_com_id("A.RULE", "art_a")),
        coverage=(
            CoverageEntry(
                capability="yara",
                state=CoverageState.PARTIAL,
                applicable_checks=4,
                verified=3,
                unavailable=1,
            ),
            CoverageEntry(
                capability="filesystem",
                state=CoverageState.COMPLETE,
                applicable_checks=2,
                verified=2,
            ),
        ),
        generated_at=FIXED_AT,
    )
    em_ordem = CanonicalReport(
        scan_id="s",
        target_root="/t",
        profile="soft",
        findings=(_finding_com_id("A.RULE", "art_a"), _finding_com_id("Z.RULE", "art_b")),
        coverage=(
            CoverageEntry(
                capability="filesystem",
                state=CoverageState.COMPLETE,
                applicable_checks=2,
                verified=2,
            ),
            CoverageEntry(
                capability="yara",
                state=CoverageState.PARTIAL,
                applicable_checks=4,
                verified=3,
                unavailable=1,
            ),
        ),
        generated_at=FIXED_AT,
    )
    assert fora_de_ordem.to_json() == em_ordem.to_json()
    data = fora_de_ordem.to_dict()
    ids = [f["id"] for f in data["findings"]]
    assert ids == sorted(ids)  # ordenado por ID estável, não por ordem de chegada
    assert [c["capability"] for c in data["coverage"]] == ["filesystem", "yara"]


def test_sem_conteudo_bruto_e_round_trip() -> None:
    import json

    report = _report()
    raw = report.to_json()
    for proibida in ('"raw"', '"file_content"', '"content_raw"'):
        assert proibida not in raw  # modelos nunca carregam conteúdo bruto

    restaurado = CanonicalReport.from_dict(json.loads(raw))
    assert restaurado.scan_id == report.scan_id
    assert restaurado.to_json() == raw
