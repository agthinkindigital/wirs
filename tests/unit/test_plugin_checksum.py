"""Plugin checksum provider (WIRS-065).

Contrato REAL (fonte wp-cli/checksum-command, lido em 2026-09-09): erros em
JSON `[{plugin_name, file, message}]` ('File was added', 'Checksum does not
match'); plugins sem baseline viram WARNINGS no stderr ("Could not retrieve
the ... skipping") — nunca failure. Ver docs/providers/wp-cli.md.
"""

from __future__ import annotations

import json

from wirs.domain import IntegrityState, LocalDirectoryTarget
from wirs.infrastructure.command_runner import CommandResult, CommandRunner
from wirs.providers.wp_checksum import verify_plugin_checksums
from wirs.providers.wpcli import WpCliDoctor


class FakeRunner(CommandRunner):
    def __init__(self, version_out: str, stdout: str, stderr: str = "", code: int = 1) -> None:
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


FAKE_JSON = json.dumps(
    [
        {
            "plugin_name": "akismet",
            "file": "akismet/akismet.php",
            "message": "Checksum does not match",
        },
        {
            "plugin_name": "akismet",
            "file": "akismet/readme.txt",
            "message": "File was added",
        },
    ]
)
FAKE_STDERR = (
    "Warning: Could not retrieve the checksums for version 1.0 of plugin meu-premium, skipping.\n"
)


def _run(tmp_path, out: str = FAKE_JSON, err: str = FAKE_STDERR):
    (tmp_path / "wp-content" / "plugins" / "akismet").mkdir(parents=True)
    runner = FakeRunner("WP-CLI 2.12.0\n", out, err)
    return runner, verify_plugin_checksums(
        LocalDirectoryTarget(tmp_path),
        runner=runner,
        doctor=WpCliDoctor(runner=runner),
        wp_command=["wp"],
    )


def _run_bare(tmp_path, runner):
    (tmp_path / "wp-content" / "plugins" / "akismet").mkdir(parents=True, exist_ok=True)
    return verify_plugin_checksums(
        LocalDirectoryTarget(tmp_path),
        runner=runner,
        doctor=WpCliDoctor(runner=runner),
        wp_command=["wp"],
    )


def test_sem_plugins_nem_chama_wp(tmp_path) -> None:
    (tmp_path / "wp-content" / "plugins").mkdir(parents=True)

    runner = FakeRunner("WP-CLI 2.12.0\n", "NUNCA", "")
    report = verify_plugin_checksums(
        LocalDirectoryTarget(tmp_path),
        runner=runner,
        doctor=WpCliDoctor(runner=runner),
        wp_command=["wp"],
    )

    assert report.plugins == () and report.unverified_plugins == ()
    assert all("verify-checksums" not in c for c in runner.calls)  # nem executou


def test_json_por_plugin_normalizado(tmp_path) -> None:
    runner, report = _run(tmp_path)

    assert report.provider_id == "wp-cli-plugin-checksum"
    akismet = next(p for p in report.plugins if p.slug == "akismet")
    assert akismet.files[0].state is IntegrityState.MISMATCH
    assert akismet.files[1].state is IntegrityState.UNEXPECTED  # 'File was added'
    assert akismet.success is False
    assert "meu-premium" in report.unverified_plugins  # skip no stderr, nunca failure
    assert all(p.slug != "meu-premium" for p in report.plugins)
    argv = [c for c in runner.calls if "verify-checksums" in c][0]
    assert argv[1:4] == ["plugin", "verify-checksums", "--all"]
    assert "--strict" in argv and "--format=json" in argv


def test_shape_do_core_rejeitado_e_falhas_propagadas(tmp_path) -> None:
    import pytest

    from wirs.domain import ProviderInvalidOutput, ProviderTimeout
    from wirs.infrastructure.command_runner import CommandResult as CR

    core_shaped = FakeRunner("WP-CLI 2.12.0\n", '[{"file": "x.php", "message": "y"}]')
    with pytest.raises(ProviderInvalidOutput):  # sem plugin_name: não é contrato
        _run_bare(tmp_path, core_shaped)

    for ruim in ["não é json", '{"a": 1}', '[{"plugin_name": "a"}]']:
        r = FakeRunner("WP-CLI 2.12.0\n", ruim)
        with pytest.raises(ProviderInvalidOutput):
            _run_bare(tmp_path, r)

    class SlowRunner(FakeRunner):
        def run(self, argv, *, timeout_s=120.0, max_bytes=1048576):  # type: ignore[override]
            if argv[-1] == "--version":
                return CR(0, "WP-CLI 2.12.0\n", "", 10, False)
            return CR(124, "", "", 120001, True)

    slow = SlowRunner("", "", "")
    with pytest.raises(ProviderTimeout):
        _run_bare(tmp_path, slow)


def test_wp_ausente_vira_unavailable(tmp_path, monkeypatch) -> None:
    import shutil

    import pytest

    from wirs.domain import ProviderUnavailable

    monkeypatch.setattr(shutil, "which", lambda *_: None)
    (tmp_path / "wp-content" / "plugins" / "x").mkdir(parents=True)
    with pytest.raises(ProviderUnavailable):
        verify_plugin_checksums(LocalDirectoryTarget(tmp_path))
