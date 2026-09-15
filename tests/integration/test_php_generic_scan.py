"""Primeiro scan PHP genérico local (WIRS-140)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from wirs.adapters.php_generic import PHPGenericAdapter
from wirs.cli.app import app
from wirs.domain import LocalDirectoryTarget

runner = CliRunner()
FIXTURE = Path(__file__).parents[1] / "fixtures" / "generic" / "php_legacy"


def test_aplicacao_php_legada_detecta_php_e_politica_de_zona_estatica() -> None:
    result = runner.invoke(
        app,
        [
            "scan",
            str(FIXTURE),
            "--format",
            "json",
            "--php-static-zone",
            "uploads",
            "--php-static-zone",
            "img",
            "--php-static-zone",
            "assets",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.stdout)
    discovery = PHPGenericAdapter().discover(LocalDirectoryTarget(FIXTURE))
    assert discovery is not None
    assert discovery.platform_id == "php_generic"
    findings = payload["findings"]
    assert [finding["rule_id"] for finding in findings] == ["PHP.ZONE.EXECUTABLE"]
    assert findings[0]["attributes"]["path"] == "uploads/shell.php"
    assert findings[0]["evidence_refs"]


def test_php_legitimo_no_webroot_nao_gera_policy_e_wp_coexiste(tmp_path: Path) -> None:
    (tmp_path / "wp-admin").mkdir()
    (tmp_path / "wp-content").mkdir()
    (tmp_path / "wp-includes").mkdir()
    (tmp_path / "wp-includes" / "version.php").write_text("<?php", encoding="utf-8")
    (tmp_path / "index.php").write_text("<?php echo 'ok';", encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "shell.php").write_text("<?php eval($_GET['x']);", encoding="utf-8")

    result = runner.invoke(
        app,
        ["scan", str(tmp_path), "--format", "json", "--php-static-zone", "assets"],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.stdout)
    assert any(f["attributes"]["path"] == "assets/shell.php" for f in payload["findings"])
    assert not any(f["attributes"]["path"] == "index.php" for f in payload["findings"])
