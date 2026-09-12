"""Assinatura HMAC-SHA256 de manifests (WIRS-046). Só stdlib.

Formato: arquivo destacado `<manifest>.sig` com o hex do HMAC-SHA256 sobre os
bytes exatos do manifest. Chave sempre via arquivo (--key-file), nunca arg
(spec 19.8: secrets não vão para linha de comando/histórico).
"""

from __future__ import annotations

import hashlib
import hmac
from pathlib import Path


class SignatureMissing(ValueError):
    """Manifest tem .sig esperado mas o arquivo não existe."""


class SignatureInvalid(ValueError):
    """Assinatura presente mas não confere."""


class SignatureNotChecked(ValueError):
    """Há .sig mas nenhuma chave foi fornecida para verificar."""


def sig_path(manifest_path: Path) -> Path:
    return Path(str(manifest_path) + ".sig")


def sign_manifest(manifest_path: Path, key: bytes) -> Path:
    """Assina e grava o .sig. Chave vazia é rejeitada."""
    if not key:
        raise ValueError("chave vazia não assina")
    dest = sig_path(manifest_path)
    try:
        content = Path(manifest_path).read_bytes()
    except OSError as e:
        raise ValueError(f"manifest ilegível: {manifest_path} ({e})") from e
    digest = hmac.new(key, content, hashlib.sha256).hexdigest()
    try:
        dest.write_text(digest + "\n", encoding="utf-8")
    except OSError as e:
        raise ValueError(f"não consegui gravar {dest} ({e})") from e
    return dest


def check_signature(manifest_path: Path, key: bytes) -> None:
    """Verifica. Levanta SignatureMissing/SignatureInvalid."""
    manifest_path = Path(manifest_path)
    dest = sig_path(manifest_path)
    try:
        expected = dest.read_text(encoding="utf-8").strip()
    except OSError as e:
        raise SignatureMissing(f"sem assinatura: {dest} ({e})") from e
    try:
        content = manifest_path.read_bytes()
    except OSError as e:
        raise ValueError(f"manifest ilegível: {manifest_path} ({e})") from e
    actual = hmac.new(key, content, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise SignatureInvalid(f"assinatura não confere: {manifest_path}")
