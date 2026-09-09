"""Modelo de domínio genérico (stdlib + value objects apenas).

Proibido importar wordpress, yara, wordfence, rich, mysql, typer a partir daqui.
"""

from wirs.domain.artifact import Artifact, ArtifactKind, ArtifactMetadata
from wirs.domain.coverage import CoverageEntry, CoverageState
from wirs.domain.errors import (
    BudgetExceeded,
    ProviderError,
    ProviderExecutionError,
    ProviderInvalidOutput,
    ProviderTimeout,
    ProviderUnavailable,
    ReadCancelled,
    SecurityBoundaryError,
    TargetError,
    WirsError,
)
from wirs.domain.evidence import Evidence, Provenance, RedactionState
from wirs.domain.finding import Confidence, ConfidenceClass, Finding, Severity
from wirs.domain.integrity import FileIntegrity, IntegrityState
from wirs.domain.ioc import IOC, IOCKind
from wirs.domain.redaction import REDACTED, STORE_RAW_CONTENT, redact_mapping, redact_text
from wirs.domain.safepath import SafePath
from wirs.domain.target import LocalDirectoryTarget, Target, TargetKind

__all__ = [
    "Artifact",
    "ArtifactKind",
    "ArtifactMetadata",
    "BudgetExceeded",
    "Confidence",
    "ConfidenceClass",
    "CoverageEntry",
    "CoverageState",
    "Evidence",
    "FileIntegrity",
    "Finding",
    "IntegrityState",
    "IOC",
    "IOCKind",
    "LocalDirectoryTarget",
    "Provenance",
    "ProviderError",
    "ProviderExecutionError",
    "ProviderInvalidOutput",
    "ProviderTimeout",
    "ProviderUnavailable",
    "REDACTED",
    "ReadCancelled",
    "RedactionState",
    "SafePath",
    "SecurityBoundaryError",
    "Severity",
    "STORE_RAW_CONTENT",
    "Target",
    "TargetError",
    "TargetKind",
    "WirsError",
    "redact_mapping",
    "redact_text",
]
