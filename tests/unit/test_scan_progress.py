"""Progresso do scan (WIRS-139)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from wirs.application.orchestrator import ProgressEvent, run_scan
from wirs.domain import Artifact, LocalDirectoryTarget
from wirs.infrastructure import ArtifactReader, LocalArtifactSource
from wirs.infrastructure.reader import ReadBudget
from wirs.ports.detection import ProposedFinding


class _Silencioso:
    id = "silencioso"
    wants_stream = False

    def analyze(
        self, artifact: Artifact, zone: str | None, head: bytes, chunks
    ) -> list[ProposedFinding]:
        return []


def test_eventos_em_ordem_com_arquivo_atual() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.php").write_bytes(b"<?php\n// a\n")
        (root / "b.txt").write_bytes(b"oi\n")
        eventos: list[ProgressEvent] = []
        run_scan(
            LocalDirectoryTarget(root),
            profile="soft",
            source=LocalArtifactSource(),
            adapters=[],
            reader=ArtifactReader(),
            budget=ReadBudget(max_bytes=1 << 20),
            detectors=[_Silencioso()],
            integrity=[],
            on_event=eventos.append,
        )

    fases = [e.phase for e in eventos]
    assert fases[0] == "inventory"
    assert "discovery" in fases
    assert "integrity" in fases
    assert fases[-1] == "done"
    detectados = [e.detail for e in eventos if e.phase == "detect"]
    assert sorted(detectados) == ["a.php", "b.txt"]
