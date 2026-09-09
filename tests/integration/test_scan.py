"""`wirs scan` mínimo (WIRS-110): inventory real + JSON/terminal honestos."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from wirs.cli.app import app

runner = CliRunner()


def _fixture(tmp_path) -> str:
    (tmp_path / "index.php").write_bytes(b"<?php // oi")
    sub = tmp_path / "wp-content"
    sub.mkdir()
    (sub / "a.txt").write_bytes(b"a")
    return str(tmp_path)


def test_scan_json_com_coverage(tmp_path) -> None:
    result = runner.invoke(app, ["scan", _fixture(tmp_path), "--format", "json"])

    assert result.exit_code == 0  # sem findings: abaixo do threshold
    data = json.loads(result.output)
    assert data["schema_version"] == "1.0"
    assert data["findings"] == []
    (cov,) = [c for c in data["coverage"] if c["capability"] == "filesystem"]
    assert cov["state"] == "complete"
    assert cov["verified"] == 4  # root + 2 arquivos + 1 diretório


def test_scan_terminal_honesto(tmp_path) -> None:
    result = runner.invoke(app, ["scan", _fixture(tmp_path)])

    assert result.exit_code == 0
    assert "Coverage" in result.output
    assert "filesystem" in result.output


def test_fail_on_threshold(tmp_path) -> None:
    # Mini-WP com 2 sinais (discovery) + PHP em uploads (policy).
    (tmp_path / "wp-includes").mkdir()
    (tmp_path / "wp-includes" / "version.php").write_bytes(b"<?php // v")
    (tmp_path / "wp-admin").mkdir()
    up = tmp_path / "wp-content" / "uploads"
    up.mkdir(parents=True)
    (up / "evil.php").write_bytes(b"<?php // x")

    padrao = runner.invoke(app, ["scan", str(tmp_path), "--format", "json"])
    assert padrao.exit_code == 1  # WP.UPLOAD.EXECUTABLE é HIGH >= high
    data = json.loads(padrao.output)
    assert any(f["rule_id"] == "WP.UPLOAD.EXECUTABLE" for f in data["findings"])

    so_critical = runner.invoke(app, ["scan", str(tmp_path), "--fail-on", "critical"])
    assert so_critical.exit_code == 0  # HIGH < critical: não falha


def test_scan_com_gap_vira_partial(tmp_path, monkeypatch) -> None:
    import os

    (tmp_path / "ok.txt").write_bytes(b"ok")
    sub = tmp_path / "bloq"
    sub.mkdir()

    real_scandir = os.scandir

    def scandir_com_falha(path, *a, **k):
        if os.path.basename(os.fspath(path)) == "bloq":
            raise PermissionError("EACCES simulado")
        return real_scandir(path, *a, **k)

    monkeypatch.setattr(os, "scandir", scandir_com_falha)

    import json as jsonlib

    result = runner.invoke(app, ["scan", str(tmp_path), "--format", "json"])
    assert result.exit_code == 0  # PARTIAL não é finding: não falha
    (cov,) = [
        c for c in jsonlib.loads(result.output)["coverage"] if c["capability"] == "filesystem"
    ]
    assert cov["state"] == "partial"
    assert cov["failed"] == 1


def test_scan_rejeita_perfil_e_formato(tmp_path) -> None:
    assert runner.invoke(app, ["scan", str(tmp_path), "--profile", "turbo"]).exit_code == 2
    assert runner.invoke(app, ["scan", str(tmp_path), "--format", "yaml"]).exit_code == 2
