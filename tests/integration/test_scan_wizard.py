"""Wizard interativo de scan (WIRS-129)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from wirs.cli.app import app

runner = CliRunner()


def test_wizard_wordpress_json_roda_scan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        alvo = tmp_path / "site"
        alvo.mkdir()
        (alvo / "a.txt").write_bytes(b"oi\n")
        relatorio = tmp_path / "saida.json"
        entrada = "\n".join(["1", "2", str(alvo), str(relatorio), "s"]) + "\n"

        result = runner.invoke(app, ["scan", "--wizard"], input=entrada)

        assert result.exit_code == 0, result.output
        dados = json.loads(relatorio.read_text(encoding="utf-8"))
        assert dados["schema_version"] == "1.0"
        assert dados["target_root"] == str(alvo.resolve())


def test_wizard_recusa_plataforma_futura_e_cancela_sem_erro() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        alvo = Path(tmp) / "site"
        alvo.mkdir()

        joomla = runner.invoke(app, ["scan", "--wizard"], input="3\n")
        assert joomla.exit_code == 2

        nao = runner.invoke(
            app, ["scan", "--wizard"], input="\n".join(["1", "1", str(alvo), "n"]) + "\n"
        )
        assert nao.exit_code == 0

        eof = runner.invoke(app, ["scan", "--wizard"], input="")
        assert eof.exit_code == 2
