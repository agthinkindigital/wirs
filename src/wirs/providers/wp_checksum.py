"""Providers de checksum via WP-CLI com anti-corruption layer.

Contratos VALIDADOS contra WP-CLI 2.12.0 real (2026-09-09) + fonte
wp-cli/checksum-command — ver docs/providers/wp-cli.md. Diferença crucial:
o CORE não aceita --format (texto no STDERR); PLUGINS aceitam --format=json
com chave `plugin_name`, e skips vivem nos warnings do STDERR.
A aplicação nunca vê esses formatos: só reports normalizados.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wirs.adapters.wordpress.zones import OFFICIAL_ROOT_FILES
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

_CORE_WARNING = re.compile(r"^Warning:\s*(.+?):\s*(\S.*?)\s*$")

# Warnings de skip do plugin (sem baseline oficial → UNVERIFIED, nunca failure).
_SKIP_VERSION = re.compile(
    r"Could not retrieve the (?:version|checksums) for"
    r" (?:version \S+ of )?plugin (\S+?), skipping\."
)
_SKIP_CUSTOM = re.compile(r"Must-use plugin '([^']+)' appears to be a custom file")
_SKIP_MAIN_FILE = re.compile(r"Plugin (\S+) main file is missing")


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
    if "doesn't verify" in low or "does not match" in low:
        return IntegrityState.MISMATCH
    if "doesn't exist" in low:
        return IntegrityState.MISSING
    if "should not exist" in low or "was added" in low or "non-wordpress" in low:
        return IntegrityState.UNEXPECTED
    raise ProviderInvalidOutput(f"mensagem desconhecida do WP-CLI: {message!r}")


def parse_core_verify_checksums(stdout: str, stderr: str = "") -> tuple[FileIntegrity, ...]:
    """Normaliza as linhas `Warning: <msg>: <file>` do core (texto, STDERR).

    Linhas `Success:`/`Error:` são resumo, não evidência. Warning desconhecido
    = ProviderInvalidOutput (explícito), nunca chute.
    """
    files: list[FileIntegrity] = []
    for line in (stdout + "\n" + stderr).splitlines():
        line = line.strip()
        if not line or line.startswith(("Success:", "Error:")):
            continue
        match = _CORE_WARNING.match(line)
        if match is None:
            raise ProviderInvalidOutput(f"linha fora do contrato: {line!r:.200}")
        message, path = match.group(1), match.group(2)
        files.append(FileIntegrity(path=path, state=_state_of(message), note=message))
    return tuple(files)


def _execute_verify(
    target: Target,
    command: list[str],
    *,
    runner: CommandRunner | None,
    doctor: WpCliDoctor | None,
    wp_command: list[str] | None,
    timeout_s: float,
    json_format: bool,
) -> tuple[CommandResult, str | None]:
    """Roda o comando e devolve (resultado, versão do provider). Falhas viram erros tipados."""
    real_runner = runner or CommandRunner()
    real_doctor = doctor or WpCliDoctor(runner=real_runner)
    status = real_doctor.check(wp_command=wp_command)
    if not status.available:
        raise ProviderUnavailable(status.error or "WP-CLI indisponível")
    # Caminho resolvido pelo doctor (bare "wp" não resolve .cmd via CreateProcess).
    base = list(wp_command) if wp_command else [status.path or "wp"]
    argv = base + command
    if json_format:
        argv = [*argv, "--format=json"]
    argv = [*argv, f"--path={target.root}"]
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
        json_format=False,  # core real não aceita --format
    )
    version = provider_version or wp_version
    files = parse_core_verify_checksums(result.stdout, result.stderr)
    if not files and result.returncode != 0:
        # Sem warnings e com falha: quebrou antes de verificar (ex.: sem rede).
        raise ProviderExecutionError(result.stderr.strip()[:200] or f"exit {result.returncode}")
    return CoreChecksumReport(
        PROVIDER_ID, version, "wordpress-core", None, success=not files, files=files
    )


def _plugin_slug_from_path(path: str) -> str:
    """Espelha get_plugin_slug_from_path do WP-CLI (dir ou basename sem .php)."""
    if "/" in path:
        return path.split("/")[0]
    return path[:-4] if path.endswith(".php") else path


def _unverified_from_stderr(stderr: str) -> list[str]:
    """Skips vivem nos warnings do STDERR (fonte, não JSON) → UNVERIFIED."""
    found: list[str] = []
    for line in stderr.splitlines():
        line = line.strip()
        match = _SKIP_VERSION.search(line) or _SKIP_MAIN_FILE.search(line)
        if match is not None:
            slug = match.group(1)
            if slug not in found:
                found.append(slug)
            continue
        custom = _SKIP_CUSTOM.search(line)
        if custom is not None:
            slug = _plugin_slug_from_path(custom.group(1))
            if slug not in found:
                found.append(slug)
    return found


def _extract_json_array(text: str) -> list[Any]:
    stripped = text.strip()
    if not stripped or stripped.startswith("Success:"):
        return []
    try:
        value, _ = json.JSONDecoder().raw_decode(stripped)
    except json.JSONDecodeError as e:
        raise ProviderInvalidOutput(f"JSON inválido do WP-CLI: {e}") from e
    if not isinstance(value, list):
        raise ProviderInvalidOutput(f"esperada lista, veio {type(value).__name__}")
    return value


def parse_plugin_verify_checksums(stdout: str, stderr: str = "") -> PluginChecksumReport:
    """Normaliza JSON `[{plugin_name, file, message}]` + skips do STDERR.

    Mensagens de arquivo seguem o mapa do core; `File was added` (fonte:
    checksum-command) = UNEXPECTED. Skips = UNVERIFIED, nunca failure.
    """
    by_plugin: dict[str, list[FileIntegrity]] = {}
    for entry in _extract_json_array(stdout):
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("plugin_name"), str)
            or not isinstance(entry.get("file"), str)
            or not isinstance(entry.get("message"), str)
        ):
            raise ProviderInvalidOutput(f"entrada fora do contrato: {entry!r:.200}")
        slug = entry["plugin_name"]
        by_plugin.setdefault(slug, []).append(
            FileIntegrity(
                path=entry["file"], state=_state_of(entry["message"]), note=entry["message"]
            )
        )
    plugins = tuple(
        PluginResult(slug=slug, success=not files, files=tuple(files))
        for slug, files in sorted(by_plugin.items())
    )
    return PluginChecksumReport(
        provider_id=PLUGIN_PROVIDER_ID,
        provider_version=None,
        plugins=plugins,
        unverified_plugins=tuple(_unverified_from_stderr(stderr)),
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
    plugins_dir = Path(target.root) / "wp-content" / "plugins"
    try:
        has_plugins = any(entry.is_dir(follow_symlinks=False) for entry in os.scandir(plugins_dir))
    except OSError:
        has_plugins = False
    if not has_plugins:
        # Nada a verificar: nem executa o WP-CLI (sem wp-config, falharia à toa).
        version = provider_version
        if version is None and doctor is not None:
            version = doctor.check(wp_command=wp_command).version
        return PluginChecksumReport(PLUGIN_PROVIDER_ID, version, (), ())
    result, wp_version = _execute_verify(
        target,
        ["plugin", "verify-checksums", "--all", "--strict"],
        runner=runner,
        doctor=doctor,
        wp_command=wp_command,
        timeout_s=timeout_s,
        json_format=True,  # plugins aceitam --format (fonte confirma)
    )
    version = provider_version or wp_version
    text = _stdout_or_raise(result)
    if not text and not result.stderr.strip():
        return PluginChecksumReport(PLUGIN_PROVIDER_ID, version, (), ())
    parsed = parse_plugin_verify_checksums(result.stdout, result.stderr)
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
        # Run completa = tudo no escopo foi verificado; só os divergentes
        # (em files) continuam sujeitos a detecção.
        covers = ("wp-admin/", "wp-includes/", *sorted(OFFICIAL_ROOT_FILES))
        return [
            ComponentIntegrity(
                provider_id=report.provider_id,
                provider_version=report.provider_version,
                component="wordpress-core",
                files=report.files,
                covers=covers,
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
                covers=(f"wp-content/plugins/{result.slug}/",),
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
