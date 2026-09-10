"""ScanOrchestrator v0 (WIRS-116): inventory → discovery → zones → coverage."""

from __future__ import annotations

from wirs.application.orchestrator import run_scan
from wirs.domain import Artifact, LocalDirectoryTarget
from wirs.infrastructure import ArtifactReader, LocalArtifactSource, ReadBudget


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


def _mini_wp(tmp_path) -> LocalDirectoryTarget:
    (tmp_path / "wp-includes").mkdir()
    (tmp_path / "wp-includes" / "version.php").write_bytes(b"<?php // v")
    (tmp_path / "wp-admin").mkdir()
    up = tmp_path / "wp-content" / "uploads"
    up.mkdir(parents=True)
    (up / "evil.php").write_bytes(b"<?php // in" + b"erte")
    return LocalDirectoryTarget(tmp_path)


def test_detection_policy_com_evidence(tmp_path) -> None:
    from wirs.adapters.wordpress.discovery import WordPressAdapter
    from wirs.adapters.wordpress.policies import UploadsExecutablePolicy

    target = _mini_wp(tmp_path)
    result = run_scan(
        target,
        profile="soft",
        source=LocalArtifactSource(),
        adapters=[WordPressAdapter()],
        reader=ArtifactReader(),
        budget=ReadBudget(max_bytes=1 << 20),
        detectors=[UploadsExecutablePolicy()],
    )

    rules = [f.rule_id for f in result.findings]
    assert "WP.UPLOAD.EXECUTABLE" in rules
    finding = next(f for f in result.findings if f.rule_id == "WP.UPLOAD.EXECUTABLE")
    assert finding.severity.value == "high"
    ev_ids = {e.id for e in result.evidence}
    assert set(finding.evidence_refs) <= ev_ids  # toda ref resolve nesta run


def test_ioc_e_heuristicas_agregados(tmp_path) -> None:
    from wirs.detectors.builtin import IocDetector, PhpHeuristicsDetector
    from wirs.domain import IOC, IOCKind

    (tmp_path / "t.php").write_bytes(
        b"<?php as" + b"sert(" + b"ba" + b"se64_decode(" + b"ZZZ)); // MARKER123"
    )
    target = LocalDirectoryTarget(tmp_path)
    ioc = IOC(kind=IOCKind.LITERAL, value="MARKER123")

    result = run_scan(
        target,
        profile="soft",
        source=LocalArtifactSource(),
        adapters=[],
        reader=ArtifactReader(),
        budget=ReadBudget(max_bytes=1 << 20),
        detectors=[IocDetector([ioc]), PhpHeuristicsDetector()],
    )

    rules = {f.rule_id for f in result.findings}
    assert rules == {"IOC.MATCH", "PHP.HEUR.CHAIN"}
    ioc_finding = next(f for f in result.findings if f.rule_id == "IOC.MATCH")
    assert ioc_finding.severity.value == "medium"
    assert ioc_finding.attributes["match_count"] == 1
    ev_ids = {e.id for e in result.evidence}
    assert all(set(f.evidence_refs) <= ev_ids for f in result.findings)


def test_checksum_ausente_degrada_e_scan_continua(tmp_path) -> None:
    from wirs.domain import ProviderUnavailable
    from wirs.ports.checksum import IntegrityProvider

    (tmp_path / "a.txt").write_bytes(b"a")

    class DeadProvider:
        id = "wp-cli-core-checksum"
        platforms = ()

        def verify(self, target):
            raise ProviderUnavailable("sem wp aqui")

    assert isinstance(DeadProvider(), IntegrityProvider)

    result = run_scan(
        LocalDirectoryTarget(tmp_path),
        profile="soft",
        source=LocalArtifactSource(),
        adapters=[],
        integrity=[DeadProvider()],
    )

    assert result.findings == ()
    (fs, ck) = result.coverage
    assert fs.state.value == "complete"
    assert ck.capability == "wp-cli-core-checksum" and ck.state.value == "unavailable"


def test_sem_stream_sem_segunda_leitura(tmp_path) -> None:
    from wirs.detectors.builtin import IocDetector, PhpHeuristicsDetector
    from wirs.domain import IOC, IOCKind

    (tmp_path / "a.txt").write_bytes(b"hello world")
    target = LocalDirectoryTarget(tmp_path)
    leituras = 0
    base = ArtifactReader()

    class SpyReader(ArtifactReader):
        def iter_chunks(self, artifact, budget, *, should_stop=None):
            nonlocal leituras
            leituras += 1
            yield from base.iter_chunks(artifact, budget, should_stop=should_stop)

    run_scan(
        target,
        profile="soft",
        source=LocalArtifactSource(),
        adapters=[],
        reader=SpyReader(),
        budget=ReadBudget(max_bytes=1 << 20),
        detectors=[PhpHeuristicsDetector()],
    )
    assert leituras == 1  # só o head; stream completo só com IOC

    leituras = 0
    run_scan(
        target,
        profile="soft",
        source=LocalArtifactSource(),
        adapters=[],
        reader=SpyReader(),
        budget=ReadBudget(max_bytes=1 << 20),
        detectors=[IocDetector([IOC(kind=IOCKind.LITERAL, value="zzz")])],
    )
    assert leituras == 2  # head + stream do IOC


def test_verificado_por_baseline_suprime_heuristicas(tmp_path) -> None:
    from wirs.adapters.wordpress.policies import UploadsExecutablePolicy
    from wirs.detectors.builtin import PhpHeuristicsDetector
    from wirs.ports.checksum import ComponentIntegrity

    (tmp_path / "wp-includes").mkdir()
    (tmp_path / "wp-includes" / "ok.php").write_bytes(b"<?php system($x);")

    class CoreOk:
        id = "fake-baseline"
        platforms = ()

        def verify(self, target):
            return [
                ComponentIntegrity(
                    provider_id="fake-baseline",
                    provider_version="1",
                    component="wordpress-core",
                    covers=("wp-includes/"),
                )
            ]

    result = run_scan(
        LocalDirectoryTarget(tmp_path),
        profile="soft",
        source=LocalArtifactSource(),
        adapters=[],
        reader=ArtifactReader(),
        budget=ReadBudget(max_bytes=1 << 20),
        detectors=[PhpHeuristicsDetector(), UploadsExecutablePolicy()],
        integrity=[CoreOk()],
    )

    assert result.findings == ()  # baseline confiável absolveu
    (fs,) = [c for c in result.coverage if c.capability == "filesystem"]
    assert "1 suprimido" in fs.note


def test_divergente_continua_escrutinado(tmp_path) -> None:
    from wirs.adapters.wordpress.policies import UploadsExecutablePolicy
    from wirs.detectors.builtin import PhpHeuristicsDetector
    from wirs.domain import FileIntegrity, IntegrityState
    from wirs.ports.checksum import ComponentIntegrity

    (tmp_path / "wp-includes").mkdir()
    (tmp_path / "wp-includes" / "ok.php").write_bytes(b"<?php // limpo")
    (tmp_path / "wp-includes" / "bad.php").write_bytes(b"<?php system($x);")

    class CoreParcial:
        id = "fake-baseline"
        platforms = ()

        def verify(self, target):
            return [
                ComponentIntegrity(
                    provider_id="fake-baseline",
                    provider_version="1",
                    component="wordpress-core",
                    files=(
                        FileIntegrity(path="wp-includes/bad.php", state=IntegrityState.MISMATCH),
                    ),
                    covers=("wp-includes/",),
                )
            ]

    result = run_scan(
        LocalDirectoryTarget(tmp_path),
        profile="soft",
        source=LocalArtifactSource(),
        adapters=[],
        reader=ArtifactReader(),
        budget=ReadBudget(max_bytes=1 << 20),
        detectors=[PhpHeuristicsDetector(), UploadsExecutablePolicy()],
        integrity=[CoreParcial()],
    )

    rules = {f.rule_id for f in result.findings}
    assert "WP.CORE.HASH_MISMATCH" in rules  # integridade viu
    assert "PHP.HEUR.SINGLE" in rules  # heurística no divergente (DX001 precisa dos dois)
    refs = {
        a.path.relative
        for a in result.artifacts
        for f in result.findings
        if f.artifact_ref == a.id and f.rule_id.startswith("PHP.")
    }
    assert refs == {"wp-includes/bad.php"}  # ok.php absolvido, sem heurística
