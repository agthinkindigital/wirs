"""Providers de checksum via WP-CLI com anti-corruption layer.

A aplicação nunca vê o formato do vendor: só `CoreChecksumReport` com
`FileIntegrity` normalizados. Mensagem desconhecida = ProviderInvalidOutput
(explícito e versionado), nunca classificação silenciosa errada.
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
from wirs.infrastructure.command_runner import CommandRunner
from wirs.providers.wpcli import WpCliDoctor

PROVIDER_ID = "wp-cli-core-checksum"


@dataclass(frozen=True)
class CoreChecksumReport:
    provider_id: str
    provider_version: str | None
    component: str
    component_version: str | None
    success: bool
    files: tuple[FileIntegrity, ...] = ()


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


def verify_core_checksum(
    target: Target,
    *,
    runner: CommandRunner | None = None,
    doctor: WpCliDoctor | None = None,
    wp_command: list[str] | None = None,
    timeout_s: float = 60.0,
    provider_version: str | None = None,
) -> CoreChecksumReport:
    real_runner = runner or CommandRunner()
    real_doctor = doctor or WpCliDoctor(runner=real_runner)
    status = real_doctor.check(wp_command=wp_command)
    if not status.available:
        raise ProviderUnavailable(status.error or "WP-CLI indisponível")
    version = provider_version or status.version
    argv = (wp_command or ["wp"]) + [
        "core",
        "verify-checksums",
        "--include-root",
        "--format=json",
        f"--path={target.root}",
    ]
    result = real_runner.run(argv, timeout_s=timeout_s)
    if result.timed_out:
        raise ProviderTimeout(f"verify-checksums excedeu {timeout_s}s")
    text = result.stdout.strip()
    if not text:
        if result.returncode != 0:
            raise ProviderExecutionError(result.stderr.strip()[:200] or f"exit {result.returncode}")
        return CoreChecksumReport(PROVIDER_ID, version, "wordpress-core", None, True, ())
    files = parse_core_verify_checksums(text)
    return CoreChecksumReport(
        PROVIDER_ID, version, "wordpress-core", None, success=not files, files=files
    )
