"""Adapter WordPress: discovery, zones, versionamento, collectors (safe_only)."""

from wirs.adapters.wordpress.discovery import WordPressAdapter
from wirs.adapters.wordpress.zones import WordPressZone, classify

__all__ = ["WordPressAdapter", "WordPressZone", "classify"]
