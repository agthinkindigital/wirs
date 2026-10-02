"""Relações entre findings — WIRS-105 (#76, DAG relations).

TDD: testes primeiro, depois `src/wirs/domain/relation.py`.
Vocabulário em CONTEXT.md (Actor: compartilhar IP/CIDR/UA é pista, não prova).
"""

from __future__ import annotations

from wirs.domain import Confidence, ConfidenceClass, Finding, Severity
from wirs.domain.relation import FindingRelation, RelationKind, correlate_relations


def _finding(id: str, artifact: str = "art_1", **attrs) -> Finding:
    return Finding(
        rule_id="PHP.HEUR.COMBO",
        title="t",
        category="heuristic",
        severity=Severity.MEDIUM,
        confidence=Confidence(ConfidenceClass.MEDIUM),
        artifact_ref=artifact,
        evidence_refs=("ev_1",),
        attributes=dict(attrs),
        id=id,
    )


def test_mesmo_artifact_vira_relacao_strong() -> None:
    a = _finding("fnd_a", artifact="art_1")
    b = _finding("fnd_b", artifact="art_1")

    (rel,) = correlate_relations([a, b])

    assert rel.rule_id == "REL.SAME_ARTIFACT"
    assert rel.kind is RelationKind.STRONG
    assert set(rel.finding_refs) == {"fnd_a", "fnd_b"}
    assert rel.key == "artifact:art_1"
    assert rel.window == "exact"
    assert rel.id.startswith("rel_")


def test_mesmo_component_e_mesmo_ioc() -> None:
    a = _finding("fnd_a", artifact="art_1", component="akismet")
    b = _finding("fnd_b", artifact="art_2", component="akismet")
    c = _finding("fnd_c", artifact="art_3", ioc_id="ioc_x")
    d = _finding("fnd_d", artifact="art_4", ioc_id="ioc_x")

    rels = {rel.rule_id: rel for rel in correlate_relations([a, b, c, d])}

    assert set(rels) >= {"REL.SAME_COMPONENT", "REL.SAME_IOC"}
    assert rels["REL.SAME_COMPONENT"].key == "component:akismet"
    assert rels["REL.SAME_IOC"].finding_refs == ("fnd_c", "fnd_d")
    assert all(rel.kind is RelationKind.STRONG for rel in rels.values())


def test_mesmo_ip_exato_e_mesma_janela_temporal() -> None:
    dia_a = "2026-09-30T10:00:00+00:00"
    dia_b = "2026-09-30T22:00:00+00:00"
    a = _finding("fnd_a", artifact="art_1", ip="203.0.113.7", occurred_at=dia_a)
    b = _finding("fnd_b", artifact="art_2", ip="203.0.113.7", occurred_at=dia_b)
    c = _finding("fnd_c", artifact="art_3", occurred_at="2026-10-01T10:00:00+00:00")

    rels = {rel.rule_id: rel for rel in correlate_relations([a, b, c])}

    net = rels["REL.SAME_NETWORK"]
    assert net.key == "ip:203.0.113.7"
    assert net.attribution is False  # IP compartilhado nunca vira ator
    window = rels["REL.SAME_WINDOW"]
    assert window.key == "day:2026-09-30"
    assert window.window == "24h"
    assert set(window.finding_refs) == {"fnd_a", "fnd_b"}


def test_cidr_e_ua_sao_cue_sem_atribuicao() -> None:
    a = _finding("fnd_a", artifact="art_1", ip="198.51.100.10", ua_family="curl")
    b = _finding("fnd_b", artifact="art_2", ip="198.51.100.99", ua_family="curl")

    rels = {rel.rule_id: rel for rel in correlate_relations([a, b])}

    assert set(rels) == {"REL.SAME_CIDR", "REL.SAME_UA_FAMILY"}
    for rel in rels.values():
        assert rel.kind is RelationKind.CUE
        assert rel.attribution is False
    assert rels["REL.SAME_CIDR"].key == "cidr:198.51.100.0/24"
    assert "same_actor" not in " ".join(r.rule_id for r in rels.values())


def test_nat_mesmo_ip_contas_distintas_nao_vira_ator() -> None:
    a = _finding("fnd_a", artifact="art_1", ip="192.0.2.5", owner="conta-alheia")
    b = _finding("fnd_b", artifact="art_2", ip="192.0.2.5", owner="conta-minha")

    rels = correlate_relations([a, b])

    redes = [rel for rel in rels if "CIDR" in rel.rule_id or "NETWORK" in rel.rule_id]
    assert redes and all(rel.attribution is False for rel in redes)
    assert not any("ACTOR" in rel.rule_id for rel in rels)


def test_admin_legitimo_nao_elevam_confianca() -> None:
    a = _finding("fnd_a", artifact="art_1", owner="admin")
    b = _finding("fnd_b", artifact="art_2", owner="admin")

    (rel,) = [r for r in correlate_relations([a, b]) if r.rule_id == "REL.SAME_OWNER"]

    assert rel.kind is RelationKind.STRONG
    assert a.confidence == Confidence(ConfidenceClass.MEDIUM)
    assert b.confidence == Confidence(ConfidenceClass.MEDIUM)


def test_sem_dados_sem_relacao_e_roundtrip() -> None:
    assert correlate_relations([]) == ()
    assert correlate_relations([_finding("fnd_a")]) == ()

    rel = FindingRelation(
        rule_id="REL.SAME_ARTIFACT",
        kind=RelationKind.STRONG,
        finding_refs=("fnd_b", "fnd_a"),
        key="artifact:art_1",
        window="exact",
        justification="j",
    )
    clone = FindingRelation.from_dict(rel.to_dict())
    assert clone == rel
    assert clone.finding_refs == ("fnd_a", "fnd_b")  # ordem estável p/ id estável
