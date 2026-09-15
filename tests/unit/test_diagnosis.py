"""Diagnosis file-centric: correlação auditável sem raciocínio circular."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from wirs.domain import (
    Artifact,
    ArtifactKind,
    Confidence,
    ConfidenceClass,
    Diagnosis,
    Evidence,
    Finding,
    Provenance,
    SafePath,
    Severity,
)
from wirs.domain.diagnosis import correlate_diagnoses


def _artifact() -> Artifact:
    return Artifact(
        kind=ArtifactKind.FILE,
        path=SafePath(Path.cwd(), "wp-includes/bad.php"),
        id="art_bad",
    )


def _finding(rule_id: str, *, evidence_refs: tuple[str, ...] = ()) -> Finding:
    return Finding(
        rule_id=rule_id,
        title=rule_id,
        category="signature" if rule_id.startswith("YARA.") else "integrity",
        severity=Severity.HIGH,
        confidence=Confidence(
            ConfidenceClass.HIGH if rule_id.startswith("YARA.") else ConfidenceClass.DETERMINISTIC
        ),
        artifact_ref="art_bad",
        evidence_refs=evidence_refs,
        provenance=None if evidence_refs else Provenance("baseline", "1"),
    )


def test_dx001_correlaciona_mismatch_contra_assinatura_no_mesmo_artifact() -> None:
    evidence = Evidence(
        scan_id="scan_1",
        kind="external_match",
        source="yara",
        artifact_ref="art_bad",
        content={"rule": "MALWARE"},
        provenance=Provenance("yara", "1"),
        id="ev_yara",
    )
    mismatch = _finding("WP.CORE.HASH_MISMATCH")
    signature = _finding("YARA.MALWARE", evidence_refs=(evidence.id,))

    diagnoses = correlate_diagnoses(
        artifacts=(_artifact(),), findings=(mismatch, signature), evidence=(evidence,)
    )

    assert len(diagnoses) == 1
    diagnosis = diagnoses[0]
    assert diagnosis.rule_id == "DX001"
    assert diagnosis.artifact_ref == "art_bad"
    assert diagnosis.confidence is ConfidenceClass.HIGH
    assert diagnosis.basis == (mismatch.id, signature.id)
    assert diagnosis.evidence_refs == (evidence.id,)
    assert diagnosis.hypothesis != diagnosis.basis
    assert diagnosis.alternative_hypotheses
    assert diagnosis.unknowns
    assert diagnosis.recommended_next_checks


def test_nao_correlaciona_sinais_de_artifacts_diferentes() -> None:
    first = _artifact()
    second = Artifact(
        kind=ArtifactKind.FILE,
        path=SafePath(Path.cwd(), "wp-includes/other.php"),
        id="art_other",
    )
    mismatch = _finding("WP.CORE.HASH_MISMATCH")
    signature = replace(
        _finding("YARA.MALWARE", evidence_refs=("ev_yara",)), artifact_ref=second.id, id=""
    )

    assert (
        correlate_diagnoses(artifacts=(first, second), findings=(mismatch, signature), evidence=())
        == ()
    )


def test_diagnosis_tem_id_estavel_e_round_trip() -> None:
    diagnosis = Diagnosis(
        rule_id="DX001",
        title="Adulteração possível",
        summary="Dois sinais convergem no mesmo arquivo.",
        artifact_ref="art_bad",
        confidence=ConfidenceClass.HIGH,
        basis=("fnd_a", "fnd_b"),
        evidence_refs=("ev_a",),
        hypothesis="O arquivo confiável pode ter sido adulterado.",
        alternative_hypotheses=("Baseline pode estar desatualizado.",),
        unknowns=("A origem da alteração não é conhecida.",),
        recommended_next_checks=("Revisar o arquivo e o deploy.",),
    )

    restored = Diagnosis.from_dict(diagnosis.to_dict())

    assert restored == diagnosis
    assert restored.diagnosis_id.startswith("dx_")
