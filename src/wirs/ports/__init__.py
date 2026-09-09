"""Ports (seams reais apenas): ArtifactSource, ArtifactReader, BaselineProvider,
ExternalAnalyzer, PlatformAdapter, CommandRunner, DatabaseReader, Reporter.
"""

from wirs.ports.platform import PlatformAdapter, PlatformDiscovery

__all__ = ["PlatformAdapter", "PlatformDiscovery"]
