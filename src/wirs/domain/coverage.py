"""Coverage: abrangência real da análise (ADR-010). Só stdlib."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any


class CoverageState(Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class CoverageEntry:
    capability: str
    state: CoverageState
    applicable_checks: int = 0
    verified: int = 0
    failed: int = 0
    skipped: int = 0
    unavailable: int = 0
    note: str = ""

    def __post_init__(self) -> None:
        counts = (self.verified, self.failed, self.skipped, self.unavailable)
        if any(c < 0 for c in counts) or self.applicable_checks < 0:
            raise ValueError("contadores de coverage não podem ser negativos")
        # Invariante: todo check aplicável cai em exatamente um balde.
        if sum(counts) != self.applicable_checks:
            raise ValueError(
                "verified+failed+skipped+unavailable precisa igualar applicable_checks"
            )
        rest = self.failed + self.skipped + self.unavailable
        match self.state:
            case CoverageState.COMPLETE:
                if rest != 0 or self.applicable_checks == 0:
                    raise ValueError("COMPLETE exige tudo verificado e ao menos 1 check")
            case CoverageState.PARTIAL:
                if rest == 0:
                    raise ValueError("PARTIAL exige ao menos 1 check não verificado")
            case CoverageState.UNAVAILABLE:
                if self.verified != 0 or self.failed != 0:
                    raise ValueError("UNAVAILABLE: nada foi executado")
            case CoverageState.SKIPPED:
                if self.verified != 0 or self.failed != 0 or self.unavailable != 0:
                    raise ValueError("SKIPPED: tudo foi pulado deliberadamente")
            case CoverageState.NOT_APPLICABLE:
                if self.applicable_checks != 0:
                    raise ValueError("NOT_APPLICABLE exige 0 checks aplicáveis")
            case CoverageState.FAILED:
                pass  # capability falhou por inteiro; contadores descrevem o estrago

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "state": self.state.value,
            "applicable_checks": self.applicable_checks,
            "verified": self.verified,
            "failed": self.failed,
            "skipped": self.skipped,
            "unavailable": self.unavailable,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CoverageEntry:
        return cls(
            capability=str(data["capability"]),
            state=CoverageState(str(data["state"])),
            applicable_checks=int(data.get("applicable_checks", 0)),
            verified=int(data.get("verified", 0)),
            failed=int(data.get("failed", 0)),
            skipped=int(data.get("skipped", 0)),
            unavailable=int(data.get("unavailable", 0)),
            note=str(data.get("note", "")),
        )
