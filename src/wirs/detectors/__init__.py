"""Detectores internos (nunca subprocess, nunca I/O direto — via ArtifactReader)."""

from wirs.detectors.executable import looks_executable
from wirs.detectors.ioc_scanner import IocMatch, IocScanResult, scan_bytes, scan_stream
from wirs.detectors.php_heuristics import analyze_php, signal_families

__all__ = [
    "IocMatch",
    "IocScanResult",
    "analyze_php",
    "looks_executable",
    "scan_bytes",
    "scan_stream",
    "signal_families",
]
