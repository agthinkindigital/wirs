"""scan --report (WIRS-119)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wirs.cli.app import app

runner = CliRunner()


def test_report_grava_json_canonico() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        alvo = tmp_path / "alvo"
        alvo.mkdir()
        destino = tmp_path / "scan.json"

        result = runner.invoke(
            app, ["scan", str(alvo), "--format", "json", "--report", str(destino)]
        )

        assert result.exit_code == 0, result.output
        do_stdout = json.loads(result.stdout)
        do_arquivo = json.loads(destino.read_text(encoding="utf-8"))
        assert do_arquivo == do_stdout
        assert do_arquivo["schema_version"] == "2.0"


def test_report_preserva_provider_run_sem_findings() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        alvo = Path(tmp) / "alvo"
        alvo.mkdir()

        result = runner.invoke(app, ["scan", str(alvo), "--format", "json"])

        assert result.exit_code == 0, result.output
        payload = json.loads(result.stdout)
        assert payload["findings"] == []
        assert {run["status"] for run in payload["provider_runs"]} == {"unavailable"}
        assert any(run["provider_id"] == "yara" for run in payload["provider_runs"])


def test_report_dentro_do_target_e_recusado() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        alvo = tmp_path / "alvo"
        alvo.mkdir()

        result = runner.invoke(app, ["scan", str(alvo), "--report", str(alvo / "scan.json")])

        assert result.exit_code == 2
        assert not (alvo / "scan.json").exists()


def test_report_symlink_dentro_do_target_e_recusado() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        alvo = tmp_path / "alvo"
        alvo.mkdir()
        externo = tmp_path / "fora.json"
        externo.write_text("sentinela", encoding="utf-8")
        destino = alvo / "scan.json"
        try:
            destino.symlink_to(externo)
        except OSError as e:
            pytest.skip(f"symlink indisponível neste host: {e}")

        result = runner.invoke(app, ["scan", str(alvo), "--report", str(destino)])

        assert result.exit_code == 2
        assert destino.is_symlink()
        assert externo.read_text(encoding="utf-8") == "sentinela"


def test_report_symlink_quebrado_dentro_do_target_e_recusado() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        alvo = tmp_path / "alvo"
        alvo.mkdir()
        destino = alvo / "scan.json"
        try:
            destino.symlink_to(tmp_path / "nao-existe.json")
        except OSError as e:
            pytest.skip(f"symlink indisponível neste host: {e}")

        result = runner.invoke(app, ["scan", str(alvo), "--report", str(destino)])

        assert result.exit_code == 2
        assert destino.is_symlink()
        assert not (tmp_path / "nao-existe.json").exists()


def test_report_em_diretorio_e_recusado() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        alvo = tmp_path / "alvo"
        alvo.mkdir()
        destino = tmp_path / "pasta"
        destino.mkdir()

        result = runner.invoke(app, ["scan", str(alvo), "--report", str(destino)])

        assert result.exit_code == 2
        assert list(destino.iterdir()) == []


def test_report_sem_parcial_e_overwrite() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        alvo = tmp_path / "alvo"
        alvo.mkdir()

        quebrado = runner.invoke(
            app, ["scan", str(alvo), "--report", str(tmp_path / "sem-dir" / "s.json")]
        )
        assert quebrado.exit_code == 4
        assert not (tmp_path / "sem-dir").exists()

        destino = tmp_path / "scan.json"
        destino.write_text("conteudo-antigo", encoding="utf-8")
        result = runner.invoke(app, ["scan", str(alvo), "--report", str(destino)])
        assert result.exit_code == 0, result.output
        assert json.loads(destino.read_text(encoding="utf-8"))["schema_version"] == "2.0"
        assert f"report: {destino}" in result.output
