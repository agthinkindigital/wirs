"""Detectores internos (nunca subprocess, nunca I/O direto — via ArtifactReader)."""

from wirs.detectors.executable import looks_executable
from wirs.detectors.ioc_scanner import IocMatch, IocScanResult, scan_bytes, scan_stream

__all__ = ["IocMatch", "IocScanResult", "looks_executable", "scan_bytes", "scan_stream"]
