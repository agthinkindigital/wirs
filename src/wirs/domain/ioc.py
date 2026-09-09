"""IOC: indicador com tipo e valor validados (spec WIRS-050). Só stdlib."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum


class IOCKind(Enum):
    LITERAL = "literal"
    DOMAIN = "domain"
    URL_FRAGMENT = "url_fragment"
    PATH_FRAGMENT = "path_fragment"
    SHA256 = "sha256"


_DOMAIN = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _normalize(kind: IOCKind, value: str) -> str:
    if not value:
        raise ValueError(f"IOC {kind.value} não pode ter valor vazio")
    if kind is IOCKind.SHA256:
        lowered = value.lower()
        if not _HEX64.match(lowered):
            raise ValueError(f"SHA-256 exige 64 hex: {value!r:.40}")
        return lowered
    if kind is IOCKind.DOMAIN:
        lowered = value.lower().rstrip(".")
        if not _DOMAIN.match(lowered):
            raise ValueError(f"domain inválido: {value!r:.60}")
        return lowered
    return value


@dataclass(frozen=True)
class IOC:
    kind: IOCKind
    value: str
    label: str = ""
    id: str = ""

    def __post_init__(self) -> None:
        normalized = _normalize(self.kind, self.value)
        object.__setattr__(self, "value", normalized)
        if not self.id:
            digest = hashlib.sha256(f"{self.kind.value}|{normalized}".encode()).hexdigest()[:12]
            object.__setattr__(self, "id", f"ioc_{digest}")

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "kind": self.kind.value, "value": self.value, "label": self.label}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> IOC:
        return cls(
            kind=IOCKind(str(data["kind"])),
            value=str(data["value"]),
            label=str(data.get("label", "")),
            id=str(data.get("id", "")),
        )
