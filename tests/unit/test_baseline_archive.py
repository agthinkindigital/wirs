"""Baseline de archive/ZIP (WIRS-043)."""

from __future__ import annotations

import hashlib
import tempfile
import zipfile
from pathlib import Path

from wirs.infrastructure.baseline import BaselineBuilder


def _zip_de(targes: dict[str, bytes]) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp.close()
    with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as zf:
        for nome, conteudo in targes.items():
            zf.writestr(nome, conteudo)
    return Path(tmp.name)


def test_zip_gera_manifest_equivalente_ao_diretorio() -> None:
    zpath = _zip_de({"index.php": b"<?php // limpo\n", "sub/readme.txt": b"oi\n"})
    esperado_zip = hashlib.sha256(zpath.read_bytes()).hexdigest()
    try:
        manifest = BaselineBuilder().build_archive(zpath, component_id="demo", version="1.0")
    finally:
        zpath.unlink(missing_ok=True)

    assert manifest.files["index.php"] == hashlib.sha256(b"<?php // limpo\n").hexdigest()
    assert manifest.files["sub/readme.txt"] == hashlib.sha256(b"oi\n").hexdigest()
    assert manifest.package_hash == esperado_zip


def test_equivalente_ao_diretorio_extraido() -> None:
    import tempfile

    from wirs.infrastructure.archive import extract_zip_safely

    zpath = _zip_de({"index.php": b"<?php // limpo\n", "sub/readme.txt": b"oi\n"})
    try:
        via_zip = BaselineBuilder().build_archive(zpath, component_id="d", version="1")
        with tempfile.TemporaryDirectory() as tmp:
            extraido = extract_zip_safely(zpath, Path(tmp) / "pkg")
            via_dir = BaselineBuilder().build(extraido, component_id="d", version="1")
    finally:
        zpath.unlink(missing_ok=True)

    assert via_zip.files == via_dir.files
