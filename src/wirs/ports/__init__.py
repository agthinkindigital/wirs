"""Ports (seams reais apenas): ArtifactSource, ArtifactReader, BaselineProvider,
ExternalAnalyzer, PlatformAdapter, CommandRunner, DatabaseReader, Reporter.
"""

from wirs.ports.platform import PlatformAdapter, PlatformDiscovery
from wirs.ports.source import ArtifactSource

__all__ = ["ArtifactSource", "PlatformAdapter", "PlatformDiscovery"]
