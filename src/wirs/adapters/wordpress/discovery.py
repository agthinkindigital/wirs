"""Discovery WordPress por combinação de sinais — sem banco, sem ler conteúdo.

Cada sinal é checado com `lstat` (nunca segue symlink, nunca abre arquivo):
só interessa *existir com o tipo certo*. Nenhum sinal sozinho decide — um
diretório chamado `wp-content` não faz um WordPress.
"""

from __future__ import annotations

import os
import stat as statmod

from wirs.adapters.wordpress.zones import classify as _classify
from wirs.domain import Target
from wirs.ports import PlatformDiscovery

# (path relativo, espera_arquivo?) — arquivos e dirs têm peso igual na contagem.
SIGNALS: tuple[tuple[str, bool], ...] = (
    ("wp-includes/version.php", True),
    ("wp-admin", False),
    ("wp-content", False),
    ("wp-config.php", True),
)

MIN_SIGNALS = 2


def _present(root: str, relative: str, want_file: bool) -> bool:
    try:
        st = os.lstat(os.path.join(root, *relative.split("/")))
    except OSError:
        return False
    if want_file:
        return statmod.S_ISREG(st.st_mode) and not statmod.S_ISLNK(st.st_mode)
    return statmod.S_ISDIR(st.st_mode) and not statmod.S_ISLNK(st.st_mode)


class WordPressAdapter:
    id = "wordpress"

    def discover(self, target: Target) -> PlatformDiscovery | None:
        root = os.fspath(target.root)
        hit = [rel for rel, want_file in SIGNALS if _present(root, rel, want_file)]
        if len(hit) < MIN_SIGNALS:
            return None
        return PlatformDiscovery(platform_id=self.id, signals=tuple(hit))

    def classify(self, relative: str) -> str:
        return _classify(relative).value
