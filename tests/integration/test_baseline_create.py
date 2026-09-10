"""baseline create de diretório (WIRS-042)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

from wirs.cli.app import app
from wirs.domain import BaselineManifest

runner = CliRunner()


def _componente(tmp_path: Path) -> Path:
    root = tmp_path / "limpo"
    (root / "sub").mkdir(parents=True)
    (root / "index.php").write_bytes(b"<?php // limpo\n")
    (root / "sub" / "readme.txt").write_bytes(b"oi\n")
    return root


def test_create_gera_manifest_com_sha256() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        root = _componente(tmp_path)
        saida = tmp_path / "demo.json"

        result = runner.invoke(
            app, ["baseline", "create", str(root), "--name", "demo", "--output", str(saida)]
        )

        assert result.exit_code == 0, result.output
        manifest = BaselineManifest.from_dict(json.loads(saida.read_text(encoding="utf-8")))
        assert manifest.component_id == "demo"
        assert manifest.files["index.php"] == hashlib.sha256(b"<?php // limpo\n").hexdigest()
        assert manifest.files["sub/readme.txt"] == hashlib.sha256(b"oi\n").hexdigest()
        assert manifest.package_hash != ""


def test_symlink_para_fora_nao_entra_e_round_trip_verifica() -> None:
    import os
    import tempfile

    from wirs.domain import IntegrityState, compare_baseline

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        root = _componente(tmp_path)
        fora = tmp_path / "segredo.txt"
        fora.write_bytes(b"topsecret\n")
        try:
            os.symlink(fora, root / "atalho.txt")
        except OSError:
            import pytest

            pytest.skip("symlink exige privilégio neste host")
        saida = tmp_path / "demo.json"

        result = runner.invoke(
            app, ["baseline", "create", str(root), "--name", "demo", "--output", str(saida)]
        )

        assert result.exit_code == 0, result.output
        manifest = BaselineManifest.from_dict(json.loads(saida.read_text(encoding="utf-8")))
        assert "atalho.txt" not in manifest.files
        assert len(manifest.files) == 2

        atual = {
            path: hashlib.sha256((root / path).read_bytes()).hexdigest()
            for path in ("index.php", "sub/readme.txt")
        }
        estados = {r.state for r in compare_baseline(manifest, atual)}
        assert estados == {IntegrityState.MATCH}
