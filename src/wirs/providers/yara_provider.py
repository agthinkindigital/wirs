"""YARA como analyzer opcional (WIRS-081).

Contrato em docs/providers/yara-python.md. A lib é opcional: ausente vira
UNAVAILABLE (nunca abort). Match só sobre bytes lidos pelo ArtifactReader
(`data=`); compile lazy no primeiro scan; timeout sempre configurado.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from wirs.domain import Artifact, ArtifactKind
from wirs.domain.errors import BudgetExceeded, ProviderInvalidOutput, ProviderUnavailable
from wirs.infrastructure.reader import ArtifactReader, ReadBudget
from wirs.ports.analysis import (
    AnalysisAvailability,
    AnalyzerResult,
    ProviderFinding,
)

try:  # dependência opcional (pip install wirs[yara])
    import yara as _yara
except ImportError:  # pragma: no cover - caminho real exige a lib
    _yara = None

PROVIDER_ID = "yara"
_SEVERIDADES = ("info", "low", "medium", "high", "critical")


class YaraAnalyzer:
    """Adapter yara-python → seam ExternalAnalyzer."""

    id = PROVIDER_ID
    platforms: tuple[str, ...] = ()
    capabilities = frozenset({"signature_scan"})

    def __init__(
        self,
        rules_source: str,
        *,
        reader: ArtifactReader | None = None,
        budget: ReadBudget | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        self._source = rules_source
        self._reader = reader or ArtifactReader()
        self._budget = budget or ReadBudget(max_bytes=64 << 20)
        self._timeout_s = timeout_s
        self._rules = None

    @classmethod
    def from_pack(
        cls,
        pack: Path,
        *,
        experimental: bool = False,
        reader: ArtifactReader | None = None,
        budget: ReadBudget | None = None,
        timeout_s: float = 60.0,
    ) -> YaraAnalyzer:
        """Monta analyzer do diretório de regras (.yar/.yara, ordenado).

        `experimental/` entra só com experimental=True. Regras são concatenadas
        numa única fonte (mesmo resultado de compilar arquivo a arquivo).
        """
        pack = Path(pack)
        dirs = sorted(
            d for d in pack.iterdir() if d.is_dir() and (experimental or d.name != "experimental")
        )
        fontes: list[str] = []
        for directory in dirs:
            for rule_file in sorted(directory.glob("*.yar")) + sorted(directory.glob("*.yara")):
                try:
                    fontes.append(rule_file.read_text(encoding="utf-8"))
                except OSError as e:
                    raise ProviderInvalidOutput(f"regra ilegível: {rule_file} ({e})") from e
        if not fontes:
            raise ProviderInvalidOutput(f"pack sem regras: {pack}")
        return cls("\n".join(fontes), reader=reader, budget=budget, timeout_s=timeout_s)

    def available(self) -> AnalysisAvailability:
        if _yara is None:
            return AnalysisAvailability(
                available=False, reason="yara-python ausente: pip install wirs[yara]"
            )
        return AnalysisAvailability(available=True, version=getattr(_yara, "__version__", None))

    def _compiled(self) -> Any:
        if _yara is None:  # pragma: no cover - scan() já barra sem lib
            raise ProviderUnavailable("yara-python ausente: pip install wirs[yara]")
        if self._rules is None:
            try:
                self._rules = _yara.compile(source=self._source, error_on_warning=True)
            except _yara.SyntaxError as e:
                raise ProviderInvalidOutput(f"rule pack não compila: {e}") from e
            except _yara.Error as e:
                raise ProviderInvalidOutput(f"erro YARA ao compilar: {e}") from e
        return self._rules

    def scan(
        self, artifacts: Sequence[Artifact], *, timeout_s: float | None = None
    ) -> AnalyzerResult:
        if _yara is None:
            raise ProviderUnavailable("yara-python ausente: pip install wirs[yara]")
        rules = self._compiled()
        limite = self._timeout_s if timeout_s is None else timeout_s
        achados: list[ProviderFinding] = []
        for artifact in artifacts:
            if artifact.kind is not ArtifactKind.FILE:
                continue
            try:
                content = b"".join(self._reader.iter_chunks(artifact, self._budget))
            except (OSError, BudgetExceeded):
                continue
            try:
                matches = rules.match(data=content, timeout=limite)
            except _yara.TimeoutError:
                continue
            except _yara.Error:
                continue
            for match in matches:
                meta = getattr(match, "meta", {}) or {}
                severity = str(meta.get("severity", "medium")).lower()
                achados.append(
                    ProviderFinding(
                        provider_id=PROVIDER_ID,
                        external_rule_id=str(match.rule),
                        severity=severity if severity in _SEVERIDADES else "medium",
                        artifact_ref=artifact.path.relative,
                        attributes={
                            "tags": list(getattr(match, "tags", [])),
                            "namespace": str(getattr(match, "namespace", "")),
                        },
                    )
                )
        return AnalyzerResult(
            provider_id=PROVIDER_ID,
            provider_version=getattr(_yara, "__version__", None),
            findings=tuple(achados),
        )
