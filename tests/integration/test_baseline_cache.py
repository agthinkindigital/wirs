"""Cache de baseline (WIRS-045)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from wirs.cli.app import app
from wirs.domain import BaselineManifest, BaselineTrust
from wirs.infrastructure.baseline import BaselineBuilder
from wirs.infrastructure.baseline_cache import BaselineCache

runner = CliRunner()


def test_cache_store_e_scan_via_cache() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        premium = tmp_path / "premium"
        premium.mkdir()
        (premium / "premium.php").write_bytes(b"<?php\n// limpo\n")
        manifest = BaselineBuilder().build(premium, component_id="premium", version="1.0")
        manifest_path = tmp_path / "premium.json"
        manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")
        cache = tmp_path / "cache"

        r_store = runner.invoke(
            app,
            [
                "baseline",
                "cache-store",
                str(manifest_path),
                "--origin",
                "zip-do-fornecedor",
                "--cache-dir",
                str(cache),
            ],
        )
        assert r_store.exit_code == 0, r_store.output

        site = tmp_path / "site"
        (site / "wp-includes").mkdir(parents=True)
        (site / "wp-includes" / "version.php").write_bytes(b"<?php\n// v\n")
        destino = site / "wp-content" / "plugins" / "premium"
        destino.mkdir(parents=True)
        (destino / "premium.php").write_bytes(b"<?php\n// limpo\n")
        mapping = tmp_path / "mapping.json"
        mapping.write_text(
            json.dumps({"wp-content/plugins/premium": "cache:premium:1.0"}), encoding="utf-8"
        )

        result = runner.invoke(
            app,
            [
                "scan",
                str(site),
                "--baseline",
                str(mapping),
                "--cache-dir",
                str(cache),
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout)["findings"] == []


def test_cache_divergente_traz_staleness_e_reference_nunca_viola() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        cache = tmp_path / "cache"
        manifest = BaselineManifest(
            component_id="premium",
            version="1.0",
            source="zip-do-fornecedor",
            trust=BaselineTrust.UNVERIFIED_REFERENCE,
            files={
                "premium.php": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            },
        )
        assert BaselineCache(cache).store(manifest, origin="zip-do-fornecedor")

        site = tmp_path / "site"
        (site / "wp-includes").mkdir(parents=True)
        (site / "wp-includes" / "version.php").write_bytes(b"<?php\n// v\n")
        destino = site / "wp-content" / "plugins" / "premium"
        destino.mkdir(parents=True)
        (destino / "premium.php").write_bytes(b"<?php\n// mudou\n")
        mapping = tmp_path / "mapping.json"
        mapping.write_text(
            json.dumps({"wp-content/plugins/premium": "cache:premium:1.0"}), encoding="utf-8"
        )

        result = runner.invoke(
            app,
            [
                "scan",
                str(site),
                "--baseline",
                str(mapping),
                "--cache-dir",
                str(cache),
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 1, result.output
        findings = json.loads(result.stdout)["findings"]
        regras = {f["rule_id"] for f in findings}
        assert "WP.PLUGIN.REFERENCE_DIFF" in regras
        assert "WP.PLUGIN.HASH_MISMATCH" not in regras
        nota = next(f for f in findings if f["rule_id"] == "WP.PLUGIN.REFERENCE_DIFF")
        assert "cache de 0d, origem zip-do-fornecedor" in nota["attributes"]["note"]
