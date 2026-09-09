"""CommandRunner: único caminho para subprocess (WIRS-120, versão mínima).

Regras invioláveis desde já: argv como sequência (nunca string), `shell=False`
sempre, timeout com kill, cap de output. Sanitização de env e cwd explícito
chegam no endurecimento (WIRS-122) — a interface já é a final.
"""

from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool
    truncated: bool = False


_SCRIPT_EXTENSIONS = (".cmd", ".bat")


def windows_shell_prefix(argv: Sequence[str]) -> list[str]:
    """No Windows, .cmd/.bat não executam via CreateProcess: prefixa cmd explícito.

    Continua `shell=False` com argv em lista (sem interpolação nossa); o
    `list2cmdline` do subprocess cita cada argumento. `/d` ignora AutoRun.
    """
    args = [str(a) for a in argv]
    if not args:
        return args
    if os.name == "nt" and args[0].lower().endswith(_SCRIPT_EXTENSIONS):
        return ["cmd.exe", "/d", "/c", *args]
    return args


class CommandRunner:
    def run(
        self,
        argv: Sequence[str],
        *,
        timeout_s: float = 30.0,
        max_bytes: int = 1 << 20,
    ) -> CommandResult:
        args = windows_shell_prefix(argv)
        if not args:
            raise ValueError("argv vazio")
        start = time.monotonic()
        try:
            # Único call site autorizado: o guarda de arquitetura trava qualquer
            # outro `import subprocess`; argv é sequência e shell=False sempre.
            proc = subprocess.run(  # noqa: S603
                args,
                shell=False,
                capture_output=True,
                timeout=timeout_s,
            )
            out, err, timed_out, code = proc.stdout, proc.stderr, False, proc.returncode
        except subprocess.TimeoutExpired as e:
            out, err, timed_out, code = e.stdout or b"", e.stderr or b"", True, 124
        except OSError as e:
            return CommandResult(
                returncode=127,
                stdout="",
                stderr=str(e)[:512],
                duration_ms=self._ms(start),
                timed_out=False,
            )
        duration = self._ms(start)
        text_out = out.decode("utf-8", errors="replace")
        text_err = err.decode("utf-8", errors="replace")
        truncated = False
        if len(text_out) > max_bytes or len(text_err) > max_bytes:
            text_out, text_err, truncated = text_out[:max_bytes], text_err[:max_bytes], True
        return CommandResult(
            returncode=code,
            stdout=text_out,
            stderr=text_err,
            duration_ms=duration,
            timed_out=timed_out,
            truncated=truncated,
        )

    @staticmethod
    def _ms(start: float) -> int:
        return int((time.monotonic() - start) * 1000)
