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
    ProviderRun,
    ProviderRunStatus,
    Severity,
    Target,
    redact_mapping,
    redact_text,
)
from wirs.domain.errors import BudgetExceeded, ProviderError, ProviderUnavailable
from wirs.ports import PlatformAdapter, PlatformDiscovery
from wirs.ports.analysis import AnalyzerResult, ExternalAnalyzer
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
    provider_runs: tuple[ProviderRun, ...] = ()


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
            atributos = dict(proposed.attributes)
            atributos.setdefault("path", artifact.path.relative)
            findings.append(
                Finding(
                    rule_id=proposed.rule_id,
                    title=proposed.title,
                    category=proposed.category,
                    severity=proposed.severity,
                    confidence=proposed.confidence,
                    artifact_ref=artifact.id,
                    evidence_refs=(ev.id,),
                    attributes=atributos,
                )
            )
    return evidences, findings


def _covered(relative: str, prefixes: tuple[str, ...]) -> bool:
    return any(relative == p.rstrip("/") or relative.startswith(p) for p in prefixes)


def _analysis_phase(
    scan_id: str,
    artifacts: Sequence[Artifact],
    analyzers: Sequence[ExternalAnalyzer],
    platform_id: str | None,
) -> tuple[list[Evidence], list[Finding], list[CoverageEntry], list[ProviderRun]]:
    evidences: list[Evidence] = []
    findings: list[Finding] = []
    coverage: list[CoverageEntry] = []
    provider_runs: list[ProviderRun] = []
    files = [artifact for artifact in artifacts if artifact.kind is ArtifactKind.FILE]
    by_ref = {(artifact.source_ref, artifact.path.relative): artifact for artifact in files}

    for analyzer in analyzers:
        capabilities = tuple(sorted(analyzer.capabilities))
        if analyzer.platforms and platform_id not in analyzer.platforms:
            coverage.append(
                CoverageEntry(
                    capability=analyzer.id,
                    state=CoverageState.UNAVAILABLE,
                    applicable_checks=len(files),
                    unavailable=len(files),
                    note="unsupported_platform",
                )
            )
            provider_runs.append(
                ProviderRun(
                    provider_id=analyzer.id,
                    status=ProviderRunStatus.UNAVAILABLE,
                    capabilities=capabilities,
                    reason="unsupported_platform",
                )
            )
            continue

        try:
            availability = analyzer.available()
        except ProviderError as error:
            reason = redact_text(str(error)[:200]) or "falha ao verificar disponibilidade"
            coverage.append(
                CoverageEntry(
                    capability=analyzer.id,
                    state=CoverageState.FAILED,
                    applicable_checks=len(files),
                    failed=len(files),
                    note=reason,
                )
            )
            provider_runs.append(
                ProviderRun(
                    provider_id=analyzer.id,
                    status=ProviderRunStatus.FAILED,
                    capabilities=capabilities,
                    reason=reason,
                )
            )
            continue

        if not availability.available:
            reason = redact_text(availability.reason[:200]) or "provider indisponível"
            coverage.append(
                CoverageEntry(
                    capability=analyzer.id,
                    state=CoverageState.UNAVAILABLE,
                    applicable_checks=len(files),
                    unavailable=len(files),
                    note=reason,
                )
            )
            provider_runs.append(
                ProviderRun(
                    provider_id=analyzer.id,
                    status=ProviderRunStatus.UNAVAILABLE,
                    version=availability.version,
                    capabilities=capabilities,
                    reason=reason,
                )
            )
            continue

        try:
            result: AnalyzerResult = analyzer.scan(files)
            if result.provider_id != analyzer.id:
                raise ValueError(
                    f"provider_id divergente: esperado {analyzer.id!r}, "
                    f"recebido {result.provider_id!r}"
                )
        except ProviderUnavailable as error:
            reason = redact_text(str(error)[:200]) or "provider indisponível"
            coverage.append(
                CoverageEntry(
                    capability=analyzer.id,
                    state=CoverageState.UNAVAILABLE,
                    applicable_checks=len(files),
                    unavailable=len(files),
                    note=reason,
                )
            )
            provider_runs.append(
                ProviderRun(
                    provider_id=analyzer.id,
                    status=ProviderRunStatus.UNAVAILABLE,
                    version=availability.version,
                    capabilities=capabilities,
                    reason=reason,
                )
            )
            continue
        except ProviderError as error:
            reason = redact_text(str(error)[:200]) or "falha no provider"
            coverage.append(
                CoverageEntry(
                    capability=analyzer.id,
                    state=CoverageState.FAILED,
                    applicable_checks=len(files),
                    failed=len(files),
                    note=reason,
                )
            )
            provider_runs.append(
                ProviderRun(
                    provider_id=analyzer.id,
                    status=ProviderRunStatus.FAILED,
                    version=availability.version,
                    capabilities=capabilities,
                    reason=reason,
                )
            )
            continue
        except ValueError as error:
            reason = redact_text(str(error)[:200]) or "output inválido do provider"
            coverage.append(
                CoverageEntry(
                    capability=analyzer.id,
                    state=CoverageState.FAILED,
                    applicable_checks=len(files),
                    failed=len(files),
                    note=reason,
                )
            )
            provider_runs.append(
                ProviderRun(
                    provider_id=analyzer.id,
                    status=ProviderRunStatus.FAILED,
                    version=availability.version,
                    capabilities=capabilities,
                    reason=reason,
                )
            )
            continue

        version = result.provider_version or availability.version or "unknown"
        failed_refs: set[str] = set()
        failure_notes: list[str] = []
        unknown_failure = False
        for failure in result.failures:
            reason = redact_text(failure.reason[:200]) or "falha sem motivo"
            failure_notes.append(f"{failure.stage}: {reason}")
            if failure.artifact_ref is None:
                unknown_failure = True
                continue
            artifact = by_ref.get((failure.source_ref, failure.artifact_ref))
            if artifact is None:
                unknown_failure = True
                continue
            failed_refs.add(artifact.id)

        provenance = Provenance(analyzer.id, version)
        for proposed in result.findings:
            artifact = by_ref.get((proposed.source_ref, proposed.artifact_ref))
            if artifact is None:
                unknown_failure = True
                failure_notes.append(
                    f"normalize: Artifact inexistente para {proposed.artifact_ref!r}"
                )
                continue
            attributes = redact_mapping(dict(proposed.attributes))
            attributes.setdefault("path", artifact.path.relative)
            attributes.setdefault("source_ref", artifact.source_ref)
            evidence_content = redact_mapping(dict(proposed.evidence_content))
            evidence_content.setdefault("rule", proposed.external_rule_id)
            evidence_content.setdefault("tags", attributes.get("tags", []))
            evidence_content.setdefault("namespace", attributes.get("namespace", ""))
            evidence = Evidence(
                scan_id=scan_id,
                kind=proposed.evidence_kind,
                source=analyzer.id,
                artifact_ref=artifact.id,
                content=evidence_content,
                provenance=provenance,
            )
            evidences.append(evidence)
            try:
                severity = Severity(proposed.severity.lower())
            except ValueError:
                severity = Severity.MEDIUM
            findings.append(
                Finding(
                    rule_id=f"{analyzer.id.upper()}.{proposed.external_rule_id}",
                    title=f"{analyzer.id}: {proposed.external_rule_id}",
                    category="signature",
                    severity=severity,
                    confidence=Confidence(ConfidenceClass.HIGH),
                    artifact_ref=artifact.id,
                    evidence_refs=(evidence.id,),
                    attributes=attributes,
                    provenance=provenance,
                )
            )

        failed_count = len(files) if unknown_failure else len(failed_refs)
        verified_count = max(0, len(files) - failed_count)
        if not files:
            state = CoverageState.NOT_APPLICABLE
        elif failed_count:
            state = CoverageState.PARTIAL
        else:
            state = CoverageState.COMPLETE
        coverage.append(
            CoverageEntry(
                capability=analyzer.id,
                state=state,
                applicable_checks=len(files),
                verified=verified_count,
                failed=failed_count,
                note="; ".join(failure_notes)[:200],
            )
        )
        status = ProviderRunStatus.PARTIAL if failed_count else ProviderRunStatus.COMPLETED
        provider_runs.append(
            ProviderRun(
                provider_id=analyzer.id,
                status=status,
                version=version,
                capabilities=capabilities,
                reason=("; ".join(failure_notes)[:200] or None),
            )
        )

    return evidences, findings, coverage, provider_runs


def _integrity_phase(
    target: Target, platform_id: str | None, providers: Sequence[IntegrityProvider]
) -> tuple[
    list[Finding],
    list[CoverageEntry],
    tuple[str, ...],
    tuple[str, ...],
    list[ProviderRun],
]:
    findings: list[Finding] = []
    coverage: list[CoverageEntry] = []
    provider_runs: list[ProviderRun] = []
    covered: list[str] = []
    diverged: list[str] = []
    for provider in providers:
        if provider.platforms and platform_id not in provider.platforms:
            provider_runs.append(
                ProviderRun(
                    provider_id=provider.id,
                    status=ProviderRunStatus.UNAVAILABLE,
                    capabilities=("integrity",),
                    reason="unsupported_platform",
                )
            )
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
            provider_runs.append(
                ProviderRun(
                    provider_id=provider.id,
                    status=(
                        ProviderRunStatus.UNAVAILABLE
                        if isinstance(e, ProviderUnavailable)
                        else ProviderRunStatus.FAILED
                    ),
                    capabilities=("integrity",),
                    reason=str(e)[:200],
                )
            )
            continue
        versions = sorted(
            {component.provider_version for component in components if component.provider_version}
        )
        provider_runs.append(
            ProviderRun(
                provider_id=provider.id,
                status=ProviderRunStatus.COMPLETED,
                version=versions[0] if versions else None,
                capabilities=("integrity",),
            )
        )
        for component in components:
            covered.extend(component.covers)
            if component.unverified:
                coverage.append(
                    CoverageEntry(
                        capability=f"baseline:{component.component}",
                        state=CoverageState.PARTIAL,
                        applicable_checks=1,
                        unavailable=1,
                        note=component.note or "sem baseline oficial",
                    )
                )
                continue
            prefix = "WP.CORE" if component.component == "wordpress-core" else "WP.PLUGIN"
            reference = component.trust is BaselineTrust.UNVERIFIED_REFERENCE
            for item in component.files:
                relative = (
                    f"{component.path_prefix.rstrip('/')}/{item.path}"
                    if component.path_prefix
                    else item.path
                )
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
                        artifact_ref=relative,
                        evidence_refs=(),
                        provenance=Provenance(
                            component.provider_id, component.provider_version or "unknown"
                        ),
                        attributes={
                            "component": component.component,
                            "path": relative,
                            "source_ref": "src_primary",
                            "note": item.note,
                            "trust": (component.trust.value if component.trust else "unknown"),
                        },
                    )
                )
    diverged = [f.attributes["path"] for f in findings if "path" in f.attributes]
    return findings, coverage, tuple(covered), tuple(diverged), provider_runs


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
    analyzers: Sequence[ExternalAnalyzer] = (),
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
    ck_findings, ck_coverage, covered, diverged, provider_runs = _integrity_phase(
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

    if analyzers:
        emit(ProgressEvent(phase="analyze", current=0, total=len(files)))
    an_evidence, an_findings, an_coverage, an_provider_runs = _analysis_phase(
        sid, artifacts, analyzers, found.platform_id if found else None
    )
    all_evidence.extend(an_evidence)
    all_findings.extend(an_findings)
    provider_runs.extend(an_provider_runs)

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
        *an_coverage,
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
        provider_runs=tuple(provider_runs),
    )
