"""Providers de capabilities externas (WP-CLI, YARA, Wordfence) com anti-corruption layer."""

from wirs.providers.wp_checksum import CoreChecksumReport, verify_core_checksum
from wirs.providers.wpcli import WpCliDoctor, WpCliStatus

__all__ = [
    "CoreChecksumReport",
    "WpCliDoctor",
    "WpCliStatus",
    "verify_core_checksum",
]
