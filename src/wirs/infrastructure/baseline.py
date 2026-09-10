"""BaselineBuilder: manifest a partir de diretório limpo (WIRS-042).

Só lê: inventory sem follow de symlink + hash SHA-256 via ArtifactReader.
Symlinks, especiais e gaps nunca entram no manifest (não são conteúdo
verificável por hash). Nenhum script do package é executado por construção.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from wirs.domain import ArtifactKind, BaselineManifest, BaselineTrust, LocalDirectoryTarget
from wirs.infrastructure.archive import extract_zip_safely
from wirs.infrastructure.filesystem import InventoryGap, LocalArtifactSource
from wirs.infrastructure.hashing import HashService
from wirs.infrastructure.reader import ArtifactReader, ReadBudget


class BaselineBuilder:
    def __init__(
        self,
        source: LocalArtifactSource | None = None,
        reader: ArtifactReader | None = None,
        budget: ReadBudget | None = None,
    ) -> None:
        self._source = source or LocalArtifactSource()
        reader = reader or ArtifactReader()
        self._hashes = HashService(reader)
        self._budget = budget or ReadBudget(max_bytes=1 << 30)

    def build_archive(self, archive: Path, *, component_id: str, version: str) -> BaselineManifest:
        """Manifest de ZIP confiável: extrai isolado e identifica pelo hash do ZIP."""
        import tempfile

        package_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="wirs-baseline-") as tmp:
            extracted = extract_zip_safely(archive, Path(tmp) / "pkg")
            manifest = self.build(extracted, component_id=component_id, version=version)
        return BaselineManifest(
            component_id=manifest.component_id,
            version=manifest.version,
            source=f"archive:{archive.resolve()}",
            trust=manifest.trust,
            files=dict(manifest.files),
            package_hash=package_hash,
            created_at=manifest.created_at,
        )

    def build(self, root: Path, *, component_id: str, version: str) -> BaselineManifest:
        target = LocalDirectoryTarget(root)
        files: dict[str, str] = {}
        for item in self._source.iter_artifacts(target):
            if isinstance(item, InventoryGap) or item.kind is not ArtifactKind.FILE:
                continue
            rel = item.path.relative
            if not rel:
                continue
            files[rel] = self._hashes.digest(item, self._budget)
        listing = "".join(f"{path}:{files[path]}\n" for path in sorted(files))
        package_hash = hashlib.sha256(listing.encode("utf-8")).hexdigest()
        return BaselineManifest(
            component_id=component_id,
            version=version,
            source=f"local:{target.root}",
            trust=BaselineTrust.TRUSTED_OPERATOR,
            files=files,
            package_hash=package_hash,
            created_at=datetime.now(UTC),
        )
