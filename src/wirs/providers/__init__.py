"""Providers de capabilities externas (WP-CLI, YARA, Wordfence) com anti-corruption layer."""

from wirs.providers.wp_checksum import (
    CoreChecksumReport,
    PluginChecksumReport,
    PluginResult,
    WpCliCoreIntegrity,
    WpCliPluginIntegrity,
    verify_core_checksum,
    verify_plugin_checksums,
)
from wirs.providers.wpcli import WpCliDoctor, WpCliStatus

__all__ = [
    "CoreChecksumReport",
    "PluginChecksumReport",
    "PluginResult",
    "WpCliCoreIntegrity",
    "WpCliPluginIntegrity",
    "WpCliDoctor",
    "WpCliStatus",
    "verify_core_checksum",
    "verify_plugin_checksums",
]
