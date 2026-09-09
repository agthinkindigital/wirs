"""HashService: identidade de conteúdo com leitura única por scan. Só stdlib.

- Uma instância por scan: o memo vive na instância e morre com ela.
- Streaming: alimenta o hasher chunk a chunk, sem materializar o arquivo.
- Algoritmo interno é SHA-256; `algorithm` alternativo (ex.: md5) existe para
  respeitar baseline upstream quando exigido (spec Q14) — com chave separada.
"""

from __future__ import annotations

import hashlib

from wirs.domain import Artifact
from wirs.infrastructure.reader import ArtifactReader, ReadBudget


class HashService:
    def __init__(self, reader: ArtifactReader) -> None:
        self._reader = reader
        self._memo: dict[tuple[str, str], str] = {}

    def digest(
        self,
        artifact: Artifact,
        budget: ReadBudget,
        *,
        algorithm: str = "sha256",
    ) -> str:
        key = (artifact.id, algorithm)
        cached = self._memo.get(key)
        if cached is not None:
            return cached
        hasher = hashlib.new(algorithm)
        for chunk in self._reader.iter_chunks(artifact, budget):
            hasher.update(chunk)
        result = hasher.hexdigest()
        self._memo[key] = result
        return result
