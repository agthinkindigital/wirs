"""Artifact model (WIRS-012, spec 3.2)."""

from __future__ import annotations

from wirs.domain import Artifact, ArtifactKind, SafePath


def test_file_artifact_com_id_estavel(tmp_path) -> None:
    path = SafePath(tmp_path, "wp-includes/version.php")
    a = Artifact(kind=ArtifactKind.FILE, path=path)
    b = Artifact(kind=ArtifactKind.FILE, path=path)

    assert a.id == b.id  # estável para mesmo kind + path
    assert a.id.startswith("art_")
    assert a.path.relative == "wp-includes/version.php"
    assert Artifact(kind=ArtifactKind.DIR, path=path).id != a.id  # kind compõe o ID


def test_kinds_dir_symlink_special(tmp_path) -> None:
    d = Artifact(kind=ArtifactKind.DIR, path=SafePath(tmp_path, "wp-content"))
    assert d.kind is ArtifactKind.DIR

    link = Artifact(
        kind=ArtifactKind.SYMLINK,
        path=SafePath(tmp_path, "link"),
        symlink_target="/srv/fora/alvo",  # destino é DADO, nunca seguido aqui
    )
    assert link.symlink_target == "/srv/fora/alvo"

    fifo = Artifact(kind=ArtifactKind.SPECIAL, path=SafePath(tmp_path, "fifo"))
    assert fifo.kind is ArtifactKind.SPECIAL
    assert fifo.symlink_target is None


def test_from_stat_mapeia_metadata_sem_io(tmp_path) -> None:
    import os
    import stat as statmod

    alvo = tmp_path / "a.php"
    alvo.write_bytes(b"<?php // x")  # I/O do TESTE; o objeto nunca faz I/O
    st = os.stat(alvo)

    a = Artifact.from_stat(
        kind=ArtifactKind.FILE,
        path=SafePath(tmp_path, "a.php"),
        st=st,
    )
    assert a.metadata.size == 10
    assert statmod.S_ISREG(a.metadata.mode or 0)
    assert a.metadata.mtime_ns == st.st_mtime_ns
    assert a.metadata.ino == st.st_ino


def test_round_trip_serializacao(tmp_path) -> None:
    original = Artifact(
        kind=ArtifactKind.SYMLINK,
        path=SafePath(tmp_path, "link"),
        symlink_target="alvo",
    )
    restaurado = Artifact.from_dict(original.to_dict())

    assert restaurado == original
    assert restaurado.id == original.id
