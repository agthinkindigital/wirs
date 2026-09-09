"""Upload executable policy (WIRS-068): conteúdo executável em zona de uploads."""

from __future__ import annotations

from wirs.adapters.wordpress.policies import check_uploads_executable
from wirs.adapters.wordpress.zones import classify
from wirs.detectors.executable import looks_executable
from wirs.domain import Artifact, ArtifactKind, SafePath, Severity


def test_conteudo_executavel_detectado() -> None:
    assert looks_executable(b"<?php // webshell inerte")
    assert looks_executable(b"<?= $x ?>")
    assert looks_executable(b"#!/usr/bin/env php\n<?php")
    assert looks_executable(b"<script>alert(1)</script>")


def test_conteudo_inerte_nao_acusa() -> None:
    assert not looks_executable(b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # jpeg
    assert not looks_executable(b"GIF89a" + b"\x00" * 20)
    assert not looks_executable(b'<?xml version="1.0"?><svg/>')  # svg legítimo
    assert not looks_executable(b"hello world")
    assert not looks_executable(b"")


def _artifact(tmp_path, relative: str) -> Artifact:
    return Artifact(kind=ArtifactKind.FILE, path=SafePath(tmp_path, relative))


def test_php_em_uploads_vira_policy_finding(tmp_path) -> None:
    artifact = _artifact(tmp_path, "wp-content/uploads/2026/evil.php")
    finding = check_uploads_executable(
        artifact,
        classify(artifact.path.relative),
        b"<?php // inerte",
        evidence_refs=("ev_1",),
    )

    assert finding is not None
    assert finding.rule_id == "WP.UPLOAD.EXECUTABLE"
    assert finding.severity is Severity.HIGH  # forte violação, não "malware"
    assert finding.artifact_ref == artifact.id


def test_fora_de_uploads_e_allowlist_nao_acusam(tmp_path) -> None:
    plugin = _artifact(tmp_path, "wp-content/plugins/ok/ok.php")
    assert (
        check_uploads_executable(
            plugin, classify(plugin.path.relative), b"<?php // legitimo", evidence_refs=("ev_1",)
        )
        is None
    )  # plugin legítimo: PHP esperado aqui

    uploads = _artifact(tmp_path, "wp-content/uploads/2026/evil.php")
    assert (
        check_uploads_executable(
            uploads,
            classify(uploads.path.relative),
            b"\xff\xd8\xff\xe0foto",
            evidence_refs=("ev_1",),
        )
        is None
    )  # jpeg: conteúdo inerte

    assert (
        check_uploads_executable(
            uploads,
            classify(uploads.path.relative),
            b"<?php // excecao",
            evidence_refs=("ev_1",),
            allowlist=("wp-content/uploads/2026/*",),
        )
        is None
    )  # exceção do operador


def test_fixtures_uploads_php() -> None:
    from pathlib import Path

    from wirs.domain import SafePath

    root = Path(__file__).parents[1] / "fixtures" / "wordpress" / "uploads_php"

    def verdict(relative: str):
        full = root / relative
        head = full.open("rb").read(8192)
        artifact = Artifact(kind=ArtifactKind.FILE, path=SafePath(root, relative))
        return check_uploads_executable(
            artifact, classify(relative), head, evidence_refs=("ev_fixture",)
        )

    assert verdict("wp-content/uploads/2026/evil.php") is not None  # positivo
    assert verdict("wp-content/uploads/foto.jpg") is None  # jpeg inerte
    assert verdict("wp-content/plugins/ok/ok.php") is None  # plugin legítimo
