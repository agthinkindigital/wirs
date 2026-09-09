"""WP-CLI doctor: disponibilidade e versão sem bootstrap da aplicação.

`wp --version` é comando pré-load (não inicializa plugins/themes), logo seguro
no modo `safe_only` (ADR-009). Saída estruturada — nunca texto solto.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass

from wirs.infrastructure.command_runner import CommandRunner

_VERSION = re.compile(r"WP-CLI\s+(\d+\.\d+(?:\.\d+)?)")


@dataclass(frozen=True)
class WpCliStatus:
    available: bool
    path: str | None
    version: str | None
    duration_ms: int = 0
    error: str | None = None


class WpCliDoctor:
    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._runner = runner or CommandRunner()

    def check(self, wp_command: list[str] | None = None, timeout_s: float = 30.0) -> WpCliStatus:
        explicit = wp_command is not None
        cmd = wp_command or ["wp"]
        # Comando explícito: o chamador assume a existência; só o default passa no which.
        path = cmd[0] if explicit else shutil.which(cmd[0])
        if path is None:
            return WpCliStatus(
                available=False, path=None, version=None, error="wp não encontrado no PATH"
            )
        result = self._runner.run([*cmd, "--version"], timeout_s=timeout_s)
        if result.timed_out:
            return WpCliStatus(
                available=False,
                path=path,
                version=None,
                duration_ms=result.duration_ms,
                error="timeout",
            )
        if result.returncode != 0:
            return WpCliStatus(
                available=False,
                path=path,
                version=None,
                duration_ms=result.duration_ms,
                error=result.stderr.strip()[:200] or f"exit {result.returncode}",
            )
        match = _VERSION.search(result.stdout)
        return WpCliStatus(
            available=True,
            path=path,
            version=match.group(1) if match else None,
            duration_ms=result.duration_ms,
        )
