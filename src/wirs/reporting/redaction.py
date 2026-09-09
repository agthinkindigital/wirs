"""Redaction de secrets na fronteira de coleta (WIRS-092).

Aplica-se ao conteúdo ANTES de construir Evidence/report — nunca só no
renderer. Padrões conservadores: exigem nome de chave por perto, então hashes,
IDs e versões legítimos passam intactos.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

REDACTED = "[REDACTED_SECRET]"

# Conteúdo bruto de arquivo nunca é armazenado por padrão (WIRS-111 liga na config).
STORE_RAW_CONTENT = False

_PATTERNS: tuple[re.Pattern[str], ...] = (
    # define( 'DB_PASSWORD', '...' ) — e variações de quote/espaço.
    re.compile(r"(define\(\s*['\"]DB_PASSWORD['\"]\s*,\s*['\"])(.*?)(['\"]\s*\))"),
    # Bloco de chave privada (multilinha).
    re.compile(
        r"-----BEGIN (?:RSA )?PRIVATE KEY-----.*?-----END (?:RSA )?PRIVATE KEY-----",
        re.DOTALL,
    ),
    # Atribuições password/passwd/pwd/secret/api_key/token (tolerante a case).
    re.compile(
        r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|token)\b\s*[:=]\s*['\"]?"
        r"([^\s'\";,}]+)"
    ),
    # AWS access key.
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    # Bearer token.
    re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]+=*\b"),
)


_KEY_NAMES = re.compile(r"(?i)^(password|passwd|pwd|secret|api[_-]?key|token|db_password)$")


def _scrub(text: str) -> str:
    out = text
    # DB_PASSWORD: preserva a moldura, troca só o segredo.
    out = _PATTERNS[0].sub(r"\1" + REDACTED + r"\3", out)
    for rx in _PATTERNS[1:]:
        out = rx.sub(REDACTED, out)
    return out


def redact_text(text: str) -> str:
    return _scrub(text)


def redact_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    """Redige recursivamente str/bytes em mappings (evidência antes do to_dict)."""

    def clean(value: Any) -> Any:
        if isinstance(value, str):
            return _scrub(value)
        if isinstance(value, bytes):
            return _scrub(value.decode("utf-8", errors="replace")).encode("utf-8")
        if isinstance(value, Mapping):
            return {
                k: (REDACTED if isinstance(k, str) and _KEY_NAMES.match(k) else clean(v))
                for k, v in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [clean(v) for v in value]
        return value

    return {k: clean(v) for k, v in data.items()}
