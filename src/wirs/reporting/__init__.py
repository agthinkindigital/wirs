"""Reporting read-only: JSON canônico, terminal Rich, Markdown, HTML skeleton."""

from wirs.reporting.canonical import SCHEMA_VERSION, CanonicalReport
from wirs.reporting.redaction import STORE_RAW_CONTENT, redact_mapping, redact_text

__all__ = [
    "SCHEMA_VERSION",
    "STORE_RAW_CONTENT",
    "CanonicalReport",
    "redact_mapping",
    "redact_text",
]
