"""Ataques contra baseline de ZIP (WIRS-043, security)."""

from __future__ import annotations

import stat
import tempfile
import zipfile
from pathlib import Path

import pytest

from wirs.domain.errors import BudgetExceeded, SecurityBoundaryError
from wirs.infrastructure.archive import extract_zip_safely


def _zip_com(entries: list[tuple[str, bytes, int]]) -> Path:
    """entries: (nome, conteúdo, external_attr)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp.close()
    with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as zf:
        for nome, conteudo, attr in entries:
            info = zipfile.ZipInfo(nome)
            info.external_attr = attr
            zf.writestr(info, conteudo)
    return Path(tmp.name)


def test_zip_slip_nao_escapa_do_destino() -> None:
    zpath = _zip_com([("../../evil.php", b"x", 0), ("ok.php", b"y", 0)])
    try:
        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(SecurityBoundaryError, match="fora do destino"):
                extract_zip_safely(zpath, Path(tmp) / "pkg")
    finally:
        zpath.unlink(missing_ok=True)


def test_symlink_entry_nao_e_materializada() -> None:
    link_attr = (stat.S_IFLNK | 0o777) << 16
    zpath = _zip_com([("link", b"/etc/passwd", link_attr), ("ok.php", b"y", 0)])
    try:
        with tempfile.TemporaryDirectory() as tmp:
            dest = extract_zip_safely(zpath, Path(tmp) / "pkg")
            assert not (dest / "link").exists() and not (dest / "link").is_symlink()
            assert (dest / "ok.php").read_bytes() == b"y"
    finally:
        zpath.unlink(missing_ok=True)


def test_bomba_de_expansao_respeita_limite() -> None:
    zpath = _zip_com([("grande.bin", b"0" * 1000, 0)])
    try:
        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(BudgetExceeded):
                extract_zip_safely(zpath, Path(tmp) / "pkg", max_bytes=100)
    finally:
        zpath.unlink(missing_ok=True)
