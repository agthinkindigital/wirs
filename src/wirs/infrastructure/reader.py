"""ArtifactReader: único caminho para ler conteúdo do alvo. Só stdlib.

- Abre sempre em `rb` (bytes, nunca texto — decoding é decisão do detector).
- Streaming em chunks com budget total e cancelamento cooperativo.
- Recusa qualquer kind que não seja FILE *antes* de tocar o disco: abrir um
  symlink seguiria para o destino; abrir dir/special travaria ou explodiria.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass

from wirs.domain import Artifact, ArtifactKind
from wirs.domain.errors import BudgetExceeded, ReadCancelled, SecurityBoundaryError


@dataclass(frozen=True)
class ReadBudget:
    max_bytes: int
    chunk_size: int = 65536

    def __post_init__(self) -> None:
        if self.max_bytes <= 0 or self.chunk_size <= 0:
            raise ValueError("budget precisa de max_bytes e chunk_size positivos")


class ArtifactReader:
    def iter_chunks(
        self,
        artifact: Artifact,
        budget: ReadBudget,
        *,
        should_stop: Callable[[], bool] | None = None,
    ) -> Iterator[bytes]:
        if artifact.kind is not ArtifactKind.FILE:
            raise SecurityBoundaryError(
                f"leitura recusada para kind {artifact.kind.value}: {artifact.path.relative!r}"
            )
        read = 0
        with open(artifact.path.full, "rb") as fh:
            while True:
                if should_stop is not None and should_stop():
                    raise ReadCancelled(f"leitura cancelada em {read} bytes")
                chunk = fh.read(min(budget.chunk_size, budget.max_bytes - read))
                if not chunk:
                    return
                read += len(chunk)
                if read >= budget.max_bytes:
                    # Consome o próximo byte para saber se acabou exatamente no limite.
                    if fh.read(1):
                        raise BudgetExceeded(
                            f"budget de {budget.max_bytes} bytes excedido", bytes_read=read
                        )
                    yield chunk
                    return
                yield chunk
