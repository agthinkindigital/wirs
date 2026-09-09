"""ScanOrchestrator v0: inventory → discovery → zones → coverage (WIRS-116).

Só conhece domain + ports. Implementações concretas (filesystem, adapters)
entram por parâmetro, montadas no CLI (composition root). Sem detectores
ainda — findings chegam na WIRS-117.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from wirs.domain import Artifact, CoverageEntry, CoverageState, Finding, Target
from wirs.ports import PlatformAdapter, PlatformDiscovery
from wirs.ports.source import ArtifactSource


@dataclass(frozen=True)
class ScanResult:
    scan_id: str
    target_root: str
    profile: str
    artifacts: tuple[Artifact, ...]
    gaps: int
    discovery: PlatformDiscovery | None
    zones: Mapping[str, str]
    coverage: tuple[CoverageEntry, ...]
    findings: tuple[Finding, ...] = ()


def run_scan(
    target: Target,
    *,
    profile: str,
    source: ArtifactSource,
    adapters: Sequence[PlatformAdapter],
    scan_id: str | None = None,
) -> ScanResult:
    artifacts: list[Artifact] = []
    gaps = 0
    for item in source.iter_artifacts(target):
        if isinstance(item, Artifact):
            artifacts.append(item)
        else:
            gaps += 1

    found: PlatformDiscovery | None = None
    for adapter in adapters:
        found = adapter.discover(target)
        if found is not None:
            break

    zones: dict[str, str] = {}
    if found is not None:
        adapter = next(a for a in adapters if a.id == found.platform_id)
        for artifact in artifacts:
            zones[artifact.id] = adapter.classify(artifact.path.relative)

    verified = len(artifacts)
    coverage = CoverageEntry(
        capability="filesystem",
        state=CoverageState.PARTIAL if gaps else CoverageState.COMPLETE,
        applicable_checks=verified + gaps,
        verified=verified,
        failed=gaps,
    )
    return ScanResult(
        scan_id=scan_id or f"scan_{uuid.uuid4().hex[:12]}",
        target_root=str(target.root),
        profile=profile,
        artifacts=tuple(artifacts),
        gaps=gaps,
        discovery=found,
        zones=MappingProxyType(zones),
        coverage=(coverage,),
    )
