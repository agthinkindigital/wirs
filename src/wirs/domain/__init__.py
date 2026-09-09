"""Modelo de domínio genérico (stdlib + value objects apenas).

Proibido importar wordpress, yara, wordfence, rich, mysql, typer a partir daqui.
"""

from wirs.domain.errors import TargetError, WirsError
from wirs.domain.target import LocalDirectoryTarget, Target, TargetKind

__all__ = [
    "LocalDirectoryTarget",
    "Target",
    "TargetError",
    "TargetKind",
    "WirsError",
]
