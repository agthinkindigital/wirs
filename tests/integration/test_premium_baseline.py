"""Premium/custom baseline mapping (WIRS-066)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from wirs.cli.app import app
from wirs.infrastructure.baseline import BaselineBuilder

runner = CliRunner()


def _wp_com_premium(tmp: Path) -> tuple[Path, Path]:
    """WP mínimo (2 sinais) + plugin premium. Retorna (root, plugin_dir)."""
    (tmp / "wp-includes").mkdir(parents=True)
    (tmp / "wp-includes" / "version.php").write_bytes(b"<?php\n// versao\n")
    (tmp / "wp-content").mkdir(parents=True)
    premium = tmp / "wp-content" / "plugins" / "premium"
    premium.mkdir(parents=True)
    (premium / "premium.php").write_bytes(b"<?php\n// premium limpo\n")
    (premium / "readme.txt").write_bytes(b"premium\n")
    return tmp, premium


def test_premium_mapeado_limpo_nao_gera_findings() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root, premium = _wp_com_premium(Path(tmp))
        manifest = BaselineBuilder().build(premium, component_id="premium", version="1.0")
        manifest_path = Path(tmp) / "premium.json"
        manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")
        mapping = Path(tmp) / "mapping.json"
        mapping.write_text(
            json.dumps({"wp-content/plugins/premium": str(manifest_path)}), encoding="utf-8"
        )

        result = runner.invoke(
            app, ["scan", str(root), "--baseline", str(mapping), "--format", "json"]
        )

        assert result.exit_code == 0, result.output
        report = json.loads(result.output)
        assert report["findings"] == []


def _com_mapping(tmp: Path, premium: Path) -> Path:
    manifest = BaselineBuilder().build(premium, component_id="premium", version="1.0")
    manifest_path = tmp / "premium.json"
    manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")
    mapping = tmp / "mapping.json"
    mapping.write_text(
        json.dumps({"wp-content/plugins/premium": str(manifest_path)}), encoding="utf-8"
    )
    return mapping


def test_premium_adulterado_gera_mismatch_e_unexpected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root, premium = _wp_com_premium(Path(tmp))
        mapping = _com_mapping(Path(tmp), premium)
        (premium / "premium.php").write_bytes(b"<?php\n// premium ADULTERADO\n")
        (premium / "evil.php").write_bytes(b"<?php\n// extra\n")

        result = runner.invoke(
            app, ["scan", str(root), "--baseline", str(mapping), "--format", "json"]
        )

        assert result.exit_code == 1, result.output
        rules = {f["rule_id"] for f in json.loads(result.output)["findings"]}
        assert "WP.PLUGIN.HASH_MISMATCH" in rules
        assert "WP.PLUGIN.UNEXPECTED_FILE" in rules


def test_premium_sem_mapping_continua_unverified() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root, _premium = _wp_com_premium(Path(tmp))
        mapping = Path(tmp) / "mapping.json"
        mapping.write_text("{}", encoding="utf-8")

        result = runner.invoke(
            app, ["scan", str(root), "--baseline", str(mapping), "--format", "json"]
        )

        assert result.exit_code == 0, result.output
        report = json.loads(result.output)
        assert report["findings"] == []
        # Sem baseline (nem oficial, nem de operador): lacuna nomeada, nunca acusação.
        lacunas = {c["capability"]: c["state"] for c in report["coverage"]}
        assert lacunas.get("baseline:plugin:premium") == "partial"
