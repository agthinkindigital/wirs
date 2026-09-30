"""Modos --cli/--gui (WIRS-139)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from wirs.cli.app import app

separado = CliRunner()


def test_cli_mostra_fases_no_stderr_sem_quebrar_stdout() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        alvo = Path(tmp) / "alvo"
        alvo.mkdir()
        (alvo / "a.php").write_bytes(b"<?php\n// a\n")

        result = separado.invoke(app, ["scan", str(alvo), "--format", "json", "--cli"])

        assert result.exit_code == 0, result.output
        json.loads(result.stdout)  # stdout segue parseável
        assert "[1/4] inventory" in result.stderr
        assert "[done]" in result.stderr


def test_gui_nao_quebra_stdout() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        alvo = Path(tmp) / "alvo"
        alvo.mkdir()
        (alvo / "a.php").write_bytes(b"<?php\n// a\n")

        result = separado.invoke(app, ["scan", str(alvo), "--format", "json", "--gui"])

        assert result.exit_code == 0, result.output
        json.loads(result.stdout)  # tela vive no stderr


def test_gui_e_cli_juntos_falham() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        alvo = Path(tmp) / "alvo"
        alvo.mkdir()

        result = separado.invoke(app, ["scan", str(alvo), "--gui", "--cli"])

        assert result.exit_code == 2


def test_doctor_espelha_lib_yara_e_nao_binario(monkeypatch) -> None:
    import sys
    from types import ModuleType

    real_import = __import__

    def sem_yara(name, *args, **kwargs):
        if name == "yara":
            raise ImportError("sem lib")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", sem_yara)
    ausente = separado.invoke(app, ["doctor"])
    assert ausente.exit_code == 0, ausente.output
    assert "yara" in ausente.output and "unavailable" in ausente.output

    fake = ModuleType("yara")
    fake.__version__ = "9.9.9"
    monkeypatch.setitem(sys.modules, "yara", fake)
    monkeypatch.setattr("builtins.__import__", real_import)
    presente = separado.invoke(app, ["doctor"])
    assert presente.exit_code == 0, presente.output
    assert "9.9.9" in presente.output
