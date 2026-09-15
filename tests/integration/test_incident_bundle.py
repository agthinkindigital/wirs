"""Incident Bundle local com manifesto (WIRS-130)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wirs.cli.app import app
from wirs.domain import SecurityBoundaryError
from wirs.infrastructure.bundle import load_bundle

runner = CliRunner()
FIXTURE = Path(__file__).parents[1] / "fixtures" / "generic" / "incident_bundle"


def test_scan_bundle_preserva_fontes_e_manifesto_no_report() -> None:
    result = runner.invoke(app, ["scan", str(FIXTURE), "--format", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["manifest"]["target"]["kind"] == "incident_bundle"
    assert payload["manifest"]["source_manifest"]["schema_version"] == "1.0"
    source_refs = [
        source["source_ref"] for source in payload["manifest"]["source_manifest"]["sources"]
    ]
    assert source_refs == ["webroot", "logs"]
    assert {artifact["source_ref"] for artifact in payload["artifacts"]} == {"webroot", "logs"}


def _manifest_for(path: str) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "sources": [
            {
                "source_ref": "escape",
                "path": path,
                "role": "webroot",
                "origin": "fixture",
                "sha256": "0" * 64,
                "trust": "TRUSTED_OPERATOR",
            }
        ],
    }


@pytest.mark.parametrize("path", ["../fora", "/absolute/fora", "C:/fora"])
def test_bundle_rejeita_traversal_e_path_absoluto(tmp_path: Path, path: str) -> None:
    (tmp_path / "wirs-bundle.json").write_text(json.dumps(_manifest_for(path)), encoding="utf-8")

    with pytest.raises(SecurityBoundaryError):
        load_bundle(tmp_path)


def test_bundle_rejeita_source_symlink(tmp_path: Path) -> None:
    external = tmp_path / "fora"
    external.mkdir()
    try:
        (tmp_path / "link").symlink_to(external, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink indisponível neste host: {exc}")
    (tmp_path / "wirs-bundle.json").write_text(json.dumps(_manifest_for("link")), encoding="utf-8")

    with pytest.raises(SecurityBoundaryError):
        load_bundle(tmp_path)
