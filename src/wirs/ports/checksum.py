"""Seam de integridade por componente (ex.: core WP, plugin X).

Um provider cobre um ou mais componentes; cada componente vira findings
(arquivos divergentes) e, quando sem baseline, coverage explícito.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from wirs.domain import FileIntegrity, Target


@dataclass(frozen=True)
class ComponentIntegrity:
    provider_id: str
    provider_version: str | None
    component: str
    files: tuple[FileIntegrity, ...] = ()
    unverified: bool = False
    # Prefixos relativos cobertos quando VERIFICADO (baseline confiável absolve:
    # heurísticas não acusam o que o upstream já absolveu). Vazio = desconhecido.
    covers: tuple[str, ...] = ()


@runtime_checkable
class IntegrityProvider(Protocol):
    id: str

    def verify(self, target: Target) -> list[ComponentIntegrity]: ...
