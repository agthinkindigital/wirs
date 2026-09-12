"""Manifest comparator (WIRS-041)."""

from __future__ import annotations

from wirs.domain import BaselineManifest, BaselineTrust, IntegrityState, compare_baseline

_HASH_A = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
_HASH_B = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
_HASH_C = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def _manifest() -> BaselineManifest:
    return BaselineManifest(
        component_id="demo",
        version="1.0",
        source="operator",
        trust=BaselineTrust.TRUSTED_OPERATOR,
        files={"ok.php": _HASH_A, "mudou.php": _HASH_B},
    )


def test_compara_manifest_contra_arvore_real() -> None:
    resultado = {
        r.path: r
        for r in compare_baseline(
            _manifest(),
            {
                "ok.php": _HASH_A,
                "mudou.php": _HASH_C,
                "extra.php": _HASH_A,
            },
        )
    }

    assert resultado["ok.php"].state is IntegrityState.MATCH
    assert resultado["mudou.php"].state is IntegrityState.MISMATCH
    assert resultado["extra.php"].state is IntegrityState.UNEXPECTED


def test_ausente_e_par_expected_actual() -> None:
    resultado = {r.path: r for r in compare_baseline(_manifest(), {"ok.php": _HASH_A})}

    ausente = resultado["mudou.php"]
    assert ausente.state is IntegrityState.MISSING
    assert ausente.expected == _HASH_B
    assert ausente.actual is None

    divergente = next(
        r
        for r in compare_baseline(_manifest(), {"mudou.php": _HASH_C})
        if r.state is IntegrityState.MISMATCH
    )
    assert divergente.expected == _HASH_B
    assert divergente.actual == _HASH_C
