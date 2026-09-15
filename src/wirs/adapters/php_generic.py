"""Adapter e policy para aplicações PHP locais, sem semântica WordPress."""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from pathlib import Path

from wirs.detectors.executable import looks_executable
from wirs.domain import Artifact, ArtifactKind, Confidence, ConfidenceClass, Severity, Target
from wirs.ports import Detector, PlatformDiscovery, ProposedFinding

PHP_EXTENSIONS = frozenset({".php", ".phtml", ".php3", ".php4", ".php5", ".phar"})
DEFAULT_STATIC_ZONES = ("img", "uploads", "assets")
RULE_ID = "PHP.ZONE.EXECUTABLE"


def _normalize_zones(zones: Sequence[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for zone in zones:
        value = zone.strip().replace("\\", "/").strip("/")
        if not value or value == "." or value.startswith("/") or ".." in value.split("/"):
            raise ValueError(f"zona PHP inválida: {zone!r}")
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _in_static_zone(relative: str, zones: Sequence[str]) -> str | None:
    for zone in zones:
        if relative == zone or relative.startswith(f"{zone}/"):
            return zone
    return None


class PHPGenericAdapter:
    """Descobre PHP por extensão sem abrir conteúdo nem seguir symlinks."""

    id = "php_generic"

    def __init__(self, static_zones: Sequence[str] = DEFAULT_STATIC_ZONES) -> None:
        self.static_zones = _normalize_zones(static_zones)

    def discover(self, target: Target) -> PlatformDiscovery | None:
        count = 0
        try:
            for root, dirs, files in os.walk(target.root, followlinks=False):
                dirs[:] = [name for name in dirs if not os.path.islink(os.path.join(root, name))]
                count += sum(Path(name).suffix.lower() in PHP_EXTENSIONS for name in files)
        except OSError:
            return None
        if not count:
            return None
        return PlatformDiscovery(
            platform_id=self.id,
            signals=(f"php_files:{count}",),
        )

    def classify(self, relative: str) -> str:
        zone = _in_static_zone(relative, self.static_zones)
        if zone is not None:
            return f"php-static:{zone}"
        if Path(relative).suffix.lower() in PHP_EXTENSIONS:
            return "php-webroot"
        return "php-other"


class PHPStaticExecutablePolicy(Detector):
    """Sinaliza PHP executável dentro de prefixo declarado como estático."""

    id = "php-static-executable"
    wants_stream = False

    def __init__(self, static_zones: Sequence[str] = DEFAULT_STATIC_ZONES) -> None:
        self.static_zones = _normalize_zones(static_zones)

    def analyze(
        self, artifact: Artifact, zone: str | None, head: bytes, chunks: Iterable[bytes]
    ) -> Sequence[ProposedFinding]:
        if artifact.kind is not ArtifactKind.FILE or not looks_executable(head):
            return ()
        static_zone = _in_static_zone(artifact.path.relative, self.static_zones)
        if static_zone is None:
            return ()
        return (
            ProposedFinding(
                rule_id=RULE_ID,
                title="Conteúdo PHP executável encontrado em zona estática",
                category="policy",
                severity=Severity.HIGH,
                confidence=Confidence(ConfidenceClass.HIGH),
                evidence_kind="php_static_policy",
                evidence_content={
                    "zone": static_zone,
                    "relative": artifact.path.relative,
                },
                attributes={"zone": static_zone},
            ),
        )
