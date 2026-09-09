"""WordPress zone classifier (WIRS-061, spec 6.2)."""

from __future__ import annotations

from wirs.adapters.wordpress.zones import WordPressZone, classify


def test_core_e_plugin() -> None:
    assert classify("wp-admin/admin.php") is WordPressZone.CORE_PROTECTED
    assert classify("wp-includes/version.php") is WordPressZone.CORE_PROTECTED
    assert classify("wp-content/plugins/akismet/akismet.php") is WordPressZone.PLUGINS


def test_todas_as_zonas() -> None:

    casos = [
        ("index.php", WordPressZone.CORE_PROTECTED),  # oficial da raiz
        ("wp-login.php", WordPressZone.CORE_PROTECTED),
        ("xmlrpc.php", WordPressZone.CORE_PROTECTED),
        ("wp-config.php", WordPressZone.ROOT_SPECIAL),
        (".htaccess", WordPressZone.ROOT_SPECIAL),
        (".user.ini", WordPressZone.ROOT_SPECIAL),
        ("php.ini", WordPressZone.ROOT_SPECIAL),
        ("backup.zip", WordPressZone.ROOT_SPECIAL),  # raiz desconhecida: sensível
        ("wp-content/themes/twentytwenty/style.css", WordPressZone.THEMES),
        ("wp-content/mu-plugins/loader.php", WordPressZone.MU_PLUGINS),
        ("wp-content/uploads/2026/foto.jpg", WordPressZone.UPLOADS),
        ("wp-content/cache/a.html", WordPressZone.CACHE),
        ("wp-content/upgrade/x/y.php", WordPressZone.UPGRADE),
        ("wp-content/custom/z.php", WordPressZone.OTHER),
        ("wp-content", WordPressZone.OTHER),
        ("qualquer/outro.php", WordPressZone.OTHER),
    ]
    for relativo, esperado in casos:
        assert classify(relativo) is esperado, relativo
