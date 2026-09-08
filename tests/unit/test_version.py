"""Smoke do scaffold (WIRS-001): pacote importável com versão."""

from wirs import __version__


def test_version_existe() -> None:
    assert isinstance(__version__, str)
    assert __version__ != ""
