"""Seam de analyzers externos (ex.: YARA, Wordfence CLI).

O analyzer nunca toca disco nem rede diretamente: recebe Artifacts (lidos pelo
ArtifactReader do scan) e devolve achados normalizados. Nenhum campo de vendor
atravessa para o application (anti-corruption).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable

from wirs.domain import Artifact


@dataclass(frozen=True)
class AnalysisAvailability:
    available: bool
    version: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class ProviderFinding:
    provider_id: str
    external_rule_id: str
    severity: str
    artifact_ref: str
    evidence_kind: str = "external_match"
    evidence_content: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    attributes: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True)
class AnalyzerResult:
    provider_id: str
    provider_version: str | None
    findings: tuple[ProviderFinding, ...] = ()


@runtime_checkable
class ExternalAnalyzer(Protocol):
    id: str
    # Plataformas atendidas; vazio = qualquer uma.
    platforms: tuple[str, ...]
    # Capabilities declaradas (ex.: {"signature_scan"}).
    capabilities: frozenset[str]

    def available(self) -> AnalysisAvailability: ...
    def scan(self, artifacts: Sequence[Artifact], *, timeout_s: float = 60.0) -> AnalyzerResult: ...
