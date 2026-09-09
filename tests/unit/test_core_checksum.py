"""Core checksum provider (WIRS-064).

Contrato REAL (WP-CLI 2.12.0, validado contra binário em 2026-09-09): o core
NÃO aceita --format — tudo sai em texto no STDERR ("Warning: <msg>: <file>").
Ver docs/providers/wp-cli.md.
"""

from __future__ import annotations

from wirs.domain import IntegrityState, LocalDirectoryTarget
from wirs.infrastructure.command_runner import CommandResult, CommandRunner
from wirs.providers.wp_checksum import verify_core_checksum
from wirs.providers.wpcli import WpCliDoctor


class FakeRunner(CommandRunner):
    def __init__(self, version_out: str, stdout: str, stderr: str, code: int = 1) -> None:
        self._version_out = version_out
        self._stdout = stdout
        self._stderr = stderr
        self._code = code
        self.calls: list[list[str]] = []

    def run(self, argv, *, timeout_s=60.0, max_bytes=1048576):  # type: ignore[override]
        self.calls.append(list(argv))
        if argv[-1] == "--version":
            return CommandResult(0, self._version_out, "", 120, False)
        return CommandResult(self._code, self._stdout, self._stderr, 900, False)


# Saída real de um core adulterado (stdout vazio, tudo no stderr).
FAKE_STDERR = (
    "Warning: File doesn't verify against checksum: wp-includes/version.php\n"
    "Warning: File should not exist: evil.php\n"
    "Error: WordPress installation doesn't verify against checksums.\n"
)


def test_texto_real_normalizado(tmp_path) -> None:
    runner = FakeRunner("WP-CLI 2.12.0\n", "", FAKE_STDERR)
    doctor = WpCliDoctor(runner=runner)
    report = verify_core_checksum(
        LocalDirectoryTarget(tmp_path),
        runner=runner,
        doctor=doctor,
        wp_command=["wp"],
        provider_version="2.12.0",
    )

    assert report.provider_id == "wp-cli-core-checksum"
    assert report.provider_version == "2.12.0"
    por_arquivo = {f.path: f.state for f in report.files}
    assert por_arquivo["wp-includes/version.php"] is IntegrityState.MISMATCH
    assert por_arquivo["evil.php"] is IntegrityState.UNEXPECTED
    argv = [c for c in runner.calls if "verify-checksums" in c][0]
    assert argv[:3] == ["wp", "core", "verify-checksums"]
    assert "--include-root" in argv
    assert not any(a.startswith("--format") for a in argv)  # core real não aceita --format


def _doctor(runner: FakeRunner) -> WpCliDoctor:
    return WpCliDoctor(runner=runner)


def test_malformed_vira_invalid_output(tmp_path) -> None:
    import pytest

    from wirs.domain import ProviderInvalidOutput

    for ruim in [
        "Warning: Mensagem do futuro: x.php\n",
        "Warning: File frobnicate: x.php\n",
        "Warning:\n",
    ]:
        runner = FakeRunner("WP-CLI 2.12.0\n", "", ruim)
        with pytest.raises(ProviderInvalidOutput):
            verify_core_checksum(
                LocalDirectoryTarget(tmp_path),
                runner=runner,
                doctor=_doctor(runner),
                wp_command=["wp"],
            )


def test_success_sem_warnings_vira_vazio(tmp_path) -> None:
    runner = FakeRunner("WP-CLI 2.12.0\n", "Success: WordPress installation verifies.\n", "")
    runner._code = 0
    report = verify_core_checksum(
        LocalDirectoryTarget(tmp_path),
        runner=runner,
        doctor=_doctor(runner),
        wp_command=["wp"],
    )
    assert report.files == () and report.success is True


def test_stdout_vazio_com_erro_vira_execution_error(tmp_path) -> None:
    import pytest

    from wirs.domain import ProviderExecutionError
    from wirs.infrastructure.command_runner import CommandResult as CR

    class FailRunner(FakeRunner):
        def run(self, argv, *, timeout_s=60.0, max_bytes=1048576):  # type: ignore[override]
            if argv[-1] == "--version":
                return CR(0, "WP-CLI 2.12.0\n", "", 10, False)
            return CR(1, "", "Error: sem stdout", 10, False)

    runner = FailRunner("", "", "")
    with pytest.raises(ProviderExecutionError):
        verify_core_checksum(
            LocalDirectoryTarget(tmp_path), runner=runner, doctor=_doctor(runner), wp_command=["wp"]
        )


def test_timeout_vira_provider_timeout(tmp_path) -> None:
    import pytest

    from wirs.domain import ProviderTimeout
    from wirs.infrastructure.command_runner import CommandResult as CR

    class SlowRunner(FakeRunner):
        def run(self, argv, *, timeout_s=60.0, max_bytes=1048576):  # type: ignore[override]
            if argv[-1] == "--version":
                return CR(0, "WP-CLI 2.12.0\n", "", 10, False)
            return CR(124, "", "", 60001, True)

    runner = SlowRunner("", "", "")
    with pytest.raises(ProviderTimeout):
        verify_core_checksum(
            LocalDirectoryTarget(tmp_path), runner=runner, doctor=_doctor(runner), wp_command=["wp"]
        )


def test_wp_ausente_vira_unavailable(tmp_path, monkeypatch) -> None:
    import shutil

    import pytest

    from wirs.domain import ProviderUnavailable

    monkeypatch.setattr(shutil, "which", lambda *_: None)
    with pytest.raises(ProviderUnavailable):
        verify_core_checksum(LocalDirectoryTarget(tmp_path))
