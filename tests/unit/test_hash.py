"""HashService (WIRS-031)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterator

from wirs.domain import Artifact, ArtifactKind, SafePath
from wirs.infrastructure.hashing import HashService
from wirs.infrastructure.reader import ArtifactReader, ReadBudget


def _artifact(tmp_path, data: bytes) -> Artifact:
    (tmp_path / "a.bin").write_bytes(data)
    return Artifact(kind=ArtifactKind.FILE, path=SafePath(tmp_path, "a.bin"))


def test_sha256_conhecido_via_streaming(tmp_path) -> None:
    data = bytes(range(256)) * 100
    service = HashService(ArtifactReader())
    budget = ReadBudget(max_bytes=1 << 20, chunk_size=1024)

    assert service.digest(_artifact(tmp_path, data), budget) == hashlib.sha256(data).hexdigest()


def test_memoizacao_uma_leitura_para_n_consultas(tmp_path) -> None:
    data = b"conteudo repetido" * 500
    artifact = _artifact(tmp_path, data)
    budget = ReadBudget(max_bytes=1 << 20)

    leituras = 0
    base = ArtifactReader()

    class SpyReader(ArtifactReader):
        def iter_chunks(
            self,
            artifact: Artifact,
            budget: ReadBudget,
            *,
            should_stop: Callable[[], bool] | None = None,
        ) -> Iterator[bytes]:
            nonlocal leituras
            leituras += 1
            yield from base.iter_chunks(artifact, budget, should_stop=should_stop)

    service = HashService(SpyReader())
    primeiro = service.digest(artifact, budget)
    segundo = service.digest(artifact, budget)

    assert primeiro == segundo == hashlib.sha256(data).hexdigest()
    assert leituras == 1  # segunda consulta veio do memo, sem tocar o disco


def test_algoritmo_upstream_com_chave_separada(tmp_path) -> None:
    data = b"wordpress"
    service = HashService(ArtifactReader())
    budget = ReadBudget(max_bytes=1 << 20)

    md5 = service.digest(_artifact(tmp_path, data), budget, algorithm="md5")
    sha = service.digest(_artifact(tmp_path, data), budget)

    # md5 aqui é compatibilidade com baseline upstream, nunca segurança.
    assert md5 == hashlib.md5(data, usedforsecurity=False).hexdigest()
    assert sha == hashlib.sha256(data).hexdigest()
    assert md5 != sha
