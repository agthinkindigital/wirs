"""scan --report (WIRS-119)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

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
        assert do_arquivo["schema_version"] == "1.0"


def test_report_dentro_do_target_e_recusado() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        alvo = tmp_path / "alvo"
        alvo.mkdir()

        result = runner.invoke(app, ["scan", str(alvo), "--report", str(alvo / "scan.json")])

        assert result.exit_code == 2
        assert not (alvo / "scan.json").exists()


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
        assert json.loads(destino.read_text(encoding="utf-8"))["schema_version"] == "1.0"
        assert f"report: {destino}" in result.output
