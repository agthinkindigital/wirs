"""ScanOrchestrator v1: inventory → discovery → zones → detection → coverage (WIRS-117).

Só conhece domain + ports. Leitores, adapters, detectores e providers de
integridade entram por parâmetro, montados no CLI (composition root). Cada
proposta vira Evidence cunhada aqui antes do Finding (invariante 2); contextos
passam por redaction.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from wirs import __version__ as scanner_version
from wirs.domain import (
    Artifact,
    ArtifactKind,
    BaselineTrust,
    Confidence,
    ConfidenceClass,
    CoverageEntry,
    CoverageState,
    Evidence,
    Finding,
    IntegrityState,
    Provenance,
    Severity,
    Target,
    redact_text,
)
from wirs.domain.errors import BudgetExceeded, ProviderError, ProviderUnavailable
from wirs.ports import PlatformAdapter, PlatformDiscovery
from wirs.ports.checksum import IntegrityProvider
from wirs.ports.detection import Detector
from wirs.ports.reader import ArtifactReader, ReadBudget
from wirs.ports.source import ArtifactSource

INTERNAL_PROVENANCE = Provenance(collector="wirs-internal", version=scanner_version)
HEAD_BYTES = 65536

_SEVERITY_BY_STATE = {
    IntegrityState.MISMATCH: (Severity.CRITICAL, "HASH_MISMATCH"),
    IntegrityState.MISSING: (Severity.HIGH, "FILE_MISSING"),
    IntegrityState.UNEXPECTED: (Severity.MEDIUM, "UNEXPECTED_FILE"),
}

# WIRS-044: linguagem de diff (referência fraca), nunca de violação confiável.
_REFERENCE_SUFFIX = {
    IntegrityState.MISMATCH: "REFERENCE_DIFF",
    IntegrityState.MISSING: "REFERENCE_MISSING",
    IntegrityState.UNEXPECTED: "REFERENCE_UNEXPECTED",
}


@dataclass(frozen=True)
class ProgressEvent:
    """Fato de progresso (WIRS-139): fase, posição, total, detalhe sanitizável.

    Fases: inventory → discovery → integrity → detect (por arquivo) → done.
    Sem segredo: detail carrega path relativo (a CLI neutraliza ao exibir).
    """

    phase: str
    current: int = 0
    total: int = 0
    detail: str = ""


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
    evidence: tuple[Evidence, ...] = ()


def _read_head(reader: ArtifactReader, artifact: Artifact, budget: ReadBudget, limit: int) -> bytes:
    parts: list[bytes] = []
    taken = 0
    stream = reader.iter_chunks(artifact, budget)
    try:
        for chunk in stream:
            need = limit - taken
            if need <= 0:
                break
            parts.append(chunk[:need])
            taken += len(parts[-1])
    finally:
        stream.close()
    return b"".join(parts)


def _detect_file(
    scan_id: str,
    artifact: Artifact,
    zone_value: str | None,
    head: bytes,
    chunks: Sequence[bytes],
    detectors: Sequence[Detector],
) -> tuple[list[Evidence], list[Finding]]:
    evidences: list[Evidence] = []
    findings: list[Finding] = []
    for detector in detectors:
        for proposed in detector.analyze(artifact, zone_value, head, chunks):
            content = dict(proposed.evidence_content)
            if "contexts" in content:
                content["contexts"] = [
                    redact_text(
                        c.decode("utf-8", errors="replace") if isinstance(c, bytes) else str(c)
                    )[:512]
                    for c in content["contexts"]
                ]
            ev = Evidence(
                scan_id=scan_id,
                kind=proposed.evidence_kind,
                source="wirs-internal",
                artifact_ref=artifact.id,
                content=content,
                provenance=INTERNAL_PROVENANCE,
            )
            evidences.append(ev)
            findings.append(
                Finding(
                    rule_id=proposed.rule_id,
                    title=proposed.title,
                    category=proposed.category,
                    severity=proposed.severity,
                    confidence=proposed.confidence,
                    artifact_ref=artifact.id,
                    evidence_refs=(ev.id,),
                    attributes=proposed.attributes,
                )
            )
    return evidences, findings


def _covered(relative: str, prefixes: tuple[str, ...]) -> bool:
    return any(relative == p.rstrip("/") or relative.startswith(p) for p in prefixes)


def _integrity_phase(
    target: Target, platform_id: str | None, providers: Sequence[IntegrityProvider]
) -> tuple[list[Finding], list[CoverageEntry], tuple[str, ...], tuple[str, ...]]:
    findings: list[Finding] = []
    coverage: list[CoverageEntry] = []
    covered: list[str] = []
    diverged: list[str] = []
    for provider in providers:
        if provider.platforms and platform_id not in provider.platforms:
            continue
        try:
            components = provider.verify(target)
        except ProviderError as e:
            state = (
                CoverageState.UNAVAILABLE
                if isinstance(e, ProviderUnavailable)
                else CoverageState.FAILED
            )
            coverage.append(CoverageEntry(capability=provider.id, state=state, note=str(e)[:200]))
            continue
        for component in components:
            covered.extend(component.covers)
            if component.unverified:
                coverage.append(
                    CoverageEntry(
                        capability=f"baseline:{component.component}",
                        state=CoverageState.PARTIAL,
                        applicable_checks=1,
                        unavailable=1,
                        note="sem baseline oficial",
                    )
                )
                continue
            prefix = "WP.CORE" if component.component == "wordpress-core" else "WP.PLUGIN"
            reference = component.trust is BaselineTrust.UNVERIFIED_REFERENCE
            for item in component.files:
                severity, suffix = _SEVERITY_BY_STATE[item.state]
                confidence = ConfidenceClass.DETERMINISTIC
                state_label = item.state.value
                if reference:
                    # WIRS-044: diff contra referência fraca, nunca "violação confiável".
                    suffix = _REFERENCE_SUFFIX[item.state]
                    confidence = ConfidenceClass.HIGH
                    state_label = f"reference-{item.state.value}"
                findings.append(
                    Finding(
                        rule_id=f"{prefix}.{suffix}",
                        title=f"{component.component}: {item.path} ({state_label})",
                        category="integrity",
                        severity=severity,
                        confidence=Confidence(confidence),
                        artifact_ref=item.path,
                        evidence_refs=(),
                        provenance=Provenance(
                            component.provider_id, component.provider_version or "unknown"
                        ),
                        attributes={
                            "component": component.component,
                            "path": item.path,
                            "note": item.note,
                            "trust": (component.trust.value if component.trust else "unknown"),
                        },
                    )
                )
    diverged = [f.attributes["path"] for f in findings if "path" in f.attributes]
    return findings, coverage, tuple(covered), tuple(diverged)


def run_scan(
    target: Target,
    *,
    profile: str,
    source: ArtifactSource,
    adapters: Sequence[PlatformAdapter],
    scan_id: str | None = None,
    reader: ArtifactReader | None = None,
    budget: ReadBudget | None = None,
    detectors: Sequence[Detector] = (),
    integrity: Sequence[IntegrityProvider] = (),
    head_bytes: int = HEAD_BYTES,
    on_event: Callable[[ProgressEvent], None] | None = None,
) -> ScanResult:
    sid = scan_id or f"scan_{uuid.uuid4().hex[:12]}"
    emit = on_event or (lambda _e: None)
    artifacts: list[Artifact] = []
    gaps = 0
    for item in source.iter_artifacts(target):
        if isinstance(item, Artifact):
            artifacts.append(item)
        else:
            gaps += 1
    emit(ProgressEvent(phase="inventory", current=len(artifacts), total=len(artifacts) + gaps))

    found: PlatformDiscovery | None = None
    for adapter in adapters:
        found = adapter.discover(target)
        if found is not None:
            break
    emit(ProgressEvent(phase="discovery", detail=found.platform_id if found else "generic"))

    zones: dict[str, str] = {}
    if found is not None:
        adapter = next(a for a in adapters if a.id == found.platform_id)
        for artifact in artifacts:
            zones[artifact.id] = adapter.classify(artifact.path.relative)

    # Integridade ANTES da detecção: baseline confiável absolve (WIRS-053).
    # Divergentes continuam escaneados (correlação DX001 precisa dos dois lados).
    ck_findings, ck_coverage, covered, diverged = _integrity_phase(
        target, found.platform_id if found else None, integrity
    )
    emit(ProgressEvent(phase="integrity", current=len(ck_coverage), total=len(integrity)))
    all_evidence: list[Evidence] = []
    all_findings: list[Finding] = list(ck_findings)
    suppressed = 0
    want_stream = any(d.wants_stream for d in detectors)
    files = [a for a in artifacts if a.kind is ArtifactKind.FILE]
    if reader is not None and budget is not None and detectors:
        for index, artifact in enumerate(files, 1):
            emit(
                ProgressEvent(
                    phase="detect", current=index, total=len(files), detail=artifact.path.relative
                )
            )
            if _covered(artifact.path.relative, covered) and artifact.path.relative not in diverged:
                suppressed += 1
                continue
            try:
                head = _read_head(reader, artifact, budget, head_bytes)
                chunks: list[bytes] = []
                if want_stream:
                    stream = reader.iter_chunks(artifact, budget)
                    try:
                        chunks = list(stream)
                    finally:
                        stream.close()
                evs, fnds = _detect_file(
                    sid, artifact, zones.get(artifact.id), head, chunks, detectors
                )
                all_evidence.extend(evs)
                all_findings.extend(fnds)
            except (OSError, BudgetExceeded):
                gaps += 1

    verified = len(artifacts)
    fs_note = f"{suppressed} suprimido(s) por baseline confiável" if suppressed else ""
    coverage = (
        CoverageEntry(
            capability="filesystem",
            state=CoverageState.PARTIAL if gaps else CoverageState.COMPLETE,
            applicable_checks=verified + gaps,
            verified=verified,
            failed=gaps,
            note=fs_note,
        ),
        *ck_coverage,
    )
    emit(ProgressEvent(phase="done", current=len(all_findings), total=len(files)))
    return ScanResult(
        scan_id=sid,
        target_root=str(target.root),
        profile=profile,
        artifacts=tuple(artifacts),
        gaps=gaps,
        discovery=found,
        zones=MappingProxyType(zones),
        coverage=coverage,
        findings=tuple(all_findings),
        evidence=tuple(all_evidence),
    )
