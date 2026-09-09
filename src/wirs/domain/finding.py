"""Finding: afirmação normalizada sustentada por evidência (spec 3.4 e 4). Só stdlib."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any

from wirs.domain.evidence import Provenance


class Severity(Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceClass(Enum):
    DETERMINISTIC = "deterministic"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Confidence:
    """Classe de confiança + score opcional (complementa, nunca substitui)."""

    class_: ConfidenceClass
    score: float | None = None

    def __post_init__(self) -> None:
        if self.score is not None and not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score de confiança fora de 0.0–1.0: {self.score}")


def _finding_id(rule_id: str, artifact_ref: str, refs: str, canonical: str) -> str:
    digest = hashlib.sha256(f"{rule_id}|{artifact_ref}|{refs}|{canonical}".encode()).hexdigest()[
        :16
    ]
    return f"fnd_{digest}"


@dataclass(frozen=True)
class Finding:
    rule_id: str
    title: str
    category: str
    severity: Severity
    confidence: Confidence
    artifact_ref: str
    evidence_refs: tuple[str, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    provenance: Provenance | None = None
    status: str = "open"
    id: str = ""

    def __post_init__(self) -> None:
        refs = tuple(self.evidence_refs)
        object.__setattr__(self, "evidence_refs", refs)
        if isinstance(self.attributes, dict):
            object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))
        # Invariante 2: sem Evidence e sem provenance explícita, não há Finding.
        if not refs and self.provenance is None:
            raise ValueError("finding exige evidence_refs ou provenance explícita de provider")
        try:
            canonical = json.dumps(dict(self.attributes), sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as e:
            raise ValueError(f"attributes de Finding precisa ser JSON-serializável: {e}") from e
        if not self.id:
            object.__setattr__(
                self,
                "id",
                _finding_id(self.rule_id, self.artifact_ref, ",".join(sorted(refs)), canonical),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "title": self.title,
            "category": self.category,
            "severity": self.severity.value,
            "confidence": {
                "class": self.confidence.class_.value,
                "score": self.confidence.score,
            },
            "artifact_ref": self.artifact_ref,
            "evidence_refs": list(self.evidence_refs),
            "attributes": dict(self.attributes),
            "provenance": (
                None
                if self.provenance is None
                else {
                    "collector": self.provenance.collector,
                    "version": self.provenance.version,
                }
            ),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Finding:
        conf = data["confidence"]
        prov = data.get("provenance")
        return cls(
            rule_id=str(data["rule_id"]),
            title=str(data["title"]),
            category=str(data["category"]),
            severity=Severity(str(data["severity"])),
            confidence=Confidence(
                ConfidenceClass(str(conf["class"])),
                score=None if conf.get("score") is None else float(conf["score"]),
            ),
            artifact_ref=str(data["artifact_ref"]),
            evidence_refs=tuple(str(r) for r in data.get("evidence_refs", ())),
            attributes=dict(data.get("attributes", {})),
            provenance=(
                None
                if prov is None
                else Provenance(collector=str(prov["collector"]), version=str(prov["version"]))
            ),
            status=str(data.get("status", "open")),
            id=str(data.get("id", "")),
        )
