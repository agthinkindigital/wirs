"""ArtifactReader: único caminho para ler conteúdo do alvo. Só stdlib.

- Abre sempre em `rb` (bytes, nunca texto — decoding é decisão do detector).
- Streaming em chunks com budget total e cancelamento cooperativo.
- Recusa qualquer kind que não seja FILE *antes* de tocar o disco: abrir um
  symlink seguiria para o destino; abrir dir/special travaria ou explodiria.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Generator

from wirs.domain import Artifact, ArtifactKind
from wirs.domain.errors import BudgetExceeded, ReadCancelled, SecurityBoundaryError
from wirs.ports.reader import ArtifactReader as ArtifactReaderPort
from wirs.ports.reader import ReadBudget

__all__ = ["ArtifactReader", "ReadBudget"]


class ArtifactReader(ArtifactReaderPort):
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock

    def iter_chunks(
        self,
        artifact: Artifact,
        budget: ReadBudget,
        *,
        should_stop: Callable[[], bool] | None = None,
    ) -> Generator[bytes, None, None]:
        if artifact.kind is not ArtifactKind.FILE:
            raise SecurityBoundaryError(
                f"leitura recusada para kind {artifact.kind.value}: {artifact.path.relative!r}"
            )
        read = 0
        lines = 0
        line_start = True
        started_at = self._clock()
        with open(artifact.path.full, "rb") as fh:
            while True:
                if should_stop is not None and should_stop():
                    raise ReadCancelled(f"leitura cancelada em {read} bytes")
                if budget.timeout_s is not None and self._clock() - started_at >= budget.timeout_s:
                    raise BudgetExceeded(f"timeout de leitura após {read} bytes", bytes_read=read)
                if read >= budget.max_bytes:
                    if fh.read(1):
                        raise BudgetExceeded(
                            f"budget de {budget.max_bytes} bytes excedido", bytes_read=read
                        )
                    return
                chunk = fh.read(min(budget.chunk_size, budget.max_bytes - read))
                if not chunk:
                    return
                if budget.max_lines is not None:
                    allowed_end = len(chunk)
                    for index, byte in enumerate(chunk):
                        if line_start:
                            if lines >= budget.max_lines:
                                allowed_end = index
                                break
                            lines += 1
                            line_start = False
                        if byte == 0x0A:
                            line_start = True
                    if allowed_end != len(chunk):
                        prefix = chunk[:allowed_end]
                        if prefix:
                            read += len(prefix)
                            yield prefix
                        raise BudgetExceeded(
                            f"budget de {budget.max_lines} linhas excedido", bytes_read=read
                        )
                read += len(chunk)
                yield chunk
