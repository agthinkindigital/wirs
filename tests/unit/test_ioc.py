"""IOC schema (WIRS-050)."""

from __future__ import annotations

import pytest

from wirs.domain import IOC, IOCKind


def test_literal_e_sha256() -> None:
    lit = IOC(kind=IOCKind.LITERAL, value="eval(base64_decode(")
    assert lit.value == "eval(base64_decode("
    assert lit.id.startswith("ioc_")

    h = IOC(
        kind=IOCKind.SHA256,
        value="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    assert h.value == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    with pytest.raises(ValueError, match="SHA-256"):
        IOC(kind=IOCKind.SHA256, value="zzz")
    with pytest.raises(ValueError, match="vazio"):
        IOC(kind=IOCKind.LITERAL, value="")


def test_domain_url_path_normalizados() -> None:
    assert IOC(kind=IOCKind.DOMAIN, value="EVIL.EXAMPLE.COM.").value == "evil.example.com"
    with pytest.raises(ValueError, match="inválido"):
        IOC(kind=IOCKind.DOMAIN, value="não é domain!!")
    with pytest.raises(ValueError, match="vazio"):
        IOC(kind=IOCKind.URL_FRAGMENT, value="")
    with pytest.raises(ValueError, match="vazio"):
        IOC(kind=IOCKind.PATH_FRAGMENT, value="")

    frag = IOC(kind=IOCKind.URL_FRAGMENT, value="/wp-content/uploads/x.php?y=1")
    assert frag.value == "/wp-content/uploads/x.php?y=1"


def test_id_estavel_e_round_trip() -> None:
    a = IOC(kind=IOCKind.LITERAL, value="abc", label="nota")
    assert a.id == IOC(kind=IOCKind.LITERAL, value="abc", label="outra").id  # label fora do ID
    restaurado = IOC.from_dict(a.to_dict())
    assert restaurado == a
