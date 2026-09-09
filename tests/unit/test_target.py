"""Target model (WIRS-010, spec 3.1)."""

from __future__ import annotations

import dataclasses

import pytest

from wirs.domain import LocalDirectoryTarget, TargetError


def test_root_inexistente_vira_target_error(tmp_path) -> None:
    with pytest.raises(TargetError):
        LocalDirectoryTarget(tmp_path / "nao-existe")


def test_arquivo_como_root_vira_target_error(tmp_path) -> None:
    arquivo = tmp_path / "f.txt"
    arquivo.write_text("x", encoding="utf-8")
    with pytest.raises(TargetError):
        LocalDirectoryTarget(arquivo)


def test_root_normalizado(tmp_path) -> None:
    com_barra = LocalDirectoryTarget(str(tmp_path) + "/")
    sem_barra = LocalDirectoryTarget(tmp_path)
    assert com_barra.root == sem_barra.root == tmp_path.resolve()
    assert com_barra.id == sem_barra.id


def test_local_directory_target_valido(tmp_path) -> None:
    target = LocalDirectoryTarget(tmp_path)

    assert target.root == tmp_path.resolve()
    assert target.id == LocalDirectoryTarget(tmp_path).id  # determinístico
    assert target.id.startswith("tgt_")


def test_metadata_imutavel(tmp_path) -> None:
    target = LocalDirectoryTarget(tmp_path, metadata={"origem": "snapshot"})
    assert target.metadata["origem"] == "snapshot"

    with pytest.raises(TypeError):
        target.metadata["origem"] = "outra"  # type: ignore[index]

    with pytest.raises(dataclasses.FrozenInstanceError):
        target.root = tmp_path  # type: ignore[misc]
