"""Ports de plataforma: seams que variam por ecossistema (WP, Laravel...)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from wirs.domain import Target


@dataclass(frozen=True)
class PlatformDiscovery:
    platform_id: str
    signals: tuple[str, ...] = ()
    version: str | None = None


@runtime_checkable
class PlatformAdapter(Protocol):
    id: str

    def discover(self, target: Target) -> PlatformDiscovery | None:
        """Identifica a plataforma sem exigir banco. None = não detectado."""
        ...
