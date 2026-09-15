"""Report canônico: a fonte de verdade que todas as views derivam (ADR-004). Só stdlib."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from wirs import __version__ as scanner_version
from wirs.domain import (
    Artifact,
    CoverageEntry,
    Diagnosis,
    Evidence,
    Finding,
    ProviderRun,
    SafePath,
    redact_mapping,
)

if TYPE_CHECKING:
    from wirs.application.orchestrator import ScanResult

SCHEMA_VERSION = "2.0"


def _diagnosis_key(item: Diagnosis) -> str:
    return item.diagnosis_id


@dataclass(frozen=True)
class CanonicalReport:
    scan_id: str
    target_root: str
    profile: str
    findings: tuple[Finding, ...] = ()
    coverage: tuple[CoverageEntry, ...] = ()
    generated_at: datetime | None = None
    note: str = ""
    artifacts: tuple[Artifact, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    provider_runs: tuple[ProviderRun, ...] = ()
    diagnoses: tuple[Diagnosis, ...] = ()
    target_kind: str = "local_directory"
    source_manifest: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "findings", tuple(self.findings))
        object.__setattr__(self, "coverage", tuple(self.coverage))
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "provider_runs", tuple(self.provider_runs))
        object.__setattr__(self, "diagnoses", tuple(self.diagnoses))
        if self.generated_at is None:
            object.__setattr__(self, "generated_at", datetime.now())

    @classmethod
    def from_scan_result(cls, result: ScanResult, *, note: str = "") -> CanonicalReport:
        """Transforma um ScanResult inteiro no único modelo canônico do report."""
        artifacts = list(result.artifacts)
        artifact_by_id = {artifact.id: artifact for artifact in artifacts}
        artifact_by_path = {
            (artifact.source_ref, artifact.path.relative): artifact for artifact in artifacts
        }
        findings: list[Finding] = []
        for finding in result.findings:
            if finding.artifact_ref not in artifact_by_id:
                relative = finding.attributes.get("path")
                source_ref = finding.attributes.get("source_ref", "src_primary")
                if isinstance(relative, str) and isinstance(source_ref, str):
                    observed = artifact_by_path.get((source_ref, relative))
                    if observed is not None:
                        finding = replace(finding, artifact_ref=observed.id, id="")
                    elif finding.rule_id.endswith("MISSING"):
                        logical = Artifact.expected_missing(
                            SafePath(Path(result.target_root), relative), source_ref=source_ref
                        )
                        artifact_by_id[logical.id] = logical
                        artifact_by_path[(source_ref, relative)] = logical
                        artifacts.append(logical)
                        finding = replace(finding, artifact_ref=logical.id, id="")
                elif finding.rule_id.endswith("MISSING"):
                    raise ValueError("Finding MISSING precisa de path e source_ref válidos")
            findings.append(finding)
        return cls(
            scan_id=result.scan_id,
            target_root=result.target_root,
            profile=result.profile,
            artifacts=tuple(artifacts),
            evidence=result.evidence,
            findings=tuple(findings),
            coverage=result.coverage,
            provider_runs=result.provider_runs,
            diagnoses=result.diagnoses,
            target_kind=result.target_kind,
            source_manifest=result.source_manifest,
            note=note,
        )

    def _validate_references(self) -> None:
        artifact_ids = {artifact.id for artifact in self.artifacts}
        evidence_ids = {item.id for item in self.evidence}
        if len(artifact_ids) != len(self.artifacts):
            raise ValueError("artifact IDs duplicados no report canônico")
        if len(evidence_ids) != len(self.evidence):
            raise ValueError("evidence IDs duplicados no report canônico")
        provider_run_ids = {run.id for run in self.provider_runs}
        if len(provider_run_ids) != len(self.provider_runs):
            raise ValueError("provider run IDs duplicados no report canônico")
        finding_ids = {finding.id for finding in self.findings}
        finding_by_id = {finding.id: finding for finding in self.findings}
        diagnosis_ids = {diagnosis.diagnosis_id for diagnosis in self.diagnoses}
        if len(diagnosis_ids) != len(self.diagnoses):
            raise ValueError("diagnosis IDs duplicados no report canônico")
        for item in self.evidence:
            if item.artifact_ref not in artifact_ids:
                raise ValueError(f"Evidence referencia Artifact inexistente: {item.artifact_ref}")
        for finding in self.findings:
            if finding.artifact_ref not in artifact_ids:
                raise ValueError(f"Finding referencia Artifact inexistente: {finding.artifact_ref}")
            missing = [ref for ref in finding.evidence_refs if ref not in evidence_ids]
            if missing:
                raise ValueError(f"Finding referencia Evidence inexistente: {missing[0]}")
        for diagnosis in self.diagnoses:
            if diagnosis.artifact_ref not in artifact_ids:
                raise ValueError(
                    f"Diagnosis referencia Artifact inexistente: {diagnosis.artifact_ref}"
                )
            missing_findings = [ref for ref in diagnosis.basis if ref not in finding_ids]
            if missing_findings:
                raise ValueError(f"Diagnosis referencia Finding inexistente: {missing_findings[0]}")
            wrong_artifact = next(
                (
                    ref
                    for ref in diagnosis.basis
                    if finding_by_id[ref].artifact_ref != diagnosis.artifact_ref
                ),
                None,
            )
            if wrong_artifact is not None:
                raise ValueError(f"Diagnosis mistura Artifacts na basis: {wrong_artifact}")
            missing_evidence = [ref for ref in diagnosis.evidence_refs if ref not in evidence_ids]
            if missing_evidence:
                raise ValueError(
                    f"Diagnosis referencia Evidence inexistente: {missing_evidence[0]}"
                )

    def to_dict(self) -> dict[str, Any]:
        self._validate_references()
        generated_at_value = self.generated_at
        if generated_at_value is None:
            raise ValueError("CanonicalReport precisa de generated_at")
        generated_at = generated_at_value.isoformat()
        source_refs = sorted({artifact.source_ref for artifact in self.artifacts})
        ordered_findings = sorted(self.findings, key=lambda f: f.id)
        ordered_coverage = sorted(self.coverage, key=lambda c: c.capability)
        artifact_payloads = []
        for artifact in sorted(self.artifacts, key=lambda a: a.id):
            serialized = artifact.to_dict()
            serialized.pop("root", None)
            artifact_payloads.append(serialized)
        target_payload: dict[str, Any] = {"root": self.target_root}
        if getattr(self, "target_kind", "local_directory") != "local_directory":
            target_payload["kind"] = self.target_kind
        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "scanner_version": scanner_version,
            "manifest": {
                "scan_id": self.scan_id,
                "profile": self.profile,
                "generated_at": generated_at,
                "target": target_payload,
                "sources": [{"source_ref": source_ref} for source_ref in source_refs],
            },
            "artifacts": artifact_payloads,
            "evidence": [item.to_dict() for item in sorted(self.evidence, key=lambda e: e.id)],
            "findings": [f.to_dict() for f in ordered_findings],
            "coverage": [c.to_dict() for c in ordered_coverage],
            "provider_runs": [
                run.to_dict() for run in sorted(self.provider_runs, key=lambda r: r.id)
            ],
            "diagnoses": [
                item.to_dict()
                for item in sorted(
                    self.diagnoses,
                    key=_diagnosis_key,
                )
            ],
            "note": self.note,
        }
        source_manifest = self.source_manifest
        if source_manifest is not None:
            payload["manifest"]["source_manifest"] = source_manifest
        return redact_mapping(payload)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CanonicalReport:
        if str(data.get("schema_version")) != SCHEMA_VERSION:
            raise ValueError(f"schema_version incompatível: {data.get('schema_version')!r}")
        manifest = data["manifest"]
        target = manifest["target"]
        artifact_root = Path(str(target["root"]))
        if not artifact_root.is_absolute():
            artifact_root = Path.cwd()
        artifact_data = []
        for item in data.get("artifacts", []):
            restored = dict(item)
            restored.setdefault("root", artifact_root)
            artifact_data.append(restored)
        return cls(
            scan_id=str(manifest["scan_id"]),
            target_root=str(target["root"]),
            profile=str(manifest.get("profile", "soft")),
            findings=tuple(Finding.from_dict(f) for f in data.get("findings", [])),
            coverage=tuple(CoverageEntry.from_dict(c) for c in data.get("coverage", [])),
            generated_at=datetime.fromisoformat(str(manifest["generated_at"])),
            note=str(data.get("note", "")),
            artifacts=tuple(Artifact.from_dict(item) for item in artifact_data),
            evidence=tuple(Evidence.from_dict(item) for item in data.get("evidence", [])),
            provider_runs=tuple(
                ProviderRun.from_dict(item) for item in data.get("provider_runs", [])
            ),
            diagnoses=tuple(Diagnosis.from_dict(item) for item in data.get("diagnoses", [])),
            target_kind=str(target.get("kind", "local_directory")),
            source_manifest=(
                manifest.get("source_manifest")
                if isinstance(manifest.get("source_manifest"), Mapping)
                else None
            ),
        )
