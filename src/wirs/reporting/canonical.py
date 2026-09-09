"""Report canônico: a fonte de verdade que todas as views derivam (ADR-004). Só stdlib."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from wirs import __version__ as scanner_version
from wirs.domain import CoverageEntry, Finding

SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class CanonicalReport:
    scan_id: str
    target_root: str
    profile: str
    findings: tuple[Finding, ...] = ()
    coverage: tuple[CoverageEntry, ...] = ()
    generated_at: datetime | None = None
    note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "findings", tuple(self.findings))
        object.__setattr__(self, "coverage", tuple(self.coverage))

    def to_dict(self) -> dict[str, Any]:
        ordered_findings = sorted(self.findings, key=lambda f: f.id)
        ordered_coverage = sorted(self.coverage, key=lambda c: c.capability)
        return {
            "schema_version": SCHEMA_VERSION,
            "scanner_version": scanner_version,
            "scan_id": self.scan_id,
            "target_root": self.target_root,
            "profile": self.profile,
            "generated_at": (self.generated_at or datetime.now()).isoformat(),
            "findings": [f.to_dict() for f in ordered_findings],
            "coverage": [c.to_dict() for c in ordered_coverage],
            "note": self.note,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CanonicalReport:
        gen = data.get("generated_at")
        return cls(
            scan_id=str(data["scan_id"]),
            target_root=str(data["target_root"]),
            profile=str(data.get("profile", "soft")),
            findings=tuple(Finding.from_dict(f) for f in data.get("findings", [])),
            coverage=tuple(CoverageEntry.from_dict(c) for c in data.get("coverage", [])),
            generated_at=None if gen is None else datetime.fromisoformat(str(gen)),
            note=str(data.get("note", "")),
        )
