"""Compat: implementação mora em wirs.domain.redaction (primitivo de segurança)."""

from __future__ import annotations

from wirs.domain.redaction import REDACTED, STORE_RAW_CONTENT, redact_mapping, redact_text

__all__ = ["REDACTED", "STORE_RAW_CONTENT", "redact_mapping", "redact_text"]
