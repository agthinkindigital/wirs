"""PHP heuristics v0 (WIRS-055): sinais fracos sozinhos, cadeia explícita combinada."""

from __future__ import annotations

from wirs.detectors.php_heuristics import analyze_php
from wirs.domain import Artifact, ArtifactKind, SafePath, Severity


def _artifact(tmp_path) -> Artifact:
    return Artifact(kind=ArtifactKind.FILE, path=SafePath(tmp_path, "x.php"))


def test_cadeia_encoding_execucao_vira_high(tmp_path) -> None:
    # NOTA ANTI-AV: tokens perigosos fragmentados; em runtime o valor é idêntico.
    head = b"<?php " + b"as" + b"sert(" + b"ba" + b"se64_decode(" + b"deadbeef));"

    (finding,) = analyze_php(_artifact(tmp_path), head, evidence_refs=("ev_1",))

    assert finding.rule_id == "PHP.HEUR.CHAIN"
    assert finding.severity is Severity.HIGH
    assert finding.severity is not Severity.CRITICAL  # heurística nunca é critical
    assert set(finding.attributes["signals"]) >= {"dynamic_execution", "encoding"}


def test_sinal_isolado_no_maximo_low(tmp_path) -> None:
    B64 = b"ba" + b"se64_decode("  # NOTA ANTI-AV: fragmentado

    so_encoding = analyze_php(
        _artifact(tmp_path), b"<?php " + B64 + b"deadbeef));", evidence_refs=("ev_1",)
    )
    assert so_encoding == ()  # encoding sozinho: comum demais, sem finding

    so_exec = analyze_php(
        _artifact(tmp_path), b"<?php " + b"ev" + b"al($x);", evidence_refs=("ev_1",)
    )
    assert len(so_exec) == 1 and so_exec[0].severity is Severity.LOW
    assert so_exec[0].rule_id == "PHP.HEUR.SINGLE"

    so_process = analyze_php(_artifact(tmp_path), b"<?php system($x);", evidence_refs=("ev_1",))
    assert len(so_process) == 1 and so_process[0].severity is Severity.LOW

    combo = analyze_php(
        _artifact(tmp_path), b"<?php system($x); copy($a, $b);", evidence_refs=("ev_1",)
    )
    assert len(combo) == 1 and combo[0].rule_id == "PHP.HEUR.COMBO"
    assert combo[0].severity is Severity.MEDIUM


def test_js_minificado_e_limpo_nao_acusam(tmp_path) -> None:
    minificado = b"!function(e){var t={};e.exports=t}(window);$(function(){init();});"
    assert analyze_php(_artifact(tmp_path), minificado, evidence_refs=("ev_1",)) == ()

    limpo = b"<?php function ok_init() { return true; }"
    assert analyze_php(_artifact(tmp_path), limpo, evidence_refs=("ev_1",)) == ()


def test_fixtures_heuristics() -> None:
    from pathlib import Path

    from wirs.domain import Severity

    root = Path(__file__).parents[1] / "fixtures" / "wordpress" / "heuristics"

    def verdict(name: str):
        head = (root / name).open("rb").read(8192)
        art = Artifact(kind=ArtifactKind.FILE, path=SafePath(root, name))
        return analyze_php(art, head, evidence_refs=("ev_fixture",))

    (chain,) = verdict("chain.php")
    assert chain.rule_id == "PHP.HEUR.CHAIN" and chain.severity is Severity.HIGH
    assert verdict("single.php") == ()
    assert verdict("clean.php") == ()
    assert verdict("min.min.js") == ()
