"""Integração do analyzer externo YARA ao scan (WIRS-086)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wirs.application.orchestrator import run_scan
from wirs.cli.app import app
from wirs.domain import LocalDirectoryTarget, ProviderInvalidOutput
from wirs.infrastructure import ArtifactReader, LocalArtifactSource, ReadBudget
from wirs.ports.analysis import (
    AnalysisAvailability,
    AnalyzerFailure,
    AnalyzerResult,
    ProviderFinding,
)


class _Analyzer:
    id = "yara"
    platforms: tuple[str, ...] = ()
    capabilities = frozenset({"signature_scan"})

    def __init__(self, result: AnalyzerResult | None = None, available: bool = True) -> None:
        self._result = result
        self._is_available = available

    def available(self) -> AnalysisAvailability:
        return AnalysisAvailability(
            available=self._is_available,
            version="4.5.4" if self._is_available else None,
            reason="yara-python ausente" if not self._is_available else "",
        )

    def scan(self, artifacts, *, timeout_s: float = 60.0) -> AnalyzerResult:
        if self._result is None:
            raise AssertionError("resultado de teste não configurado")
        return self._result


def _target(tmp_path: Path) -> LocalDirectoryTarget:
    (tmp_path / "evil.php").write_bytes(b"<?php eval(base64_decode($x));")
    (tmp_path / "clean.txt").write_bytes(b"texto limpo")
    return LocalDirectoryTarget(tmp_path)


def _run(target: LocalDirectoryTarget, analyzer: _Analyzer):
    return run_scan(
        target,
        profile="soft",
        source=LocalArtifactSource(),
        adapters=[],
        reader=ArtifactReader(),
        budget=ReadBudget(max_bytes=1 << 20),
        analyzers=[analyzer],
    )


def test_analyzer_match_vira_finding_evidence_com_artifact_id(tmp_path: Path) -> None:
    target = _target(tmp_path)
    analyzer = _Analyzer(
        AnalyzerResult(
            provider_id="yara",
            provider_version="4.5.4",
            findings=(
                ProviderFinding(
                    provider_id="yara",
                    external_rule_id="WIRS_PHP_Webshell_EvalChain",
                    severity="high",
                    artifact_ref="evil.php",
                    attributes={"tags": ["webshell"], "namespace": "builtin"},
                ),
            ),
        )
    )

    result = _run(target, analyzer)

    (finding,) = result.findings
    artifact_ids = {artifact.id for artifact in result.artifacts}
    assert finding.rule_id == "YARA.WIRS_PHP_Webshell_EvalChain"
    assert finding.artifact_ref in artifact_ids
    assert finding.attributes["tags"] == ["webshell"]
    assert finding.attributes["namespace"] == "builtin"
    assert finding.evidence_refs
    assert result.evidence[0].artifact_ref == finding.artifact_ref
    assert result.evidence[0].provenance.collector == "yara"
    assert result.coverage[-1].capability == "yara"
    assert result.coverage[-1].state.value == "complete"
    assert result.provider_runs[-1].status.value == "completed"


def test_analyzer_ausente_registra_unavailable(tmp_path: Path) -> None:
    result = _run(_target(tmp_path), _Analyzer(available=False))

    coverage = next(item for item in result.coverage if item.capability == "yara")
    assert coverage.state.value == "unavailable"
    assert coverage.unavailable == 2
    assert result.provider_runs[-1].status.value == "unavailable"
    assert result.findings == ()


def test_falha_por_arquivo_vira_coverage_partial(tmp_path: Path) -> None:
    result = _run(
        _target(tmp_path),
        _Analyzer(
            AnalyzerResult(
                provider_id="yara",
                provider_version="4.5.4",
                failures=(
                    AnalyzerFailure(stage="match", reason="timeout", artifact_ref="evil.php"),
                ),
            )
        ),
    )

    coverage = next(item for item in result.coverage if item.capability == "yara")
    assert coverage.state.value == "partial"
    assert coverage.verified == 1
    assert coverage.failed == 1
    assert result.provider_runs[-1].status.value == "partial"


def test_falha_de_compile_vira_failed_e_scan_continua(tmp_path: Path) -> None:
    class _Invalid(_Analyzer):
        def scan(self, artifacts, *, timeout_s: float = 60.0) -> AnalyzerResult:
            raise ProviderInvalidOutput("rule pack inválido")

    result = _run(_target(tmp_path), _Invalid())

    coverage = next(item for item in result.coverage if item.capability == "yara")
    assert coverage.state.value == "failed"
    assert coverage.failed == 2
    assert result.provider_runs[-1].status.value == "failed"
    assert result.coverage[0].capability == "filesystem"


@pytest.mark.skipif(importlib.util.find_spec("yara") is None, reason="yara-python não instalado")
def test_scan_builtin_yara_gera_match_real(tmp_path: Path) -> None:
    alvo = tmp_path / "alvo"
    alvo.mkdir()
    (alvo / "evil.php").write_bytes(b"<?php eval(base64_decode($payload));")

    result = CliRunner().invoke(app, ["scan", str(alvo), "--format", "json"])

    assert result.exit_code == 1, result.output
    payload = json.loads(result.stdout)
    yara_findings = [item for item in payload["findings"] if item["rule_id"].startswith("YARA.")]
    assert [item["rule_id"] for item in yara_findings] == ["YARA.WIRS_PHP_Webshell_EvalChain"]
    assert yara_findings[0]["attributes"]["namespace"] == "default"
    yara_coverage = next(item for item in payload["coverage"] if item["capability"] == "yara")
    yara_run = next(item for item in payload["provider_runs"] if item["provider_id"] == "yara")
    assert yara_coverage["state"] == "complete"
    assert yara_run["status"] == "completed"


@pytest.mark.skipif(importlib.util.find_spec("yara") is None, reason="yara-python não instalado")
def test_scan_builtin_yara_negativo_real_nao_gera_finding(tmp_path: Path) -> None:
    alvo = tmp_path / "alvo"
    alvo.mkdir()
    (alvo / "clean.php").write_bytes(b"<?php echo 'clean';")

    result = CliRunner().invoke(app, ["scan", str(alvo), "--format", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert not [item for item in payload["findings"] if item["rule_id"].startswith("YARA.")]
    yara_coverage = next(item for item in payload["coverage"] if item["capability"] == "yara")
    assert yara_coverage["state"] == "complete"
