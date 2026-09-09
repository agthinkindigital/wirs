"""Inventory de filesystem local (WIRS-013)."""

from __future__ import annotations

import inspect

from wirs.domain import Artifact, ArtifactKind, LocalDirectoryTarget
from wirs.infrastructure.filesystem import InventoryGap, LocalArtifactSource


def _try_symlink(target: str, link: str) -> bool:
    import os

    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError):
        return False
    return True


def _tree(root) -> None:
    (root / "a.php").write_bytes(b"<?php // a")
    (root / ".hidden").write_bytes(b"h")
    sub = root / "dir"
    sub.mkdir()
    (sub / "b.txt").write_bytes(b"b")


def test_inventario_arquivos_hidden_subdir(tmp_path) -> None:
    _tree(tmp_path)
    target = LocalDirectoryTarget(tmp_path)

    items = list(LocalArtifactSource().iter_artifacts(target))
    arts = [i for i in items if isinstance(i, Artifact)]

    relatives = sorted(a.path.relative for a in arts)
    assert relatives == ["", ".hidden", "a.php", "dir", "dir/b.txt"]  # "" = root
    kinds = {a.path.relative: a.kind for a in arts}
    assert kinds["a.php"] is ArtifactKind.FILE
    assert kinds["dir"] is ArtifactKind.DIR


def test_ordem_deterministica_e_streaming(tmp_path) -> None:
    _tree(tmp_path)
    target = LocalDirectoryTarget(tmp_path)
    src = LocalArtifactSource()

    assert inspect.isgeneratorfunction(src.iter_artifacts)

    primeira = [a.path.relative for a in src.iter_artifacts(target) if isinstance(a, Artifact)]
    segunda = [a.path.relative for a in src.iter_artifacts(target) if isinstance(a, Artifact)]
    assert primeira == segunda


def test_symlink_registrado_sem_atravessar(tmp_path) -> None:
    import pytest

    real = tmp_path / "real"
    real.mkdir()
    (real / "dentro.txt").write_bytes(b"x")
    if not _try_symlink(str(real), str(tmp_path / "atalho")):
        pytest.skip("SO não permite criar symlink sem privilégio")
    if not _try_symlink(str(tmp_path / "inexistente"), str(tmp_path / "quebrado")):
        pytest.skip("SO não permite criar symlink sem privilégio")

    target = LocalDirectoryTarget(tmp_path)
    arts = [i for i in LocalArtifactSource().iter_artifacts(target) if isinstance(i, Artifact)]
    por_rel = {a.path.relative: a for a in arts}

    assert por_rel["atalho"].kind is ArtifactKind.SYMLINK
    assert por_rel["quebrado"].kind is ArtifactKind.SYMLINK
    # Conteúdo atrás do link NÃO é atravessado: só aparece pelo path real.
    assert "atalho/dentro.txt" not in por_rel
    assert por_rel["real/dentro.txt"].kind is ArtifactKind.FILE


def test_special_nunca_aberto(tmp_path) -> None:
    import os

    import pytest

    if not hasattr(os, "mkfifo"):
        pytest.skip("SO sem mkfifo")
    os.mkfifo(tmp_path / "canal")

    target = LocalDirectoryTarget(tmp_path)
    # Se o inventory tentasse ABRIR o fifo, este teste travaria para sempre.
    arts = [i for i in LocalArtifactSource().iter_artifacts(target) if isinstance(i, Artifact)]
    por_rel = {a.path.relative: a for a in arts}
    assert por_rel["canal"].kind is ArtifactKind.SPECIAL


def test_child_ilegivel_vira_gap_e_scan_continua(tmp_path, monkeypatch) -> None:
    import os

    (tmp_path / "ok.txt").write_bytes(b"ok")
    bloqueado = tmp_path / "bloq"
    bloqueado.mkdir()
    (bloqueado / "x.txt").write_bytes(b"x")

    real_scandir = os.scandir

    def scandir_com_falha(path, *a, **k):
        if os.path.basename(os.fspath(path)) == "bloq":
            raise PermissionError("EACCES simulado")
        return real_scandir(path, *a, **k)

    monkeypatch.setattr(os, "scandir", scandir_com_falha)

    target = LocalDirectoryTarget(tmp_path)
    items = list(LocalArtifactSource().iter_artifacts(target))

    gaps = [i for i in items if isinstance(i, InventoryGap)]
    assert any(g.path.relative == "bloq" and g.reason == "unreadable_dir" for g in gaps)
    arts = [i for i in items if isinstance(i, Artifact)]
    assert "ok.txt" in {a.path.relative for a in arts}  # resto continua


def test_root_ilegivel_falha_o_target(tmp_path, monkeypatch) -> None:
    import os

    import pytest

    from wirs.domain import TargetError

    target = LocalDirectoryTarget(tmp_path)  # root existe de verdade

    def stat_negado(*a, **k):
        raise PermissionError("EACCES simulado no root")

    monkeypatch.setattr(os, "stat", stat_negado)

    with pytest.raises(TargetError):
        list(LocalArtifactSource().iter_artifacts(target))
