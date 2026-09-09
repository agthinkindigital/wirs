"""Target: o que está sendo analisado (spec 3.1). Só stdlib."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from wirs.domain.errors import TargetError


class TargetKind(Enum):
    LOCAL_DIRECTORY = "local_directory"
    SNAPSHOT_DIRECTORY = "snapshot_directory"
    ARCHIVE = "archive"


def _target_id(kind: TargetKind, root: Path) -> str:
    digest = hashlib.sha256(f"{kind.value}|{root}".encode()).hexdigest()[:16]
    return f"tgt_{digest}"


@dataclass(frozen=True)
class Target:
    kind: TargetKind
    root: Path
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    id: str = ""

    def __post_init__(self) -> None:
        normalized = Path(self.root).expanduser().resolve()
        object.__setattr__(self, "root", normalized)
        if isinstance(self.metadata, dict):
            object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        if not self.id:
            object.__setattr__(self, "id", _target_id(self.kind, normalized))


def LocalDirectoryTarget(root: str | Path, metadata: Mapping[str, Any] | None = None) -> Target:
    """Alvo diretório local: precisa existir e ser diretório (senão, TargetError)."""
    candidate = Path(root).expanduser()
    if not candidate.exists():
        raise TargetError(f"target inexistente: {root}")
    if not candidate.is_dir():
        raise TargetError(f"target não é diretório: {root}")
    return Target(
        kind=TargetKind.LOCAL_DIRECTORY,
        root=candidate,
        metadata=metadata if metadata is not None else {},
    )
