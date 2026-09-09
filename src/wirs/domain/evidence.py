"""Evidence: observação imutável com provenance (spec 3.3). Só stdlib."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from types import MappingProxyType
from typing import Any


class RedactionState(Enum):
    NONE = "none"
    REDACTED = "redacted"


@dataclass(frozen=True)
class Provenance:
    collector: str
    version: str


def _evidence_id(scan_id: str, kind: str, artifact_ref: str, canonical: str) -> str:
    digest = hashlib.sha256(f"{scan_id}|{kind}|{artifact_ref}|{canonical}".encode()).hexdigest()[
        :16
    ]
    return f"ev_{digest}"


@dataclass(frozen=True)
class Evidence:
    scan_id: str
    kind: str
    source: str
    artifact_ref: str
    content: Mapping[str, Any]
    provenance: Provenance
    collected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    redaction_state: RedactionState = RedactionState.NONE
    id: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.content, dict):
            object.__setattr__(self, "content", MappingProxyType(dict(self.content)))
        try:
            canonical = json.dumps(dict(self.content), sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as e:
            raise ValueError(f"content de Evidence precisa ser JSON-serializável: {e}") from e
        if not self.id:
            object.__setattr__(
                self,
                "id",
                _evidence_id(self.scan_id, self.kind, self.artifact_ref, canonical),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "kind": self.kind,
            "source": self.source,
            "artifact_ref": self.artifact_ref,
            "content": dict(self.content),
            "provenance": {
                "collector": self.provenance.collector,
                "version": self.provenance.version,
            },
            "collected_at": self.collected_at.isoformat(),
            "redaction_state": self.redaction_state.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Evidence:
        prov = data["provenance"]
        return cls(
            scan_id=str(data["scan_id"]),
            kind=str(data["kind"]),
            source=str(data["source"]),
            artifact_ref=str(data["artifact_ref"]),
            content=dict(data.get("content", {})),
            provenance=Provenance(collector=str(prov["collector"]), version=str(prov["version"])),
            collected_at=datetime.fromisoformat(str(data["collected_at"])),
            redaction_state=RedactionState(str(data.get("redaction_state", "none"))),
            id=str(data.get("id", "")),
        )
