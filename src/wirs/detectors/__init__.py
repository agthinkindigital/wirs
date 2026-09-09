"""Detectores internos (nunca subprocess, nunca I/O direto — via ArtifactReader)."""

from wirs.detectors.executable import looks_executable

__all__ = ["looks_executable"]
