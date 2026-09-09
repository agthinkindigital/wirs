"""Secret redaction na fronteira de coleta (WIRS-092)."""

from __future__ import annotations

from wirs.reporting.redaction import redact_text

DB_PASSWORD = "define( 'DB_PASSWORD', 'sup3r-s3cr3t' );"  # noqa: S105 — fake de fixture
PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\nMIIBOgIBAAJBAKqu\n-----END RSA PRIVATE KEY-----"
LEGIT = "sha256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 art_abc v6.5.2"


def test_db_password_e_private_key_somem() -> None:
    redigido = redact_text(f"{DB_PASSWORD}\n{PRIVATE_KEY}\n{LEGIT}")

    assert "sup3r-s3cr3t" not in redigido
    assert "MIIBOgIBAAJBAKqu" not in redigido
    assert "[REDACTED_SECRET]" in redigido
    assert "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" in redigido
    assert "art_abc" in redigido and "6.5.2" in redigido


def test_tokens_e_atribuicoes() -> None:
    redigido = redact_text(
        "Authorization: Bearer abcDEF123._-x\n"
        "aws_key = AKIAIOSFODNN7EXAMPLE\n"
        "api_key: 12345-secret\n"
        "user=admin password=hunter2\n"
    )

    assert "abcDEF123._-x" not in redigido
    assert "AKIAIOSFODNN7EXAMPLE" not in redigido
    assert "12345-secret" not in redigido
    assert "hunter2" not in redigido
    assert "admin" in redigido  # usuário não é secret
    assert redigido.count("[REDACTED_SECRET]") == 4


def test_mapping_recursivo_bytes_e_default() -> None:
    from wirs.reporting import STORE_RAW_CONTENT
    from wirs.reporting.redaction import redact_mapping

    assert STORE_RAW_CONTENT is False

    limpo = redact_mapping(
        {
            "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "cfg": {"pwd": "s3nha"},
            "raw": b"token=abc123",
            "n": 42,
        }
    )
    assert limpo["hash"].startswith("e3b0c442")
    assert limpo["cfg"] == {"pwd": "[REDACTED_SECRET]"}
    assert limpo["raw"] == b"[REDACTED_SECRET]"
    assert limpo["n"] == 42
