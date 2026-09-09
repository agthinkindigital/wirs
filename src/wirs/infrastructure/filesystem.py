"""Inventory de filesystem local: streaming, sem follow de symlink, sem I/O além de stat.

- Symlink é registrado (com destino de `readlink`, que não segue) e nunca atravessado:
  loops e escapes são impossíveis por construção.
- Arquivo especial (FIFO/socket/device) vira `SPECIAL` e nunca é aberto.
- Erro por entrada vira `InventoryGap` (scan continua); root ilegível vira `TargetError`.
- Ordem determinística (entradas ordenadas por nome em cada diretório).
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from wirs.domain import Artifact, ArtifactKind, SafePath, Target, TargetError


@dataclass(frozen=True)
class InventoryGap:
    """Entrada que não pôde ser caracterizada (scan continua; vira Coverage)."""

    path: SafePath
    reason: str  # "stat_failed" | "unreadable_dir" | "readlink_failed"


class LocalArtifactSource:
    def iter_artifacts(self, target: Target) -> Iterator[Artifact | InventoryGap]:
        try:
            root_stat = os.stat(target.root, follow_symlinks=False)
        except OSError as e:
            raise TargetError(f"root ilegível: {target.root} ({e})") from e
        yield Artifact.from_stat(
            kind=ArtifactKind.DIR,
            path=SafePath(target.root, ""),
            st=root_stat,
        )
        stack: list[Path] = [target.root]
        while stack:
            current = stack.pop()
            try:
                with os.scandir(current) as it:
                    entries = sorted(it, key=lambda e: e.name)
            except OSError:
                rel = os.path.relpath(current, target.root).replace(os.sep, "/")
                yield InventoryGap(path=SafePath(target.root, rel), reason="unreadable_dir")
                continue
            subdirs: list[Path] = []
            for entry in entries:
                item, descend = self._one(target, entry)
                yield item
                if descend is not None:
                    subdirs.append(descend)
            stack.extend(reversed(subdirs))

    def _one(
        self, target: Target, entry: os.DirEntry[str]
    ) -> tuple[Artifact | InventoryGap, Path | None]:
        """Caracteriza uma entrada; segundo elemento indica onde descer (só DIR real)."""
        rel = os.path.relpath(entry.path, target.root).replace(os.sep, "/")
        path = SafePath(target.root, rel)
        try:
            is_link = entry.is_symlink()
            st = entry.stat(follow_symlinks=False)
        except OSError:
            return InventoryGap(path=path, reason="stat_failed"), None
        if is_link:
            try:
                dest = os.readlink(entry.path)
            except OSError:
                return InventoryGap(path=path, reason="readlink_failed"), None
            meta = Artifact.from_stat(ArtifactKind.SYMLINK, path, st).metadata
            return (
                Artifact(kind=ArtifactKind.SYMLINK, path=path, symlink_target=dest, metadata=meta),
                None,
            )
        if entry.is_file(follow_symlinks=False):
            return Artifact.from_stat(ArtifactKind.FILE, path, st), None
        if entry.is_dir(follow_symlinks=False):
            return Artifact.from_stat(ArtifactKind.DIR, path, st), Path(entry.path)
        return Artifact.from_stat(ArtifactKind.SPECIAL, path, st), None
