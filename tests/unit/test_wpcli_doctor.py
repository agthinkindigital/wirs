"""WP-CLI doctor (WIRS-063): disponibilidade, versão e timeout, sem bootstrap."""

from __future__ import annotations

from wirs.infrastructure.command_runner import CommandResult, CommandRunner
from wirs.providers.wpcli import WpCliDoctor


class FakeRunner(CommandRunner):
    def __init__(self, result: CommandResult) -> None:
        self._result = result
        self.calls: list[list[str]] = []

    def run(self, argv, *, timeout_s=30.0, max_bytes=1048576):  # type: ignore[override]
        self.calls.append(list(argv))
        return self._result


def test_wpcli_disponivel_com_versao() -> None:
    runner = FakeRunner(
        CommandResult(
            returncode=0, stdout="WP-CLI 2.10.0\n", stderr="", duration_ms=120, timed_out=False
        )
    )
    status = WpCliDoctor(runner=runner).check(wp_command=["wp"])

    assert status.available is True
    assert status.version == "2.10.0"
    assert runner.calls == [["wp", "--version"]]  # pré-load, sem bootstrap


def test_wpcli_ausente_timeout_falha(monkeypatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda *_: None)
    ausente = WpCliDoctor(runner=FakeRunner(CommandResult(0, "", "", 0, False))).check()
    assert ausente.available is False and ausente.path is None

    timeout = WpCliDoctor(runner=FakeRunner(CommandResult(124, "", "", 30001, True))).check(
        wp_command=["wp"]
    )
    assert timeout.available is False and timeout.error == "timeout"

    quebrou = WpCliDoctor(runner=FakeRunner(CommandResult(1, "", "Error: YOLO", 50, False))).check(
        wp_command=["wp"]
    )
    assert quebrou.available is False and "YOLO" in (quebrou.error or "")


def test_command_runner_executa_e_mata_no_timeout() -> None:
    import sys

    runner = CommandRunner()
    ok = runner.run([sys.executable, "-c", "print('oi')"], timeout_s=10.0)
    assert ok.returncode == 0 and ok.stdout.strip() == "oi" and not ok.timed_out

    lento = runner.run([sys.executable, "-c", "import time; time.sleep(30)"], timeout_s=0.5)
    assert lento.timed_out is True

    with __import__("pytest").raises(ValueError):
        runner.run([])
