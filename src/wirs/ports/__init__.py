"""Ports (seams reais apenas): ArtifactSource, ArtifactReader, BaselineProvider,
ExternalAnalyzer, PlatformAdapter, CommandRunner, DatabaseReader, Reporter.
"""

from wirs.ports.checksum import ComponentIntegrity, IntegrityProvider
from wirs.ports.detection import Detector, ProposedFinding
from wirs.ports.platform import PlatformAdapter, PlatformDiscovery
from wirs.ports.reader import ArtifactReader, ReadBudget
from wirs.ports.source import ArtifactSource

__all__ = [
    "ArtifactReader",
    "ArtifactSource",
    "ComponentIntegrity",
    "Detector",
    "IntegrityProvider",
    "PlatformAdapter",
    "PlatformDiscovery",
    "ProposedFinding",
    "ReadBudget",
]
