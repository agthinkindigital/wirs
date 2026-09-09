"""Artifact: objeto lógico analisável (spec 3.2). Só stdlib, nenhum I/O aqui."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from wirs.domain.safepath import SafePath


class ArtifactKind(Enum):
    FILE = "file"
    DIR = "dir"
    SYMLINK = "symlink"
    SPECIAL = "special"


def _artifact_id(kind: ArtifactKind, path: SafePath) -> str:
    digest = hashlib.sha256(f"{kind.value}|{path.root}|{path.relative}".encode()).hexdigest()[:16]
    return f"art_{digest}"


@dataclass(frozen=True)
class ArtifactMetadata:
    size: int | None = None
    mode: int | None = None
    uid: int | None = None
    gid: int | None = None
    ino: int | None = None
    dev: int | None = None
    mtime_ns: int | None = None
    ctime_ns: int | None = None
    extra: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True)
class Artifact:
    kind: ArtifactKind
    path: SafePath
    metadata: ArtifactMetadata = field(default_factory=ArtifactMetadata)
    symlink_target: str | None = None
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", _artifact_id(self.kind, self.path))

    @classmethod
    def from_stat(
        cls,
        kind: ArtifactKind,
        path: SafePath,
        st: os.stat_result,
        symlink_target: str | None = None,
    ) -> Artifact:
        """Constrói a partir de um stat JÁ coletado — nenhum I/O aqui dentro."""
        return cls(
            kind=kind,
            path=path,
            metadata=ArtifactMetadata(
                size=st.st_size,
                mode=st.st_mode,
                uid=getattr(st, "st_uid", None),
                gid=getattr(st, "st_gid", None),
                ino=st.st_ino,
                dev=st.st_dev,
                mtime_ns=st.st_mtime_ns,
                ctime_ns=st.st_ctime_ns,
            ),
            symlink_target=symlink_target,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "root": str(self.path.root),
            "relative": self.path.relative,
            "symlink_target": self.symlink_target,
            "metadata": {
                "size": self.metadata.size,
                "mode": self.metadata.mode,
                "uid": self.metadata.uid,
                "gid": self.metadata.gid,
                "ino": self.metadata.ino,
                "dev": self.metadata.dev,
                "mtime_ns": self.metadata.mtime_ns,
                "ctime_ns": self.metadata.ctime_ns,
                "extra": dict(self.metadata.extra),
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Artifact:
        meta = data.get("metadata", {})
        return cls(
            kind=ArtifactKind(data["kind"]),
            path=SafePath(Path(data["root"]), str(data["relative"])),
            metadata=ArtifactMetadata(
                size=meta.get("size"),
                mode=meta.get("mode"),
                uid=meta.get("uid"),
                gid=meta.get("gid"),
                ino=meta.get("ino"),
                dev=meta.get("dev"),
                mtime_ns=meta.get("mtime_ns"),
                ctime_ns=meta.get("ctime_ns"),
                extra=meta.get("extra", {}),
            ),
            symlink_target=data.get("symlink_target"),
            id=str(data.get("id", "")),
        )
