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

    assert result.exit_code == 3  # pipeline incompleto por construção (Fase A)
    data = json.loads(result.output)
    assert data["schema_version"] == "1.0"
    assert data["findings"] == []
    (cov,) = data["coverage"]
    assert cov["capability"] == "filesystem"
    assert cov["state"] == "complete"
    assert cov["verified"] == 4  # root + 2 arquivos + 1 diretório


def test_scan_terminal_honesto(tmp_path) -> None:
    result = runner.invoke(app, ["scan", _fixture(tmp_path)])

    assert result.exit_code == 3
    assert "Coverage" in result.output
    assert "filesystem" in result.output
    assert "incompleto" in result.output


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
    assert result.exit_code == 3
    (cov,) = jsonlib.loads(result.output)["coverage"]
    assert cov["state"] == "partial"
    assert cov["failed"] == 1


def test_scan_rejeita_perfil_e_formato(tmp_path) -> None:
    assert runner.invoke(app, ["scan", str(tmp_path), "--profile", "turbo"]).exit_code == 2
    assert runner.invoke(app, ["scan", str(tmp_path), "--format", "yaml"]).exit_code == 2
