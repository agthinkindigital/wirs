"""Streaming literal scanner (WIRS-051): bytes, fronteira de chunk, cap, contexto."""

from __future__ import annotations

from wirs.detectors.ioc_scanner import scan_bytes, scan_stream
from wirs.domain import IOC, IOCKind

# NOTA ANTI-AV: literais que formariam assinatura viva de webshell são
# fragmentados com + explícito (o formatador jamais os junta). Em runtime o
# valor é idêntico, mas o arquivo nunca contém o padrão contíguo. O Defender
# já quarantinou uma versão anterior deste arquivo. Ver SECURITY.md.
EV = "ev" + "al("


def test_literal_com_offset_e_contexto() -> None:
    ioc = IOC(kind=IOCKind.LITERAL, value=EV)
    data = b"<?php " + EV.encode() + b"$_GET[x]); ?>"

    result = scan_bytes(data, [ioc])

    assert result.total_counts[ioc.id] == 1
    (match,) = result.matches
    assert match.ioc_id == ioc.id
    assert match.offset == 6
    assert match.context == data
    assert result.truncated is False


def test_ioc_cruzando_fronteira_de_chunk() -> None:
    ioc = IOC(kind=IOCKind.LITERAL, value="ABCDEF")
    chunks = [b"xxAB", b"CDEFyy", b"zz"]

    result = scan_stream(iter(chunks), [ioc])

    assert result.total_counts[ioc.id] == 1
    (match,) = result.matches
    assert match.offset == 2  # absoluto no stream, não no chunk


def test_fronteira_sem_duplicar_nem_perder() -> None:
    ioc = IOC(kind=IOCKind.LITERAL, value="AB")
    chunks = [b"AB", b"AB", b"AB"]  # um por chunk + nenhum cruzado

    result = scan_stream(iter(chunks), [ioc])

    assert result.total_counts[ioc.id] == 3
    assert sorted(m.offset for m in result.matches) == [0, 2, 4]


def test_cap_preserva_count_e_trunca() -> None:
    ioc = IOC(kind=IOCKind.LITERAL, value="X")
    data = b"X" * 250

    result = scan_bytes(data, [ioc], occurrence_cap=100)

    assert result.total_counts[ioc.id] == 250
    assert len(result.matches) == 100
    assert result.truncated is True


def test_binario_sem_decode_e_sha_ignorado() -> None:
    ioc = IOC(kind=IOCKind.LITERAL, value="ZZ")
    blob = b"\xff\xd8ZZ\x00\x01\x02" + b"y" * 5000
    sha = IOC(
        kind=IOCKind.SHA256,
        value="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )

    result = scan_bytes(blob, [ioc, sha])

    assert result.total_counts[ioc.id] == 1
    (match,) = result.matches
    assert match.context == blob[: 2 + 2 + 64]  # janela limitada, bytes crus
    assert sha.id not in result.total_counts  # sha256 não é literal: orquestrador compara
