"""Modelo de domínio genérico (stdlib + value objects apenas).

Proibido importar wordpress, yara, wordfence, rich, mysql, typer a partir daqui.
"""

from wirs.domain.artifact import Artifact, ArtifactKind, ArtifactMetadata
from wirs.domain.errors import SecurityBoundaryError, TargetError, WirsError
from wirs.domain.evidence import Evidence, Provenance, RedactionState
from wirs.domain.safepath import SafePath
from wirs.domain.target import LocalDirectoryTarget, Target, TargetKind

__all__ = [
    "Artifact",
    "ArtifactKind",
    "ArtifactMetadata",
    "Evidence",
    "LocalDirectoryTarget",
    "Provenance",
    "RedactionState",
    "SafePath",
    "SecurityBoundaryError",
    "Target",
    "TargetError",
    "TargetKind",
    "WirsError",
]
