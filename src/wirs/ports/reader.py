"""Seam de leitura de conteúdo (implementada por infrastructure.reader)."""

from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from wirs.domain import Artifact


@dataclass(frozen=True)
class ReadBudget:
    max_bytes: int
    chunk_size: int = 65536

    def __post_init__(self) -> None:
        if self.max_bytes <= 0 or self.chunk_size <= 0:
            raise ValueError("budget precisa de max_bytes e chunk_size positivos")


@runtime_checkable
class ArtifactReader(Protocol):
    def iter_chunks(
        self,
        artifact: Artifact,
        budget: ReadBudget,
        *,
        should_stop: Callable[[], bool] | None = None,
    ) -> Generator[bytes, None, None]: ...
