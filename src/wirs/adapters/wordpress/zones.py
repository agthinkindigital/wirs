"""Zonas do filesystem WordPress (spec 6.2). Função pura sobre path relativo posix."""

from __future__ import annotations

from enum import Enum


class WordPressZone(Enum):
    CORE_PROTECTED = "wp-core-protected"
    ROOT_SPECIAL = "wp-root-special"
    PLUGINS = "wp-content-plugins"
    THEMES = "wp-content-themes"
    MU_PLUGINS = "wp-content-mu-plugins"
    UPLOADS = "wp-content-uploads"
    CACHE = "wp-content-cache"
    UPGRADE = "wp-content-upgrade"
    OTHER = "wp-content-other"


# Arquivos oficiais da raiz (comparáveis com upstream — lista estável do core).
OFFICIAL_ROOT_FILES = frozenset(
    {
        "index.php",
        "license.txt",
        "readme.html",
        "wp-activate.php",
        "wp-blog-header.php",
        "wp-comments-post.php",
        "wp-config-sample.php",
        "wp-cron.php",
        "wp-links-opml.php",
        "wp-load.php",
        "wp-login.php",
        "wp-mail.php",
        "wp-settings.php",
        "wp-signup.php",
        "wp-trackback.php",
        "xmlrpc.php",
    }
)

# Configuração visível (política/heurística, nunca igualdade com upstream).
ROOT_SPECIAL_FILES = frozenset(
    {
        "wp-config.php",
        ".htaccess",
        ".user.ini",
        "php.ini",
    }
)


def classify(relative: str) -> WordPressZone:
    """Classifica um path relativo posix (compatível com SafePath.relative)."""
    parts = [p for p in relative.strip("/").split("/") if p not in ("", ".")]
    if not parts:
        return WordPressZone.ROOT_SPECIAL  # o próprio root: área sensível
    head = parts[0]
    if head in ("wp-admin", "wp-includes"):
        return WordPressZone.CORE_PROTECTED
    if head == "wp-content":
        second = parts[1] if len(parts) > 1 else ""
        return {
            "plugins": WordPressZone.PLUGINS,
            "themes": WordPressZone.THEMES,
            "mu-plugins": WordPressZone.MU_PLUGINS,
            "uploads": WordPressZone.UPLOADS,
            "cache": WordPressZone.CACHE,
            "upgrade": WordPressZone.UPGRADE,
        }.get(second, WordPressZone.OTHER)
    if len(parts) == 1:
        if head in OFFICIAL_ROOT_FILES:
            return WordPressZone.CORE_PROTECTED
        # Especial conhecido ou desconhecido: raiz é área sensível, merece
        # heurística — nunca igualdade silenciosa com upstream.
        return WordPressZone.ROOT_SPECIAL
    return WordPressZone.OTHER
