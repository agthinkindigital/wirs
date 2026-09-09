"""Core checksum provider (WIRS-064).

Contrato WP-CLI (doc oficial `wp core verify-checksums`): roda em
`before_wp_load`, baixa md5 do WordPress.org por versão+locale, `--format=json`
emite LISTA de {"file", "message"} e exit != 0 quando algo diverge.
"""

from __future__ import annotations

import json

from wirs.domain import IntegrityState, LocalDirectoryTarget
from wirs.infrastructure.command_runner import CommandResult, CommandRunner
from wirs.providers.wp_checksum import verify_core_checksum
from wirs.providers.wpcli import WpCliDoctor


class FakeRunner(CommandRunner):
    def __init__(self, version_out: str, verify_out: str, verify_code: int = 1) -> None:
        self._version_out = version_out
        self._verify_out = verify_out
        self._verify_code = verify_code
        self.calls: list[list[str]] = []

    def run(self, argv, *, timeout_s=60.0, max_bytes=1048576):  # type: ignore[override]
        self.calls.append(list(argv))
        if argv[-1] == "--version":
            return CommandResult(0, self._version_out, "", 120, False)
        return CommandResult(self._verify_code, self._verify_out, "", 900, False)


FAKE_JSON = json.dumps(
    [
        {"file": "wp-includes/version.php", "message": "File doesn't verify against checksum"},
        {"file": "readme.html", "message": "File doesn't exist"},
        {"file": "evil.php", "message": "File should not exist"},
    ]
)


def test_json_normalizado(tmp_path) -> None:
    runner = FakeRunner("WP-CLI 2.10.0\n", FAKE_JSON)
    doctor = WpCliDoctor(runner=runner)
    report = verify_core_checksum(
        LocalDirectoryTarget(tmp_path),
        runner=runner,
        doctor=doctor,
        wp_command=["wp"],
        provider_version="2.10.0",
    )

    assert report.provider_id == "wp-cli-core-checksum"
    assert report.provider_version == "2.10.0"
    por_arquivo = {f.path: f.state for f in report.files}
    assert por_arquivo["wp-includes/version.php"] is IntegrityState.MISMATCH
    assert por_arquivo["readme.html"] is IntegrityState.MISSING
    assert por_arquivo["evil.php"] is IntegrityState.UNEXPECTED
    argv = [c for c in runner.calls if "verify-checksums" in c][0]
    assert argv[:4] == ["wp", "core", "verify-checksums", "--include-root"]
    assert "--format=json" in argv  # exit != 0 é sinal, não erro: parseou normal


def _doctor(runner: FakeRunner) -> WpCliDoctor:
    return WpCliDoctor(runner=runner)


def test_malformed_vira_invalid_output(tmp_path) -> None:
    import pytest

    from wirs.domain import ProviderInvalidOutput

    for ruim in [
        "não é json",
        '{"a": 1}',
        '[{"file": 1}]',
        '[{"file": "x.php", "message": "Mensagem do futuro"}]',
    ]:
        runner = FakeRunner("WP-CLI 2.10.0\n", ruim)
        with pytest.raises(ProviderInvalidOutput):
            verify_core_checksum(
                LocalDirectoryTarget(tmp_path),
                runner=runner,
                doctor=_doctor(runner),
                wp_command=["wp"],
            )


def test_stdout_vazio_com_erro_vira_execution_error(tmp_path) -> None:
    import pytest

    from wirs.domain import ProviderExecutionError
    from wirs.infrastructure.command_runner import CommandResult as CR

    class FailRunner(FakeRunner):
        def run(self, argv, *, timeout_s=60.0, max_bytes=1048576):  # type: ignore[override]
            if argv[-1] == "--version":
                return CR(0, "WP-CLI 2.10.0\n", "", 10, False)
            return CR(1, "", "Error: sem stdout", 10, False)

    runner = FailRunner("", "")
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
                return CR(0, "WP-CLI 2.10.0\n", "", 10, False)
            return CR(124, "", "", 60001, True)

    runner = SlowRunner("", "")
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
