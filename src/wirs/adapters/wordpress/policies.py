"""Policies WordPress: expectativa de zona + conteúdo (spec 6.2 e 8/Q17).

PHP em uploads é forte violação de expectativa — mas violação de expectativa,
não prova de malware. Por isso severity HIGH com confidence HIGH (não
DETERMINISTIC): a zona é convenção, não baseline oficial.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Sequence

from wirs.adapters.wordpress.zones import WordPressZone
from wirs.detectors.executable import looks_executable
from wirs.domain import Artifact, Confidence, ConfidenceClass, Finding, Severity

RULE_ID = "WP.UPLOAD.EXECUTABLE"


def check_uploads_executable(
    artifact: Artifact,
    zone: WordPressZone,
    head: bytes,
    *,
    evidence_refs: Sequence[str],
    allowlist: Sequence[str] = (),
) -> Finding | None:
    """Retorna Finding se houver conteúdo executável onde não deveria."""
    if zone is not WordPressZone.UPLOADS:
        return None
    if not looks_executable(head):
        return None
    if any(fnmatch.fnmatchcase(artifact.path.relative, pattern) for pattern in allowlist):
        return None
    return Finding(
        rule_id=RULE_ID,
        title="Conteúdo executável encontrado em zona destinada a uploads",
        category="policy",
        severity=Severity.HIGH,
        confidence=Confidence(ConfidenceClass.HIGH),
        artifact_ref=artifact.id,
        evidence_refs=tuple(evidence_refs),
        attributes={"zone": zone.value},
    )
