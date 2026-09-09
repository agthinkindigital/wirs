"""Modelo de domínio genérico (stdlib + value objects apenas).

Proibido importar wordpress, yara, wordfence, rich, mysql, typer a partir daqui.
"""

from wirs.domain.artifact import Artifact, ArtifactKind, ArtifactMetadata
from wirs.domain.coverage import CoverageEntry, CoverageState
from wirs.domain.errors import SecurityBoundaryError, TargetError, WirsError
from wirs.domain.evidence import Evidence, Provenance, RedactionState
from wirs.domain.finding import Confidence, ConfidenceClass, Finding, Severity
from wirs.domain.safepath import SafePath
from wirs.domain.target import LocalDirectoryTarget, Target, TargetKind

__all__ = [
    "Artifact",
    "ArtifactKind",
    "ArtifactMetadata",
    "Confidence",
    "ConfidenceClass",
    "CoverageEntry",
    "CoverageState",
    "Evidence",
    "Finding",
    "LocalDirectoryTarget",
    "Provenance",
    "RedactionState",
    "SafePath",
    "SecurityBoundaryError",
    "Severity",
    "Target",
    "TargetError",
    "TargetKind",
    "WirsError",
]
