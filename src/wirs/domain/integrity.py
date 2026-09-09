"""Tipos normalizados de integridade (anti-corruption: nenhum campo de vendor vaza)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IntegrityState(Enum):
    MATCH = "match"
    MISMATCH = "mismatch"
    MISSING = "missing"
    UNEXPECTED = "unexpected"


@dataclass(frozen=True)
class FileIntegrity:
    path: str
    state: IntegrityState
    expected: str | None = None
    actual: str | None = None
    note: str = ""
