"""ScanOrchestrator v0 (WIRS-116): inventory → discovery → zones → coverage."""

from __future__ import annotations

from wirs.application.orchestrator import run_scan
from wirs.domain import Artifact, LocalDirectoryTarget
from wirs.infrastructure import LocalArtifactSource


def _fixture(tmp_path) -> LocalDirectoryTarget:
    (tmp_path / "index.php").write_bytes(b"<?php // oi")
    sub = tmp_path / "wp-content"
    sub.mkdir()
    (sub / "a.txt").write_bytes(b"a")
    return LocalDirectoryTarget(tmp_path)


def test_pipeline_base(tmp_path) -> None:
    target = _fixture(tmp_path)

    result = run_scan(target, profile="soft", source=LocalArtifactSource(), adapters=[])

    arts = [i for i in result.artifacts if isinstance(i, Artifact)]
    assert len(arts) == 4  # root + 2 arquivos + 1 diretório
    assert result.gaps == 0
    assert result.coverage[0].state.value == "complete"
    assert result.profile == "soft"


def test_deterministico(tmp_path) -> None:
    target = _fixture(tmp_path)
    kwargs = {"profile": "soft", "source": LocalArtifactSource(), "adapters": []}

    a = run_scan(target, **kwargs)
    b = run_scan(target, **kwargs)

    assert [x.id for x in a.artifacts] == [x.id for x in b.artifacts]
    assert a.scan_id != b.scan_id  # cada execução é um evento distinto


def test_gap_vira_partial(tmp_path, monkeypatch) -> None:
    import os

    (tmp_path / "ok.txt").write_bytes(b"ok")
    (tmp_path / "bloq").mkdir()

    real_scandir = os.scandir

    def scandir_com_falha(path, *a, **k):
        if os.path.basename(os.fspath(path)) == "bloq":
            raise PermissionError("EACCES simulado")
        return real_scandir(path, *a, **k)

    monkeypatch.setattr(os, "scandir", scandir_com_falha)
    result = run_scan(
        LocalDirectoryTarget(tmp_path), profile="soft", source=LocalArtifactSource(), adapters=[]
    )

    assert result.gaps == 1
    assert result.coverage[0].state.value == "partial"
    assert result.coverage[0].failed == 1


def test_discovery_e_zones_wordpress(tmp_path) -> None:
    from wirs.adapters.wordpress.discovery import WordPressAdapter

    (tmp_path / "wp-includes").mkdir()
    (tmp_path / "wp-includes" / "version.php").write_bytes(b"v")
    (tmp_path / "wp-admin").mkdir()
    (tmp_path / "wp-content" / "uploads").mkdir(parents=True)
    (tmp_path / "wp-content" / "uploads" / "x.jpg").write_bytes(b"img")

    result = run_scan(
        LocalDirectoryTarget(tmp_path),
        profile="soft",
        source=LocalArtifactSource(),
        adapters=[WordPressAdapter()],
    )

    assert result.discovery is not None and result.discovery.platform_id == "wordpress"
    por_rel = {a.path.relative: a.id for a in result.artifacts}
    assert result.zones[por_rel["wp-includes/version.php"]] == "wp-core-protected"
    assert result.zones[por_rel["wp-content/uploads/x.jpg"]] == "wp-content-uploads"
