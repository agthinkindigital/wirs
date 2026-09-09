"""Adapter WordPress: discovery, zones, versionamento, collectors (safe_only)."""

from wirs.adapters.wordpress.discovery import WordPressAdapter
from wirs.adapters.wordpress.policies import RULE_ID as UPLOAD_EXECUTABLE_RULE_ID
from wirs.adapters.wordpress.policies import UploadsExecutablePolicy, check_uploads_executable
from wirs.adapters.wordpress.zones import WordPressZone, classify

__all__ = [
    "UPLOAD_EXECUTABLE_RULE_ID",
    "UploadsExecutablePolicy",
    "WordPressAdapter",
    "WordPressZone",
    "check_uploads_executable",
    "classify",
]
