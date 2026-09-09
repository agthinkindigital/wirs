"""Heurísticas PHP v0: sinais fracos + combinação explícita (spec T050–T054).

Devolve PROPOSTAS sem evidence_refs (o orquestrador cunha a Evidence e anexa
a ref — invariante 2). Regras de combinação (a única inteligência aqui):
- ENCODING + (DYNAMIC_EXECUTION | PROCESS | DYNAMIC_FUNCTION) → CHAIN/HIGH
- 3+ famílias → CHAIN/HIGH
- DYNAMIC_EXECUTION + (PROCESS | FILE_NET | DYNAMIC_FUNCTION) → COMBO/MEDIUM
- PROCESS + FILE_NET → COMBO/MEDIUM
- DYNAMIC_EXECUTION ou PROCESS isolados → SINGLE/LOW
- demais isolados → nada (comuns demais em código legítimo)
- heurística NUNCA gera CRITICAL (só determinístico/assinatura podem)
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from wirs.domain import Artifact, Confidence, ConfidenceClass, Severity
from wirs.ports.detection import ProposedFinding

_DYNAMIC_EXECUTION = (
    rb"\beval\s*\(",
    rb"\bassert\s*\(",
    rb"\bcreate_function\s*\(",
    rb"\bcall_user_func(_array)?\s*\(",
)
_ENCODING = (
    rb"\bbase64_decode\s*\(",
    rb"\bgzinflate\s*\(",
    rb"\bstr_rot13\s*\(",
    rb"\bhex2bin\s*\(",
    rb"\burldecode\s*\(",
    rb"\bconvert_uudecode\s*\(",
)
_PROCESS = (
    rb"\bshell_exec\s*\(",
    rb"\bexec\s*\(",
    rb"\bsystem\s*\(",
    rb"\bpassthru\s*\(",
    rb"\bpopen\s*\(",
    rb"\bproc_open\s*\(",
    rb"\bpcntl_exec\s*\(",
)
_FILE_NET = (
    rb"\bfile_get_contents\s*\(",
    rb"\bfile_put_contents\s*\(",
    rb"\bfopen\s*\(",
    rb"\bcurl_exec\s*\(",
    rb"\bcurl_init\s*\(",
    rb"\bfsockopen\s*\(",
    rb"\bcopy\s*\(",
    rb"\bmove_uploaded_file\s*\(",
)
_DYNAMIC_FUNCTION = (rb"\$\w+\s*\(", rb"`[^`]{1,200}`")
_ENCODED_LITERAL = (rb"[A-Za-z0-9+/]{200,}={0,2}",)

_FAMILIES: tuple[tuple[str, tuple[bytes, ...]], ...] = (
    ("dynamic_execution", _DYNAMIC_EXECUTION),
    ("encoding", _ENCODING),
    ("process", _PROCESS),
    ("file_network", _FILE_NET),
    ("dynamic_function", _DYNAMIC_FUNCTION),
    ("encoded_literal", _ENCODED_LITERAL),
)

_PATTERNS = [(fam, re.compile(b"|".join(pats), re.IGNORECASE)) for fam, pats in _FAMILIES]


def signal_families(head: bytes) -> tuple[str, ...]:
    """Famílias de sinais presentes nos bytes (case-insensitive, sem decode)."""
    return tuple(fam for fam, rx in _PATTERNS if rx.search(head))


def _tier(families: frozenset[str]) -> tuple[str, Severity, Confidence] | None:
    enc = "encoding" in families
    if enc and (families & {"dynamic_execution", "process", "dynamic_function"}):
        return ("PHP.HEUR.CHAIN", Severity.HIGH, Confidence(ConfidenceClass.HIGH))
    if len(families) >= 3:
        return ("PHP.HEUR.CHAIN", Severity.HIGH, Confidence(ConfidenceClass.HIGH))
    if "dynamic_execution" in families and (
        families & {"process", "file_network", "dynamic_function"}
    ):
        return ("PHP.HEUR.COMBO", Severity.MEDIUM, Confidence(ConfidenceClass.MEDIUM))
    if {"process", "file_network"} <= families:
        return ("PHP.HEUR.COMBO", Severity.MEDIUM, Confidence(ConfidenceClass.MEDIUM))
    if families & {"dynamic_execution", "process"}:
        return ("PHP.HEUR.SINGLE", Severity.LOW, Confidence(ConfidenceClass.LOW))
    return None


def analyze_php(
    artifact: Artifact,
    head: bytes,
    *,
    evidence_refs: Sequence[str] = (),
) -> tuple[ProposedFinding, ...]:
    """Uma proposta no máximo (o tier mais alto): sem duplicar por família.

    `evidence_refs` existe por compatibilidade e é ignorado: a ref verdadeira
    é anexada pelo orquestrador ao cunhar a Evidence.
    """
    _ = evidence_refs
    families = frozenset(signal_families(head))
    decided = _tier(families)
    if decided is None:
        return ()
    rule_id, severity, confidence = decided
    return (
        ProposedFinding(
            rule_id=rule_id,
            title="Padrões suspeitos de ofuscação/execução em PHP",
            category="heuristic",
            severity=severity,
            confidence=confidence,
            evidence_kind="php_heuristic",
            evidence_content={"rule": rule_id, "signals": sorted(families)},
            attributes={"signals": sorted(families)},
        ),
    )
