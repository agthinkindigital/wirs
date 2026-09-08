"""CLI smoke: --help funciona e scan rejeita target inválido com exit 2."""

from typer.testing import CliRunner

from wirs.cli.app import app

runner = CliRunner()


def test_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "scan" in result.output


def test_scan_target_invalido_exit_2(tmp_path) -> None:
    result = runner.invoke(app, ["scan", str(tmp_path / "inexistente")])
    assert result.exit_code == 2
