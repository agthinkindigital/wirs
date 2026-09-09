"""Seam de detector interno: propõe findings, orquestrador cunha evidências.

O detector nunca toca disco nem rede: recebe bytes prontos e devolve propostas
sem `evidence_refs` (o orquestrador cunha a Evidence e anexa a ref). Isso mantém
a invariante 2 sem o detector conhecer scan_id ou provenance.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable

from wirs.domain import Artifact, Confidence, Severity


@dataclass(frozen=True)
class ProposedFinding:
    rule_id: str
    title: str
    category: str
    severity: Severity
    confidence: Confidence
    evidence_kind: str
    evidence_content: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    attributes: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@runtime_checkable
class Detector(Protocol):
    id: str
    wants_stream: bool

    def analyze(
        self, artifact: Artifact, zone: str | None, head: bytes, chunks: Sequence[bytes]
    ) -> Sequence[ProposedFinding]: ...
