"""Diagnosis: hipótese auditável derivada de Findings existentes."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from wirs.domain.artifact import Artifact
from wirs.domain.evidence import Evidence
from wirs.domain.finding import ConfidenceClass, Finding, Severity


def _diagnosis_id(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"dx_{hashlib.sha256(canonical.encode()).hexdigest()[:16]}"


@dataclass(frozen=True)
class Diagnosis:
    """Interpretação file-centric; não é Finding e não cria Evidence."""

    rule_id: str
    title: str
    summary: str
    artifact_ref: str
    confidence: ConfidenceClass
    basis: tuple[str, ...]
    hypothesis: str
    alternative_hypotheses: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    recommended_next_checks: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    requires_human_confirmation: bool = True
    severity: Severity = Severity.HIGH
    diagnosis_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "basis", tuple(self.basis))
        object.__setattr__(self, "alternative_hypotheses", tuple(self.alternative_hypotheses))
        object.__setattr__(self, "unknowns", tuple(self.unknowns))
        object.__setattr__(self, "recommended_next_checks", tuple(self.recommended_next_checks))
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))
        if not self.basis:
            raise ValueError("Diagnosis exige pelo menos um Finding na basis")
        if not self.artifact_ref:
            raise ValueError("Diagnosis exige artifact_ref")
        if not self.hypothesis:
            raise ValueError("Diagnosis exige hypothesis")
        if not self.diagnosis_id:
            object.__setattr__(self, "diagnosis_id", _diagnosis_id(self._identity_payload()))

    def _identity_payload(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "artifact_ref": self.artifact_ref,
            "confidence": self.confidence.value,
            "basis": sorted(self.basis),
            "evidence_refs": sorted(self.evidence_refs),
            "hypothesis": self.hypothesis,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "diagnosis_id": self.diagnosis_id,
            "rule_id": self.rule_id,
            "title": self.title,
            "summary": self.summary,
            "artifact_ref": self.artifact_ref,
            "confidence": self.confidence.value,
            "basis": list(self.basis),
            "evidence_refs": list(self.evidence_refs),
            "hypothesis": self.hypothesis,
            "alternative_hypotheses": list(self.alternative_hypotheses),
            "unknowns": list(self.unknowns),
            "recommended_next_checks": list(self.recommended_next_checks),
            "requires_human_confirmation": self.requires_human_confirmation,
            "severity": self.severity.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Diagnosis:
        return cls(
            rule_id=str(data["rule_id"]),
            title=str(data["title"]),
            summary=str(data.get("summary", "")),
            artifact_ref=str(data["artifact_ref"]),
            confidence=ConfidenceClass(str(data["confidence"])),
            basis=tuple(str(ref) for ref in data["basis"]),
            evidence_refs=tuple(str(ref) for ref in data.get("evidence_refs", ())),
            hypothesis=str(data["hypothesis"]),
            alternative_hypotheses=tuple(
                str(item) for item in data.get("alternative_hypotheses", ())
            ),
            unknowns=tuple(str(item) for item in data.get("unknowns", ())),
            recommended_next_checks=tuple(
                str(item) for item in data.get("recommended_next_checks", ())
            ),
            requires_human_confirmation=bool(data.get("requires_human_confirmation", True)),
            severity=Severity(str(data.get("severity", Severity.HIGH.value))),
            diagnosis_id=str(data.get("diagnosis_id", data.get("id", ""))),
        )


def _artifact_for_finding(finding: Finding, artifacts: Sequence[Artifact]) -> Artifact | None:
    by_id = {artifact.id: artifact for artifact in artifacts}
    direct = by_id.get(finding.artifact_ref)
    if direct is not None:
        return direct
    path = finding.attributes.get("path")
    source_ref = finding.attributes.get("source_ref", "src_primary")
    if not isinstance(path, str) or not isinstance(source_ref, str):
        return None
    return next(
        (
            artifact
            for artifact in artifacts
            if artifact.source_ref == source_ref and artifact.path.relative == path
        ),
        None,
    )


def _is_trusted_mismatch(finding: Finding) -> bool:
    trust = finding.attributes.get("trust")
    return (
        finding.rule_id.endswith("HASH_MISMATCH")
        and finding.confidence.class_ is ConfidenceClass.DETERMINISTIC
        and trust != "unverified_reference"
    )


def _is_high_signature(finding: Finding) -> bool:
    return (
        finding.category in {"signature", "heuristic"}
        and finding.confidence.class_ is ConfidenceClass.HIGH
    )


def correlate_diagnoses(
    *,
    artifacts: Sequence[Artifact],
    findings: Sequence[Finding],
    evidence: Sequence[Evidence],
) -> tuple[Diagnosis, ...]:
    """Aplica DX001 sem criar Evidence e sem alterar os Findings de entrada."""
    evidence_ids = {item.id for item in evidence}
    grouped: defaultdict[str, list[Finding]] = defaultdict(list)
    artifact_by_id = {artifact.id: artifact for artifact in artifacts}
    for finding in findings:
        artifact = _artifact_for_finding(finding, artifacts)
        if artifact is not None:
            grouped[artifact.id].append(finding)

    diagnoses: list[Diagnosis] = []
    for artifact_id, candidates in sorted(grouped.items()):
        mismatches = [finding for finding in candidates if _is_trusted_mismatch(finding)]
        signatures = [finding for finding in candidates if _is_high_signature(finding)]
        if not mismatches or not signatures:
            continue
        base = sorted((*mismatches, *signatures), key=lambda finding: finding.id)
        if not any(finding.evidence_refs for finding in signatures):
            continue
        if any(ref not in evidence_ids for finding in base for ref in finding.evidence_refs):
            continue
        evidence_refs = tuple(sorted({ref for finding in base for ref in finding.evidence_refs}))
        artifact = artifact_by_id[artifact_id]
        diagnoses.append(
            Diagnosis(
                rule_id="DX001",
                title="Possível adulteração de Artifact confiável",
                summary=(
                    "Um mismatch de baseline confiável e uma assinatura de malware "
                    "convergem no mesmo Artifact."
                ),
                artifact_ref=artifact.id,
                confidence=ConfidenceClass.HIGH,
                basis=tuple(finding.id for finding in base),
                evidence_refs=evidence_refs,
                hypothesis=(
                    "O Artifact confiável pode ter sido adulterado; a confirmação "
                    "exige revisão humana e validação do baseline."
                ),
                alternative_hypotheses=(
                    "O baseline pode não refletir a versão legítima implantada.",
                    "A assinatura pode ser um falso positivo contextual.",
                ),
                unknowns=("A origem e o momento da alteração não são conhecidos neste scan.",),
                recommended_next_checks=(
                    "Revisar o conteúdo e confirmar o baseline usado.",
                    "Comparar o arquivo com um pacote confiável da mesma versão.",
                ),
                severity=Severity.CRITICAL,
            )
        )
    return tuple(sorted(diagnoses, key=lambda diagnosis: diagnosis.diagnosis_id))
