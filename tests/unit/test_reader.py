"""ArtifactReader read-only (WIRS-030)."""

from __future__ import annotations

import pytest

from wirs.domain import Artifact, ArtifactKind, SafePath, SecurityBoundaryError
from wirs.infrastructure.reader import ArtifactReader, ReadBudget


def _file_artifact(tmp_path, name: str, data: bytes) -> Artifact:
    (tmp_path / name).write_bytes(data)
    return Artifact(kind=ArtifactKind.FILE, path=SafePath(tmp_path, name))


def test_leitura_rb_com_streaming(tmp_path) -> None:
    data = bytes(range(256)) * 40  # 10240 bytes binários (não-UTF-8 incluso)
    artifact = _file_artifact(tmp_path, "a.bin", data)
    reader = ArtifactReader()

    chunks = list(reader.iter_chunks(artifact, ReadBudget(max_bytes=1 << 20, chunk_size=1024)))

    assert len(chunks) == 10  # streaming de verdade, não leitura única
    assert all(isinstance(c, bytes) for c in chunks)
    assert b"".join(chunks) == data


@pytest.mark.parametrize("kind", [ArtifactKind.DIR, ArtifactKind.SYMLINK, ArtifactKind.SPECIAL])
def test_nao_file_recusado_sem_tocar_o_disco(tmp_path, kind: ArtifactKind) -> None:
    import pytest

    # Paths INEXISTENTES: se tocar o disco, dá FileNotFoundError em vez do guarda.
    artifact = Artifact(kind=kind, path=SafePath(tmp_path, "fantasma"))
    with pytest.raises(SecurityBoundaryError):
        list(ArtifactReader().iter_chunks(artifact, ReadBudget(max_bytes=1024)))


def test_budget_excedido(tmp_path) -> None:
    from wirs.domain import BudgetExceeded

    artifact = _file_artifact(tmp_path, "g.txt", b"x" * 5000)

    with pytest.raises(BudgetExceeded) as exc:
        list(ArtifactReader().iter_chunks(artifact, ReadBudget(max_bytes=1024)))
    assert exc.value.bytes_read == 1024

    # Arquivo que termina EXATAMENTE no limite não é erro.
    exato = _file_artifact(tmp_path, "e.txt", b"y" * 1024)
    assert b"".join(ArtifactReader().iter_chunks(exato, ReadBudget(max_bytes=1024))) == b"y" * 1024


def test_cancelamento_cooperativo(tmp_path) -> None:
    from wirs.domain import ReadCancelled

    artifact = _file_artifact(tmp_path, "c.txt", b"z" * 10000)
    chamadas = 0

    def parar_na_segunda() -> bool:
        nonlocal chamadas
        chamadas += 1
        return chamadas >= 2

    with pytest.raises(ReadCancelled):
        list(
            ArtifactReader().iter_chunks(
                artifact,
                ReadBudget(max_bytes=1 << 20, chunk_size=1024),
                should_stop=parar_na_segunda,
            )
        )
    assert chamadas >= 2


def test_budget_invalido_rejeitado() -> None:
    import pytest as pt

    with pt.raises(ValueError):
        ReadBudget(max_bytes=0)
    with pt.raises(ValueError):
        ReadBudget(max_bytes=100, chunk_size=0)
