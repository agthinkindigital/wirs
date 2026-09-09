"""Integração real do plugin checksum: roda quando houver `wp` + fixture WordPress."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "wordpress" / "with_plugins"


def test_verify_plugin_checksums_real() -> None:
    if shutil.which("wp") is None:
        pytest.skip("sem WP-CLI neste ambiente")
    if not (FIXTURE / "wp-content" / "plugins").is_dir():
        pytest.skip("sem fixture wordpress/with_plugins (Fase D)")
    from wirs.domain import LocalDirectoryTarget
    from wirs.providers.wp_checksum import verify_plugin_checksums

    report = verify_plugin_checksums(LocalDirectoryTarget(FIXTURE), timeout_s=180.0)
    assert report.provider_id == "wp-cli-plugin-checksum"
