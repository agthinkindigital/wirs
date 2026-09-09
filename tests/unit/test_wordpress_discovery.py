"""WordPress discovery (WIRS-060): combinação de sinais, sem banco."""

from __future__ import annotations

from wirs.adapters.wordpress.discovery import WordPressAdapter
from wirs.domain import LocalDirectoryTarget


def _wp_like(root) -> None:
    (root / "wp-includes").mkdir()
    (root / "wp-includes" / "version.php").write_bytes(b"<?php // v")
    (root / "wp-admin").mkdir()
    (root / "wp-content").mkdir()
    (root / "wp-config.php").write_bytes(b"<?php // cfg")


def test_arvore_wordpress_descoberta(tmp_path) -> None:
    _wp_like(tmp_path)
    found = WordPressAdapter().discover(LocalDirectoryTarget(tmp_path))

    assert found is not None
    assert found.platform_id == "wordpress"
    assert set(found.signals) >= {
        "wp-includes/version.php",
        "wp-admin",
        "wp-content",
        "wp-config.php",
    }


def test_arvore_generica_nao_descoberta(tmp_path) -> None:
    (tmp_path / "index.html").write_bytes(b"<h1>oi</h1>")
    assert WordPressAdapter().discover(LocalDirectoryTarget(tmp_path)) is None


def test_sinal_unico_nao_decide(tmp_path) -> None:
    (tmp_path / "wp-content").mkdir()  # só um diretório com nome famoso
    assert WordPressAdapter().discover(LocalDirectoryTarget(tmp_path)) is None

    (tmp_path / "wp-config.php").write_bytes(b"<?php // cfg")
    found = WordPressAdapter().discover(LocalDirectoryTarget(tmp_path))
    assert found is not None  # 2 sinais: limiar mínimo atingido
    assert set(found.signals) == {"wp-content", "wp-config.php"}


def test_adapter_implementa_protocolo() -> None:
    from wirs.ports import PlatformAdapter

    adapter = WordPressAdapter()
    assert isinstance(adapter, PlatformAdapter)
    assert adapter.id == "wordpress"
