"""Reporting read-only: JSON canônico, terminal Rich, Markdown, HTML skeleton."""

from wirs.reporting.atomic_writer import write_text_atomic
from wirs.reporting.canonical import SCHEMA_VERSION, CanonicalReport
from wirs.reporting.markdown import md_safe, render_markdown
from wirs.reporting.redaction import STORE_RAW_CONTENT, redact_mapping, redact_text
from wirs.reporting.terminal import render_report, sanitize

__all__ = [
    "SCHEMA_VERSION",
    "STORE_RAW_CONTENT",
    "CanonicalReport",
    "md_safe",
    "redact_mapping",
    "redact_text",
    "render_markdown",
    "render_report",
    "sanitize",
    "write_text_atomic",
]
