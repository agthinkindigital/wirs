"""Estado genérico de uma execução de provider (ADR-010)."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ProviderRunStatus(Enum):
    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"
    PARTIAL = "partial"


def _provider_run_id(
    provider_id: str,
    status: ProviderRunStatus,
    version: str | None,
    capabilities: tuple[str, ...],
    reason: str | None,
) -> str:
    canonical = "|".join(
        (provider_id, status.value, version or "", ",".join(capabilities), reason or "")
    )
    return f"prun_{hashlib.sha256(canonical.encode()).hexdigest()[:16]}"


@dataclass(frozen=True)
class ProviderRun:
    provider_id: str
    status: ProviderRunStatus
    version: str | None = None
    capabilities: tuple[str, ...] = ()
    reason: str | None = None
    id: str = ""

    def __post_init__(self) -> None:
        if not self.provider_id:
            raise ValueError("provider_id não pode ser vazio")
        capabilities = tuple(sorted(set(self.capabilities)))
        object.__setattr__(self, "capabilities", capabilities)
        if not self.id:
            object.__setattr__(
                self,
                "id",
                _provider_run_id(
                    self.provider_id, self.status, self.version, capabilities, self.reason
                ),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "status": self.status.value,
            "version": self.version,
            "capabilities": list(self.capabilities),
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProviderRun:
        return cls(
            provider_id=str(data["provider_id"]),
            status=ProviderRunStatus(str(data["status"])),
            version=None if data.get("version") is None else str(data["version"]),
            capabilities=tuple(str(item) for item in data.get("capabilities", ())),
            reason=None if data.get("reason") is None else str(data["reason"]),
            id=str(data.get("id", "")),
        )
