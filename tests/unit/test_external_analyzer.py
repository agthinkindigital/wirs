"""ExternalAnalyzer contract (WIRS-080)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from wirs.domain import Artifact, ArtifactKind, LocalDirectoryTarget, SafePath
from wirs.ports.analysis import (
    AnalysisAvailability,
    AnalyzerResult,
    ExternalAnalyzer,
    ProviderFinding,
)


class _Fake:
    id = "fake-analyzer"
    platforms: tuple[str, ...] = ()
    capabilities = frozenset({"signature_scan"})

    def __init__(self, disponivel: bool = True) -> None:
        self._disponivel = disponivel

    def available(self) -> AnalysisAvailability:
        if self._disponivel:
            return AnalysisAvailability(available=True, version="0.0-test")
        return AnalysisAvailability(available=False, reason="binário ausente (teste)")

    def scan(self, artifacts: Sequence[Artifact], *, timeout_s: float = 60.0) -> AnalyzerResult:
        assert isinstance(self, ExternalAnalyzer)
        return AnalyzerResult(
            provider_id=self.id,
            provider_version="0.0-test",
            findings=(
                ProviderFinding(
                    provider_id=self.id,
                    external_rule_id="T100",
                    severity="high",
                    artifact_ref="a.php",
                ),
            ),
        )


def _artifact(tmp_path: Path) -> Artifact:
    root = LocalDirectoryTarget(tmp_path).root
    return Artifact(kind=ArtifactKind.FILE, path=SafePath(root, "a.php"))


def test_contrato_com_fake_conforme(tmp_path: Path) -> None:
    fake = _Fake()
    assert "signature_scan" in fake.capabilities
    disp = fake.available()
    assert disp.available and disp.version == "0.0-test"

    resultado = fake.scan([_artifact(tmp_path)])

    assert resultado.provider_id == "fake-analyzer"
    (achado,) = resultado.findings
    assert achado.external_rule_id == "T100"
    assert achado.severity == "high"


def test_indisponivel_traz_motivo_e_normalizacao_sem_vendor() -> None:
    fake = _Fake(disponivel=False)
    disp = fake.available()

    assert not disp.available
    assert "ausente" in disp.reason

    normalizado = ProviderFinding(
        provider_id="yara",
        external_rule_id="PHP_WEBSHELL",
        severity="high",
        artifact_ref="evil.php",
        attributes={"tags": ["webshell"], "namespace": "builtin"},
    )
    assert normalizado.attributes["namespace"] == "builtin"
    assert "yara" not in normalizado.attributes  # vendor só no provider_id
