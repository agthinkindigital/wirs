"""JSON canônico (WIRS-090, ADR-004)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from wirs import __version__
from wirs.application.orchestrator import ScanResult
from wirs.domain import (
    Artifact,
    ArtifactKind,
    Confidence,
    ConfidenceClass,
    CoverageEntry,
    CoverageState,
    Evidence,
    Finding,
    Provenance,
    ProviderRun,
    ProviderRunStatus,
    SafePath,
    Severity,
)
from wirs.reporting.canonical import CanonicalReport

FIXED_AT = datetime(2026, 9, 9, 12, 0, 0)


def _report() -> CanonicalReport:
    return CanonicalReport(
        scan_id="scan_01",
        target_root="/srv/www/site",
        profile="soft",
        artifacts=(
            Artifact(kind=ArtifactKind.FILE, path=SafePath(Path.cwd(), "x.php"), id="art_abc"),
        ),
        evidence=(
            Evidence(
                scan_id="scan_01",
                kind="test",
                source="test",
                artifact_ref="art_abc",
                content={},
                provenance=Provenance("test", "1"),
                collected_at=FIXED_AT,
                id="ev_01",
            ),
        ),
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

    assert data["schema_version"] == "2.0"
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
        artifacts=(
            Artifact(kind=ArtifactKind.FILE, path=SafePath(Path.cwd(), "b.php"), id="art_b"),
            Artifact(kind=ArtifactKind.FILE, path=SafePath(Path.cwd(), "a.php"), id="art_a"),
        ),
        evidence=(
            Evidence(
                scan_id="s",
                kind="test",
                source="test",
                artifact_ref="art_a",
                content={},
                provenance=Provenance("test", "1"),
                collected_at=FIXED_AT,
                id="ev_1",
            ),
        ),
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
        artifacts=(
            Artifact(kind=ArtifactKind.FILE, path=SafePath(Path.cwd(), "a.php"), id="art_a"),
            Artifact(kind=ArtifactKind.FILE, path=SafePath(Path.cwd(), "b.php"), id="art_b"),
        ),
        evidence=(
            Evidence(
                scan_id="s",
                kind="test",
                source="test",
                artifact_ref="art_a",
                content={},
                provenance=Provenance("test", "1"),
                collected_at=FIXED_AT,
                id="ev_1",
            ),
        ),
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


def test_from_scan_result_produz_report_20_com_manifest_e_registros(tmp_path) -> None:
    artifact = Artifact(
        kind=ArtifactKind.FILE,
        path=SafePath(tmp_path, "wp-content/plugins/foo.php"),
        source_ref="src_primary",
    )
    evidence = Evidence(
        scan_id="scan_transform",
        kind="content_match",
        source="wirs-internal",
        artifact_ref=artifact.id,
        content={"rule": "eval"},
        provenance=Provenance("wirs-internal", __version__),
    )
    finding = Finding(
        rule_id="PHP.EVAL",
        title="eval encontrado",
        category="content",
        severity=Severity.HIGH,
        confidence=Confidence(ConfidenceClass.HIGH),
        artifact_ref=artifact.id,
        evidence_refs=(evidence.id,),
    )
    result = ScanResult(
        scan_id="scan_transform",
        target_root=str(tmp_path),
        profile="soft",
        artifacts=(artifact,),
        gaps=0,
        discovery=None,
        zones={},
        coverage=(
            CoverageEntry(
                capability="filesystem",
                state=CoverageState.COMPLETE,
                applicable_checks=1,
                verified=1,
            ),
        ),
        findings=(finding,),
        evidence=(evidence,),
        provider_runs=(
            ProviderRun(
                provider_id="test-provider",
                status=ProviderRunStatus.COMPLETED,
                version="1.0",
                capabilities=("test",),
            ),
        ),
    )

    data = CanonicalReport.from_scan_result(result).to_dict()

    assert data["schema_version"] == "2.0"
    assert data["manifest"]["scan_id"] == "scan_transform"
    assert data["manifest"]["target"]["root"] == str(tmp_path)
    assert data["manifest"]["sources"] == [{"source_ref": "src_primary"}]
    artifact_data = artifact.to_dict()
    artifact_data.pop("root")
    assert data["artifacts"] == [artifact_data]
    assert data["evidence"] == [evidence.to_dict()]
    assert data["provider_runs"][0]["status"] == "completed"
    assert data["diagnoses"] == []


def test_referencia_quebrada_falha_antes_da_serializacao() -> None:
    finding = Finding(
        rule_id="TEST.BROKEN_REF",
        title="ref quebrada",
        category="test",
        severity=Severity.HIGH,
        confidence=Confidence(ConfidenceClass.HIGH),
        artifact_ref="art_missing",
        evidence_refs=("ev_missing",),
    )
    report = CanonicalReport(
        scan_id="s", target_root="/target", profile="soft", findings=(finding,)
    )

    with pytest.raises(ValueError, match="Finding referencia Artifact inexistente"):
        report.to_json()


def test_diagnosis_orfa_falha_antes_da_serializacao() -> None:
    from wirs.domain import Diagnosis

    report = CanonicalReport(
        scan_id="s",
        target_root="/target",
        profile="soft",
        diagnoses=(
            Diagnosis(
                rule_id="DX001",
                title="diagnosis",
                summary="summary",
                artifact_ref="art_missing",
                confidence=ConfidenceClass.HIGH,
                basis=("fnd_missing",),
                hypothesis="hypothesis",
            ),
        ),
    )

    with pytest.raises(ValueError, match="Diagnosis referencia Artifact inexistente"):
        report.to_json()


def test_serializacao_aplica_redaction_final_em_registros() -> None:
    artifact = Artifact(
        kind=ArtifactKind.FILE,
        path=SafePath(Path.cwd(), "token=segredo.php"),
        id="art_secret",
    )
    evidence = Evidence(
        scan_id="s",
        kind="test",
        source="test",
        artifact_ref=artifact.id,
        content={"password": "super-secret"},
        provenance=Provenance("test", "1"),
    )
    finding = Finding(
        rule_id="TEST.SECRET",
        title="secret",
        category="test",
        severity=Severity.LOW,
        confidence=Confidence(ConfidenceClass.LOW),
        artifact_ref=artifact.id,
        evidence_refs=(evidence.id,),
        attributes={"api_key": "abc123"},
    )
    report = CanonicalReport(
        scan_id="s",
        target_root="/target/token=target-secret",
        profile="soft",
        artifacts=(artifact,),
        evidence=(evidence,),
        findings=(finding,),
        provider_runs=(
            ProviderRun(
                provider_id="test",
                status=ProviderRunStatus.FAILED,
                reason="token=provider-secret",
            ),
        ),
    )

    output = report.to_json()

    assert "super-secret" not in output
    assert "abc123" not in output
    assert "provider-secret" not in output
    assert "target-secret" not in output
