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
    # Prefixos relativos que o provider VERIFICOU nesta run (baseline confiável
    # absolve). Inclui paths verificados mesmo quando outros divergiram: só os
    # divergentes (em `files`) continuam sujeitos a detecção (correlação DX001).
    covers: tuple[str, ...] = ()


@runtime_checkable
class IntegrityProvider(Protocol):
    id: str
    # Plataformas atendidas; vazio = qualquer uma. Orquestrador só chama quando
    # a plataforma detectada está incluída (evita FAILED barulhento em subdir).
    platforms: tuple[str, ...]

    def verify(self, target: Target) -> list[ComponentIntegrity]: ...
