"""SafePath: path relativo canônico confinado ao root (WIRS-011, ADR-008)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from wirs.domain import SafePath, SecurityBoundaryError


def test_path_benigno_preservado(tmp_path) -> None:
    sp = SafePath(tmp_path, "wp-content/uploads/foto.jpg")

    assert sp.relative == "wp-content/uploads/foto.jpg"
    assert sp.full == tmp_path.resolve() / "wp-content/uploads/foto.jpg"
    assert str(sp) == "wp-content/uploads/foto.jpg"


@pytest.mark.parametrize(
    "hostil",
    [
        "..",
        "../..",
        "a/../../x",
        "/etc/passwd",
        "/",
        "C:\\Windows\\x",
        "C:/Windows/x",
        "\\\\server\\share",
        "..\\..\\x",
        "a\\..\\..\\x",
    ],
)
def test_escape_do_root_rejeitado(tmp_path, hostil: str) -> None:
    with pytest.raises(SecurityBoundaryError):
        SafePath(tmp_path, hostil)


def test_dotdot_interno_resolvido_sem_escapar(tmp_path) -> None:
    sp = SafePath(tmp_path, "a/b/../c.php")
    assert sp.relative == "a/c.php"
    assert sp.full == tmp_path.resolve() / "a/c.php"


def test_dot_e_dotdot_que_voltam_ao_root(tmp_path) -> None:
    assert SafePath(tmp_path, ".").relative == ""
    assert SafePath(tmp_path, "a/..").relative == ""
    assert SafePath(tmp_path, "").relative == ""
    assert SafePath(tmp_path, ".").full == tmp_path.resolve()


def test_backslash_vira_separador(tmp_path) -> None:
    sp = SafePath(tmp_path, "a\\b\\c.php")
    assert sp.relative == "a/b/c.php"


def test_nul_rejeitado(tmp_path) -> None:
    with pytest.raises(SecurityBoundaryError):
        SafePath(tmp_path, "a\x00b.php")


def test_unicode_normalizado_nfc(tmp_path) -> None:
    sp = SafePath(tmp_path, "cafe\u0301.php")  # e + acento combinante
    assert sp.relative == "caf\u00e9.php"


def test_trailing_slash_removido(tmp_path) -> None:
    assert SafePath(tmp_path, "a/b/").relative == "a/b"


@pytest.mark.parametrize("cru", ["::", "a/C:x", "NUL.txt:evil", "..."])
def test_segmentos_que_quebram_joinpath_ficam_contidos(tmp_path, cru: str) -> None:
    sp = SafePath(tmp_path, cru)
    assert sp.full.parts[: len(tmp_path.resolve().parts)] == tmp_path.resolve().parts


HOSTILE_ALPHABET = st.sampled_from(sorted(set("ab/\\.: \x00éC" + "\udcff")))


@given(st.text(alphabet=HOSTILE_ALPHABET, max_size=24))
def test_confinamento_invariante(raw: str) -> None:
    # SafePath é lexical (não toca o filesystem): root sintético basta.
    root = Path(tempfile.gettempdir())
    try:
        sp = SafePath(root, raw)
    except SecurityBoundaryError:
        return
    segs = sp.relative.split("/") if sp.relative else []
    assert ".." not in segs
    assert not sp.relative.startswith(("/", "C:"))
    assert sp.full.parts[: len(root.parts)] == root.parts
