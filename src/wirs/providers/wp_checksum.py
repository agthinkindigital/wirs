"""Providers de checksum via WP-CLI com anti-corruption layer.

A aplicação nunca vê o formato do vendor: só reports com `FileIntegrity`
normalizados. Mensagem desconhecida = ProviderInvalidOutput (explícito e
versionado), nunca classificação silenciosa errada.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from wirs.domain import IntegrityState, Target
from wirs.domain.errors import (
    ProviderExecutionError,
    ProviderInvalidOutput,
    ProviderTimeout,
    ProviderUnavailable,
)
from wirs.domain.integrity import FileIntegrity
from wirs.infrastructure.command_runner import CommandResult, CommandRunner
from wirs.ports.checksum import ComponentIntegrity
from wirs.providers.wpcli import WpCliDoctor

PROVIDER_ID = "wp-cli-core-checksum"
PLUGIN_PROVIDER_ID = "wp-cli-plugin-checksum"

# Contrato ASSUMIDO para plugins (doc oficial não mostra o JSON): entradas com
# slug do componente + mensagens de skip tabeladas. A confirmar contra WP-CLI
# real — ver docs/providers/wp-cli.md.
UNVERIFIED_MARKERS = (
    "not found",
    "doesn't exist",
    "does not exist",
    "no checksum",
    "no checksums",
    "skipped",
    "unavailable",
)


@dataclass(frozen=True)
class CoreChecksumReport:
    provider_id: str
    provider_version: str | None
    component: str
    component_version: str | None
    success: bool
    files: tuple[FileIntegrity, ...] = ()


@dataclass(frozen=True)
class PluginResult:
    slug: str
    success: bool
    files: tuple[FileIntegrity, ...] = ()


@dataclass(frozen=True)
class PluginChecksumReport:
    provider_id: str
    provider_version: str | None
    plugins: tuple[PluginResult, ...] = ()
    unverified_plugins: tuple[str, ...] = ()


def _state_of(message: str) -> IntegrityState:
    low = message.lower()
    if "doesn't verify" in low:
        return IntegrityState.MISMATCH
    if "doesn't exist" in low:
        return IntegrityState.MISSING
    if "should not exist" in low or "was added" in low or "non-wordpress" in low:
        return IntegrityState.UNEXPECTED
    raise ProviderInvalidOutput(f"mensagem desconhecida do WP-CLI: {message!r}")


def parse_core_verify_checksums(output: str) -> tuple[FileIntegrity, ...]:
    """Normaliza o JSON `[{file, message}]` do WP-CLI. Contrato estrito."""
    try:
        data: Any = json.loads(output)
    except json.JSONDecodeError as e:
        raise ProviderInvalidOutput(f"JSON inválido do WP-CLI: {e}") from e
    if not isinstance(data, list):
        raise ProviderInvalidOutput(f"esperada lista, veio {type(data).__name__}")
    files: list[FileIntegrity] = []
    for entry in data:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("file"), str)
            or not isinstance(entry.get("message"), str)
        ):
            raise ProviderInvalidOutput(f"entrada fora do contrato: {entry!r:.200}")
        files.append(
            FileIntegrity(
                path=entry["file"], state=_state_of(entry["message"]), note=entry["message"]
            )
        )
    return tuple(files)


def _execute_verify(
    target: Target,
    command: list[str],
    *,
    runner: CommandRunner | None,
    doctor: WpCliDoctor | None,
    wp_command: list[str] | None,
    timeout_s: float,
) -> tuple[CommandResult, str | None]:
    """Roda o comando e devolve (resultado, versão do provider). Falhas viram erros tipados."""
    real_runner = runner or CommandRunner()
    real_doctor = doctor or WpCliDoctor(runner=real_runner)
    status = real_doctor.check(wp_command=wp_command)
    if not status.available:
        raise ProviderUnavailable(status.error or "WP-CLI indisponível")
    argv = (wp_command or ["wp"]) + command + ["--format=json", f"--path={target.root}"]
    result = real_runner.run(argv, timeout_s=timeout_s)
    if result.timed_out:
        raise ProviderTimeout(f"{' '.join(command)} excedeu {timeout_s}s")
    return result, status.version


def _stdout_or_raise(result: CommandResult) -> str:
    text = result.stdout.strip()
    if text:
        return text
    if result.returncode != 0:
        raise ProviderExecutionError(result.stderr.strip()[:200] or f"exit {result.returncode}")
    return ""


def verify_core_checksum(
    target: Target,
    *,
    runner: CommandRunner | None = None,
    doctor: WpCliDoctor | None = None,
    wp_command: list[str] | None = None,
    timeout_s: float = 60.0,
    provider_version: str | None = None,
) -> CoreChecksumReport:
    result, wp_version = _execute_verify(
        target,
        ["core", "verify-checksums", "--include-root"],
        runner=runner,
        doctor=doctor,
        wp_command=wp_command,
        timeout_s=timeout_s,
    )
    version = provider_version or wp_version
    text = _stdout_or_raise(result)
    if not text:
        return CoreChecksumReport(PROVIDER_ID, version, "wordpress-core", None, True, ())
    files = parse_core_verify_checksums(text)
    return CoreChecksumReport(
        PROVIDER_ID, version, "wordpress-core", None, success=not files, files=files
    )


def _is_unverified_skip(message: str) -> bool:
    return any(m in message.lower() for m in UNVERIFIED_MARKERS)


def parse_plugin_verify_checksums(output: str) -> PluginChecksumReport:
    """Normaliza o JSON `[{plugin, file?, message}]`. Contrato assumido — estrito."""
    try:
        data: Any = json.loads(output)
    except json.JSONDecodeError as e:
        raise ProviderInvalidOutput(f"JSON inválido do WP-CLI: {e}") from e
    if not isinstance(data, list):
        raise ProviderInvalidOutput(f"esperada lista, veio {type(data).__name__}")
    by_plugin: dict[str, list[FileIntegrity]] = {}
    unverified: list[str] = []
    for entry in data:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("plugin"), str)
            or not isinstance(entry.get("message"), str)
        ):
            raise ProviderInvalidOutput(f"entrada fora do contrato: {entry!r:.200}")
        slug, message = entry["plugin"], entry["message"]
        if "file" not in entry:
            if _is_unverified_skip(message):
                if slug not in unverified:
                    unverified.append(slug)
                continue
            raise ProviderInvalidOutput(f"entrada de plugin sem file: {entry!r:.200}")
        if not isinstance(entry["file"], str):
            raise ProviderInvalidOutput(f"entrada fora do contrato: {entry!r:.200}")
        by_plugin.setdefault(slug, []).append(
            FileIntegrity(path=entry["file"], state=_state_of(message), note=message)
        )
    plugins = tuple(
        PluginResult(slug=slug, success=not files, files=tuple(files))
        for slug, files in sorted(by_plugin.items())
    )
    return PluginChecksumReport(
        provider_id=PLUGIN_PROVIDER_ID,
        provider_version=None,
        plugins=plugins,
        unverified_plugins=tuple(unverified),
    )


def verify_plugin_checksums(
    target: Target,
    *,
    runner: CommandRunner | None = None,
    doctor: WpCliDoctor | None = None,
    wp_command: list[str] | None = None,
    timeout_s: float = 120.0,
    provider_version: str | None = None,
) -> PluginChecksumReport:
    result, wp_version = _execute_verify(
        target,
        ["plugin", "verify-checksums", "--all", "--strict"],
        runner=runner,
        doctor=doctor,
        wp_command=wp_command,
        timeout_s=timeout_s,
    )
    version = provider_version or wp_version
    text = _stdout_or_raise(result)
    if not text:
        return PluginChecksumReport(PLUGIN_PROVIDER_ID, version, (), ())
    parsed = parse_plugin_verify_checksums(text)
    return PluginChecksumReport(
        provider_id=parsed.provider_id,
        provider_version=version,
        plugins=parsed.plugins,
        unverified_plugins=parsed.unverified_plugins,
    )


class WpCliCoreIntegrity:
    """Adapter WP-CLI → seam IntegrityProvider (montado no CLI)."""

    id = "wp-cli-core-checksum"

    def __init__(
        self,
        *,
        runner: CommandRunner | None = None,
        wp_command: list[str] | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        self._runner = runner
        self._wp_command = wp_command
        self._timeout_s = timeout_s

    def verify(self, target: Target) -> list[ComponentIntegrity]:
        report = verify_core_checksum(
            target, runner=self._runner, wp_command=self._wp_command, timeout_s=self._timeout_s
        )
        return [
            ComponentIntegrity(
                provider_id=report.provider_id,
                provider_version=report.provider_version,
                component="wordpress-core",
                files=report.files,
            )
        ]


class WpCliPluginIntegrity:
    """Adapter WP-CLI → seam IntegrityProvider (montado no CLI)."""

    id = "wp-cli-plugin-checksum"

    def __init__(
        self,
        *,
        runner: CommandRunner | None = None,
        wp_command: list[str] | None = None,
        timeout_s: float = 120.0,
    ) -> None:
        self._runner = runner
        self._wp_command = wp_command
        self._timeout_s = timeout_s

    def verify(self, target: Target) -> list[ComponentIntegrity]:
        report = verify_plugin_checksums(
            target, runner=self._runner, wp_command=self._wp_command, timeout_s=self._timeout_s
        )
        out = [
            ComponentIntegrity(
                provider_id=report.provider_id,
                provider_version=report.provider_version,
                component=f"plugin:{result.slug}",
                files=result.files,
            )
            for result in report.plugins
        ]
        out.extend(
            ComponentIntegrity(
                provider_id=report.provider_id,
                provider_version=report.provider_version,
                component=f"plugin:{slug}",
                unverified=True,
            )
            for slug in report.unverified_plugins
        )
        return out
