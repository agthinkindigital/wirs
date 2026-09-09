"""Integração real do core checksum: roda quando houver `wp` + fixture WordPress.

Sem WP-CLI ou sem fixture, pula com motivo explícito (o contrato fake já cobre
a lógica em tests/unit/test_core_checksum.py).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "wordpress" / "clean_core"


def test_verify_checksums_real() -> None:
    if shutil.which("wp") is None:
        pytest.skip("sem WP-CLI neste ambiente")
    if not (FIXTURE / "wp-includes" / "version.php").exists():
        pytest.skip("sem fixture wordpress/clean_core (Fase D)")
    from wirs.domain import LocalDirectoryTarget
    from wirs.providers.wp_checksum import verify_core_checksum

    report = verify_core_checksum(LocalDirectoryTarget(FIXTURE), timeout_s=120.0)
    assert report.provider_id == "wp-cli-core-checksum"
    assert report.provider_version is not None
