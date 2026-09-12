"""Signed manifests (WIRS-046)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from wirs.cli.app import app
from wirs.infrastructure.baseline import BaselineBuilder

runner = CliRunner()


def _site_com_premium(tmp: Path) -> Path:
    (tmp / "wp-includes").mkdir(parents=True)
    (tmp / "wp-includes" / "version.php").write_bytes(b"<?php\n// v\n")
    destino = tmp / "wp-content" / "plugins" / "premium"
    destino.mkdir(parents=True)
    (destino / "premium.php").write_bytes(b"<?php\n// premium\n")
    return destino


def test_sign_scan_com_chave_e_sem_chave() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        premium = _site_com_premium(tmp_path)
        manifest = BaselineBuilder().build(premium, component_id="premium", version="1.0")
        manifest_path = tmp_path / "premium.json"
        manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")
        chave = tmp_path / "chave.key"
        chave.write_bytes(b"segredo-do-ci-123")
        mapping = tmp_path / "mapping.json"
        mapping.write_text(
            json.dumps({"wp-content/plugins/premium": str(manifest_path)}), encoding="utf-8"
        )

        r_sign = runner.invoke(
            app, ["baseline", "sign", str(manifest_path), "--key-file", str(chave)]
        )
        assert r_sign.exit_code == 0, r_sign.output
        assert (tmp_path / "premium.json.sig").exists()

        com_chave = runner.invoke(
            app,
            [
                "scan",
                str(tmp_path),
                "--baseline",
                str(mapping),
                "--sign-key",
                str(chave),
                "--format",
                "json",
            ],
        )
        assert com_chave.exit_code == 0, com_chave.output
        assert json.loads(com_chave.stdout)["findings"] == []

        sem_chave = runner.invoke(
            app, ["scan", str(tmp_path), "--baseline", str(mapping), "--format", "json"]
        )
        assert sem_chave.exit_code == 0, sem_chave.output
        lacunas = {c["capability"]: c["state"] for c in json.loads(sem_chave.stdout)["coverage"]}
        assert lacunas.get("baseline:plugin:premium") == "partial"


def test_sig_adulterada_rejeita_e_verify_sig() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        premium = _site_com_premium(tmp_path)
        manifest = BaselineBuilder().build(premium, component_id="premium", version="1.0")
        manifest_path = tmp_path / "premium.json"
        manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")
        chave = tmp_path / "chave.key"
        chave.write_bytes(b"segredo-do-ci-123")
        mapping = tmp_path / "mapping.json"
        mapping.write_text(
            json.dumps({"wp-content/plugins/premium": str(manifest_path)}), encoding="utf-8"
        )

        assert (
            runner.invoke(
                app, ["baseline", "sign", str(manifest_path), "--key-file", str(chave)]
            ).exit_code
            == 0
        )
        assert (
            runner.invoke(
                app, ["baseline", "verify-sig", str(manifest_path), "--key-file", str(chave)]
            ).exit_code
            == 0
        )

        # Adultera o manifest depois de assinado: nada passa.
        manifest_path.write_text(json.dumps(manifest.to_dict()) + " ", encoding="utf-8")
        assert (
            runner.invoke(
                app, ["baseline", "verify-sig", str(manifest_path), "--key-file", str(chave)]
            ).exit_code
            == 2
        )
        adulterado = runner.invoke(
            app,
            [
                "scan",
                str(tmp_path),
                "--baseline",
                str(mapping),
                "--sign-key",
                str(chave),
                "--format",
                "json",
            ],
        )
        assert adulterado.exit_code == 0
        estados = {c["capability"]: c["state"] for c in json.loads(adulterado.stdout)["coverage"]}
        assert estados.get("operator-baseline") == "failed"
