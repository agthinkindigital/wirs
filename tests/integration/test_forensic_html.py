"""Relatório HTML forense self-contained (WIRS-095)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from typer.testing import CliRunner

from wirs.cli.app import app
from wirs.domain import (
    Artifact,
    ArtifactKind,
    Confidence,
    ConfidenceClass,
    Evidence,
    Finding,
    Provenance,
    SafePath,
    Severity,
)
from wirs.reporting import CanonicalReport, render_forensic_html

runner = CliRunner()


def test_scan_html_eh_self_contained_e_explica_ausencias() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "alvo"
        target.mkdir()
        (target / "index.php").write_text("<?php echo 'ok';", encoding="utf-8")

        result = runner.invoke(app, ["scan", str(target), "--format", "html"])

    assert result.exit_code == 0, result.output
    assert "<!doctype html>" in result.stdout.lower()
    assert "Content-Security-Policy" in result.stdout
    assert "default-src &#x27;none&#x27;" in result.stdout
    assert "Summary" in result.stdout
    assert "Findings" in result.stdout
    assert "Coverage" in result.stdout
    assert "Nenhuma Diagnosis" in result.stdout
    assert "Timeline não disponível" in result.stdout
    assert "https://" not in result.stdout


def test_html_escapa_path_hostil_e_preserva_redaction() -> None:
    artifact = Artifact(
        kind=ArtifactKind.FILE,
        path=SafePath(Path.cwd(), "<script>alert('x')</script>.php"),
        id="art_hostile",
    )
    evidence = Evidence(
        scan_id="scan_hostile",
        kind="test",
        source="test",
        artifact_ref=artifact.id,
        content={"password": "super-secret"},
        provenance=Provenance("test", "1"),
        id="ev_hostile",
    )
    finding = Finding(
        rule_id="TEST.HOSTILE",
        title="<script>alert('x')</script>",
        category="test",
        severity=Severity.HIGH,
        confidence=Confidence(ConfidenceClass.HIGH),
        artifact_ref=artifact.id,
        evidence_refs=(evidence.id,),
    )
    report = CanonicalReport(
        scan_id="scan_hostile",
        target_root="/target/token=target-secret",
        profile="soft",
        artifacts=(artifact,),
        evidence=(evidence,),
        findings=(finding,),
        generated_at=datetime(2026, 9, 15, 12, 0),
    )

    html = render_forensic_html(report)

    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html
    assert "super-secret" not in html
    assert "target-secret" not in html
    assert "innerHTML" not in html


def test_html_report_file_continua_sendo_json_canonico() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        target = tmp_path / "alvo"
        target.mkdir()
        destination = tmp_path / "scan.json"

        result = runner.invoke(
            app,
            [
                "scan",
                str(target),
                "--format",
                "html",
                "--report",
                str(destination),
            ],
        )

        assert result.exit_code == 0, result.output
        assert json.loads(destination.read_text(encoding="utf-8"))["schema_version"] == "2.0"


def test_cli_html_emite_utf8_mesmo_com_console_cp1252(tmp_path) -> None:
    target = tmp_path / "alvo"
    target.mkdir()
    (target / "index.php").write_text("<?php echo 'ok';", encoding="utf-8")
    executable = shutil.which("wirs") or shutil.which("wirs.exe")
    assert executable is not None

    env = os.environ | {"PYTHONIOENCODING": "cp1252"}
    result = subprocess.run(  # noqa: S603 - executable vem do ambiente de testes
        [executable, "scan", str(target), "--format", "html"],
        capture_output=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr.decode(sys.getdefaultencoding(), errors="replace")
    assert "investigação".encode() in result.stdout
    assert b"\xef\xbf\xbd" not in result.stdout
