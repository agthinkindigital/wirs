"""Detectores internos prontos: adaptam funções puras para a seam Detector."""

from __future__ import annotations

from collections.abc import Sequence

from wirs.detectors.ioc_scanner import IocMatch, scan_stream
from wirs.detectors.php_heuristics import analyze_php
from wirs.domain import IOC, Artifact, Confidence, ConfidenceClass, Severity
from wirs.ports.detection import Detector, ProposedFinding


class IocDetector(Detector):
    """IOC literals em streaming (SHA256 vai para o HashService, no orquestrador)."""

    id = "ioc-scanner"
    wants_stream = True

    def __init__(self, iocs: Sequence[IOC], occurrence_cap: int = 100) -> None:
        self._iocs = tuple(iocs)
        self._cap = occurrence_cap

    def analyze(
        self, artifact: Artifact, zone: str | None, head: bytes, chunks: Sequence[bytes]
    ) -> Sequence[ProposedFinding]:
        if not self._iocs:
            return ()
        result = scan_stream(iter(chunks), self._iocs, occurrence_cap=self._cap)
        seen: dict[str, list[IocMatch]] = {}
        for match in result.matches:
            seen.setdefault(match.ioc_id, []).append(match)
        out: list[ProposedFinding] = []
        for ioc_id, matches in seen.items():
            ioc = next(i for i in self._iocs if i.id == ioc_id)
            out.append(
                ProposedFinding(
                    rule_id="IOC.MATCH",
                    title=f"Indicador conhecido: {ioc.label or ioc.value[:60]}",
                    category="ioc",
                    severity=Severity.MEDIUM,
                    confidence=Confidence(ConfidenceClass.MEDIUM),
                    evidence_kind="ioc_match",
                    evidence_content={
                        "ioc_id": ioc_id,
                        "kind": ioc.kind.value,
                        "match_count": result.total_counts[ioc_id],
                        "offsets": [m.offset for m in matches[:10]],
                        "contexts": [m.context for m in matches[:3]],
                    },
                    attributes={"ioc_id": ioc_id, "match_count": result.total_counts[ioc_id]},
                )
            )
        return out


class PhpHeuristicsDetector(Detector):
    """Heurísticas PHP sobre o head (bytes prontos, sem I/O)."""

    id = "php-heuristics"
    wants_stream = False

    def analyze(
        self, artifact: Artifact, zone: str | None, head: bytes, chunks: Sequence[bytes]
    ) -> Sequence[ProposedFinding]:
        return analyze_php(artifact, head)
