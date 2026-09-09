"""Ataques contra o redactor: o secret NÃO pode sobreviver em nenhuma forma."""

from __future__ import annotations

from wirs.reporting.redaction import redact_text

SEGREDO = "s3cr3t0-f1n4l"


def _limpo(secret: str, texto: str) -> None:
    assert secret not in redact_text(texto), texto


def test_variacoes_de_aspas_e_case() -> None:
    _limpo(SEGREDO, f'define( "DB_PASSWORD" , "{SEGREDO}" );')
    _limpo(SEGREDO, f"Password={SEGREDO}")
    _limpo(SEGREDO, f"API-KEY: {SEGREDO}")
    _limpo(SEGREDO, f"token = '{SEGREDO}';")


def test_chave_multilinha_e_quebrada() -> None:
    bloco = f"-----BEGIN PRIVATE KEY-----\n{SEGREDO}\n-----END PRIVATE KEY-----"
    _limpo(SEGREDO, f"cabeçalho\n{bloco}\nrodapé")


def test_legitimo_sobrevive_ao_lado() -> None:
    texto = (
        "id=fnd_556bae7c4eabcc31 hash="
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 "
        f"password={SEGREDO}"
    )
    out = redact_text(texto)
    assert SEGREDO not in out
    assert "fnd_556bae7c4eabcc31" in out
    assert "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" in out
