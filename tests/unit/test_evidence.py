"""Evidence schema (WIRS-020, spec 3.3)."""

from __future__ import annotations

from wirs.domain import Evidence, Provenance, RedactionState


def test_file_hash_evidence_com_id_estavel() -> None:
    prov = Provenance(collector="internal.hash", version="0.1.0")
    a = Evidence(
        scan_id="scan_01",
        kind="file_hash",
        source="filesystem",
        artifact_ref="art_abc",
        content={"algorithm": "sha256", "hash": "deadbeef"},
        provenance=prov,
    )
    b = Evidence(
        scan_id="scan_01",
        kind="file_hash",
        source="filesystem",
        artifact_ref="art_abc",
        content={"algorithm": "sha256", "hash": "deadbeef"},
        provenance=prov,
    )

    assert a.id == b.id  # estável para mesma observação
    assert a.id.startswith("ev_")
    assert a.redaction_state.value == "none"


def _base(**over) -> Evidence:
    args: dict = {
        "scan_id": "scan_01",
        "kind": "file_hash",
        "source": "filesystem",
        "artifact_ref": "art_abc",
        "content": {"algorithm": "sha256", "hash": "deadbeef"},
        "provenance": Provenance(collector="internal.hash", version="0.1.0"),
    }
    args.update(over)
    return Evidence(**args)


def test_provenance_obrigatoria() -> None:
    import pytest

    with pytest.raises(TypeError):
        Evidence(
            scan_id="scan_01",
            kind="file_hash",
            source="filesystem",
            artifact_ref="art_abc",
            content={},
        )  # type: ignore[call-arg] — provenance não tem default de propósito


def test_redaction_explicito_e_unicidade() -> None:
    base = _base()
    assert base.redaction_state is RedactionState.NONE

    redigida = _base(redaction_state=RedactionState.REDACTED)
    assert redigida.redaction_state is RedactionState.REDACTED

    assert _base(content={"hash": "outro"}).id != base.id  # conteúdo difere → outro ID
    assert _base(kind="file_metadata").id != base.id  # kind difere → outro ID
    assert _base(artifact_ref="art_outro").id != base.id


def test_content_nao_serializavel_rejeitado() -> None:
    import pytest

    with pytest.raises(ValueError, match="JSON-serializável"):
        _base(content={"bin": b"\x00\x01"})  # type: ignore[dict-item]


def test_round_trip_serializacao() -> None:
    original = _base(redaction_state=RedactionState.REDACTED)
    restaurada = Evidence.from_dict(original.to_dict())

    assert restaurada == original
    assert restaurada.id == original.id
    assert restaurada.provenance == original.provenance
