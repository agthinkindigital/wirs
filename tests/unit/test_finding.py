"""Finding schema (WIRS-021, spec 3.4 e 4)."""

from __future__ import annotations

from wirs.domain import Confidence, ConfidenceClass, Finding, Severity


def test_finding_integridade_com_id_estavel() -> None:
    a = Finding(
        rule_id="WP.CORE.HASH_MISMATCH",
        title="Arquivo do core diverge do baseline confiável",
        category="integrity",
        severity=Severity.CRITICAL,
        confidence=Confidence(ConfidenceClass.DETERMINISTIC),
        artifact_ref="art_abc",
        evidence_refs=("ev_01",),
        attributes={"expected_hash": "aaa", "actual_hash": "bbb"},
    )
    b = Finding(
        rule_id="WP.CORE.HASH_MISMATCH",
        title="Arquivo do core diverge do baseline confiável",
        category="integrity",
        severity=Severity.CRITICAL,
        confidence=Confidence(ConfidenceClass.DETERMINISTIC),
        artifact_ref="art_abc",
        evidence_refs=("ev_01",),
        attributes={"expected_hash": "aaa", "actual_hash": "bbb"},
    )

    assert a.id == b.id  # estável para mesma afirmação
    assert a.id.startswith("fnd_")
    assert a.severity is Severity.CRITICAL
    assert a.confidence.class_ is ConfidenceClass.DETERMINISTIC


def _base(**over) -> Finding:
    args: dict = {
        "rule_id": "R",
        "title": "t",
        "category": "integrity",
        "severity": Severity.HIGH,
        "confidence": Confidence(ConfidenceClass.HIGH),
        "artifact_ref": "art_x",
        "evidence_refs": ("ev_1",),
    }
    args.update(over)
    return Finding(**args)


def test_sem_evidence_nem_provenance_nao_ha_finding() -> None:
    import pytest

    with pytest.raises(ValueError, match="evidence_refs ou provenance"):
        _base(evidence_refs=())


def test_provenance_explicita_dispensa_evidence_refs() -> None:
    from wirs.domain import Provenance

    f = _base(
        evidence_refs=(),
        provenance=Provenance(collector="wordfence-cli", version="5.0.0"),
    )
    assert f.provenance is not None and f.provenance.collector == "wordfence-cli"


def test_estados_invalidos_rejeitados() -> None:
    import pytest

    with pytest.raises(ValueError, match="0.0"):
        Confidence(ConfidenceClass.HIGH, score=1.5)
    with pytest.raises(ValueError, match="0.0"):
        Confidence(ConfidenceClass.HIGH, score=-0.1)
    with pytest.raises(ValueError):
        Severity("apocalíptico")  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        ConfidenceClass("certeza_absoluta")  # type: ignore[call-arg]


def test_round_trip_serializacao() -> None:
    original = _base(
        evidence_refs=("ev_2", "ev_1"),  # ordem não importa para o ID
        attributes={"k": [1, 2]},
    )
    assert original.id == _base(evidence_refs=("ev_1", "ev_2"), attributes={"k": [1, 2]}).id

    restaurado = Finding.from_dict(original.to_dict())
    assert restaurado == original
    assert restaurado.severity is Severity.HIGH
    assert restaurado.confidence == Confidence(ConfidenceClass.HIGH)
