"""Providers de capabilities externas (WP-CLI, YARA, Wordfence) com anti-corruption layer."""

from wirs.providers.wpcli import WpCliDoctor, WpCliStatus

__all__ = ["WpCliDoctor", "WpCliStatus"]
