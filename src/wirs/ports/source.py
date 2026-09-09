"""Seam de fonte de artifacts (local, archive, SFTP...)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Protocol

from wirs.domain import Target


class ArtifactSource(Protocol):
    def iter_artifacts(self, target: Target) -> Iterator[Any]:
        """Itens heterogêneos por desenho: Artifact ou gap de caracterização."""
        ...
