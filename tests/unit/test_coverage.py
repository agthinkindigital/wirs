"""Coverage model (WIRS-023, ADR-010)."""

from __future__ import annotations

from wirs.domain import CoverageEntry, CoverageState


def test_entry_complete_valida() -> None:
    entry = CoverageEntry(
        capability="filesystem",
        state=CoverageState.COMPLETE,
        applicable_checks=100,
        verified=100,
    )

    assert entry.state is CoverageState.COMPLETE
    assert entry.verified == 100
    assert [s.value for s in CoverageState] == [
        "complete",
        "partial",
        "skipped",
        "unavailable",
        "failed",
        "not_applicable",
    ]


def _entry(**over) -> CoverageEntry:
    args: dict = {
        "capability": "x",
        "state": CoverageState.PARTIAL,
        "applicable_checks": 10,
        "verified": 7,
        "failed": 3,
    }
    args.update(over)
    return CoverageEntry(**args)


def test_soma_dos_baldes_iguala_aplicaveis() -> None:
    import pytest

    with pytest.raises(ValueError, match="aplicáveis|aplicaveis|igualar"):
        _entry(verified=5, failed=3)  # soma 8 != 10
    with pytest.raises(ValueError):
        _entry(verified=-1, failed=11)


def test_provider_ausente_nunca_vira_complete() -> None:
    import pytest

    # YARA indisponível: o correto é UNAVAILABLE ou PARTIAL, nunca COMPLETE.
    with pytest.raises(ValueError, match="COMPLETE"):
        CoverageEntry(
            capability="yara",
            state=CoverageState.COMPLETE,
            applicable_checks=50,
            verified=40,
            unavailable=10,
        )
    parcial = CoverageEntry(
        capability="yara",
        state=CoverageState.PARTIAL,
        applicable_checks=50,
        verified=40,
        unavailable=10,
    )
    assert parcial.unavailable == 10


def test_estados_coerentes() -> None:
    import pytest

    with pytest.raises(ValueError, match="PARTIAL"):
        _entry(verified=10, failed=0)  # tudo verificado não é PARTIAL
    with pytest.raises(ValueError, match="UNAVAILABLE"):
        CoverageEntry(
            capability="db", state=CoverageState.UNAVAILABLE, applicable_checks=5, verified=5
        )
    with pytest.raises(ValueError, match="SKIPPED"):
        CoverageEntry(capability="db", state=CoverageState.SKIPPED, applicable_checks=5, verified=5)
    skip = CoverageEntry(
        capability="runtime", state=CoverageState.SKIPPED, applicable_checks=4, skipped=4
    )
    assert skip.skipped == 4
    na = CoverageEntry(capability="laravel", state=CoverageState.NOT_APPLICABLE)
    assert na.applicable_checks == 0


def test_round_trip_serializacao() -> None:
    original = _entry(note="YARA sem regras wordpress")
    restaurada = CoverageEntry.from_dict(original.to_dict())

    assert restaurada == original
    assert restaurada.state is CoverageState.PARTIAL
