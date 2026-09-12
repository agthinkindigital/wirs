"""Trust explícito na linguagem (WIRS-044)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from wirs.cli.app import app
from wirs.domain import BaselineManifest, BaselineTrust

runner = CliRunner()

_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def _wp(tmp: Path) -> Path:
    (tmp / "wp-includes").mkdir(parents=True)
    (tmp / "wp-includes" / "version.php").write_bytes(b"<?php\n// v\n")
    (tmp / "wp-content").mkdir(parents=True)
    premium = tmp / "wp-content" / "plugins" / "premium"
    premium.mkdir(parents=True)
    (premium / "premium.php").write_bytes(b"<?php\n// ADULTERADO\n")
    return premium


def _manifest(premium: Path, trust: BaselineTrust, tmp: Path, nome: str) -> Path:
    manifest = BaselineManifest(
        component_id="premium",
        version="1.0",
        source="teste",
        trust=trust,
        files={"premium.php": _HASH},
    )
    dest = tmp / nome
    dest.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")
    mapping = tmp / f"map-{nome}"
    mapping.write_text(json.dumps({"wp-content/plugins/premium": str(dest)}), encoding="utf-8")
    return mapping


def test_reference_diff_nao_e_hash_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        premium = _wp(tmp_path)
        map_op = _manifest(premium, BaselineTrust.TRUSTED_OPERATOR, tmp_path, "op.json")
        map_ref = _manifest(premium, BaselineTrust.UNVERIFIED_REFERENCE, tmp_path, "ref.json")

        r_op = runner.invoke(
            app, ["scan", str(tmp_path), "--baseline", str(map_op), "--format", "json"]
        )
        r_ref = runner.invoke(
            app, ["scan", str(tmp_path), "--baseline", str(map_ref), "--format", "json"]
        )

        rules_op = {f["rule_id"] for f in json.loads(r_op.stdout)["findings"]}
        findings_ref = json.loads(r_ref.stdout)["findings"]
        rules_ref = {f["rule_id"] for f in findings_ref}
        assert "WP.PLUGIN.HASH_MISMATCH" in rules_op
        assert "WP.PLUGIN.HASH_MISMATCH" not in rules_ref
        assert "WP.PLUGIN.REFERENCE_DIFF" in rules_ref


def test_missing_e_unexpected_contra_reference_com_confianca_rebaixada() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        premium = _wp(tmp_path)
        (premium / "extra.php").write_bytes(b"<?php\n// extra\n")
        manifest = BaselineManifest(
            component_id="premium",
            version="1.0",
            source="teste",
            trust=BaselineTrust.UNVERIFIED_REFERENCE,
            files={"ausente.php": _HASH, "premium.php": _HASH},
        )
        dest = tmp_path / "ref.json"
        dest.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")
        mapping = tmp_path / "map.json"
        mapping.write_text(json.dumps({"wp-content/plugins/premium": str(dest)}), encoding="utf-8")

        result = runner.invoke(
            app, ["scan", str(tmp_path), "--baseline", str(mapping), "--format", "json"]
        )

        assert result.exit_code == 1, result.output
        por_regra = {f["rule_id"]: f for f in json.loads(result.stdout)["findings"]}
        assert set(por_regra) >= {
            "WP.PLUGIN.REFERENCE_MISSING",
            "WP.PLUGIN.REFERENCE_UNEXPECTED",
            "WP.PLUGIN.REFERENCE_DIFF",
        }
        for finding in por_regra.values():
            assert finding["confidence"]["class"] == "high"
            assert finding["attributes"]["trust"] == "unverified_reference"
            assert "reference" in finding["title"]
