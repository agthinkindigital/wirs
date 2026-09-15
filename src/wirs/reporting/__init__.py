"""Reporting read-only: JSON canônico e views humanas derivadas."""

from wirs.reporting.atomic_writer import write_text_atomic
from wirs.reporting.canonical import SCHEMA_VERSION, CanonicalReport
from wirs.reporting.html import render_forensic_html
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
    "render_forensic_html",
    "render_report",
    "sanitize",
    "write_text_atomic",
]
