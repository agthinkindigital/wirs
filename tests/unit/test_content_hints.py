"""Content hints no passo único de leitura (WIRS-054)."""

from __future__ import annotations

from wirs.detectors.content import ContentHints, extract_hints


def test_hints_php_em_um_passo() -> None:
    hints = extract_hints(b"<?php echo 1;")

    assert isinstance(hints, ContentHints)
    assert hints.is_text is True
    assert hints.executable is True


def test_binario_utf8_e_vazio() -> None:
    jpeg = extract_hints(b"\xff\xd8\xff\xe0" + b"\x00" * 10)
    assert jpeg.is_text is False and jpeg.executable is False

    latin = extract_hints("café".encode("latin-1"))  # não-UTF-8 válido
    assert latin.is_text is False

    vazio = extract_hints(b"")
    assert vazio.is_text is True and vazio.executable is False


def test_executable_reutiliza_detector() -> None:
    from wirs.detectors import executable as exec_module

    amostras = [b"<?php x", b"<?= y", b"hello", b"\x00\x01", b"<script>z</script>"]
    for amostra in amostras:
        assert extract_hints(amostra).executable is exec_module.looks_executable(amostra)
