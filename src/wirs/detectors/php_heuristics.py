"""Heurísticas PHP v0: sinais fracos + combinação explícita (spec T050–T054).

Devolve PROPOSTAS sem evidence_refs (o orquestrador cunha a Evidence e anexa
a ref — invariante 2). Regras de combinação (a única inteligência aqui):
- ENCODING + (DYNAMIC_EXECUTION | PROCESS | DYNAMIC_FUNCTION) → CHAIN/HIGH
- 3+ famílias → CHAIN/HIGH
- DYNAMIC_EXECUTION + (PROCESS | FILE_NET | DYNAMIC_FUNCTION) → COMBO/MEDIUM
- PROCESS + FILE_NET → COMBO/MEDIUM
- FUNCTION_MAPPING + DYNAMIC_FUNCTION → COMBO/MEDIUM (#84: webshell por mapa)
- DYNAMIC_EXECUTION ou PROCESS isolados → SINGLE/LOW
- demais isolados → nada (comuns demais em código legítimo)
- heurística NUNCA gera CRITICAL por conta própria (só determinístico/assinatura podem)
  exceto quando a zona é CORE_PROTECTED (core WordPress), onde escala para CRITICAL.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence

from wirs.adapters.wordpress.zones import WordPressZone
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
_STREAM_CARRY_BYTES = 512
_CONTEXT_LINE_CAP = 5
_CONTEXT_LINE_WIDTH = 200

# Nomes perigosos citados como strings (#84: mapa de despacho do webshell).
# Veredito exige 2+ nomes DISTINTOS + chamada dinâmica (1 nome citado sozinho
# é comum em docs/logs). Ordenados por tamanho p/ alternância exata.
_MAPPING_NAMES: tuple[bytes, ...] = tuple(
    sorted(
        (
            b"create_function",
            b"call_user_func",
            b"file_get_contents",
            b"file_put_contents",
            b"move_uploaded_file",
            b"base64_decode",
            b"shell_exec",
            b"proc_open",
            b"gzinflate",
            b"str_rot13",
            b"passthru",
            b"assert",
            b"system",
            b"popen",
            b"fopen",
            b"eval",
            b"exec",
        ),
        key=len,
        reverse=True,
    )
)
_MAPPING_RX = re.compile(rb"['\"](" + b"|".join(_MAPPING_NAMES) + rb")['\"]", re.IGNORECASE)
# Legit code cita 1-2 nomes (docs/fallbacks, ex.: 'fopen'+'gzinflate' no
# Requests); shells mapeiam cardápios inteiros. Limiar em 3 distintos.
_MAPPING_MIN_DISTINCT = 3


def _mapping_names(data: bytes) -> frozenset[bytes]:
    """Nomes perigosos distintos citados como strings no conteúdo."""
    return frozenset(match.group(1).lower() for match in _MAPPING_RX.finditer(data))


def _matching_lines(data: bytes, limit: int = _CONTEXT_LINE_CAP) -> tuple[str, ...]:
    """Linhas que casam algum padrão (trecho demonstrativo da evidência).

    Aparadas em largura e quantidade para não inflar o report; a redaction
    final (secrets) acontece no orquestrador.
    """
    out: list[str] = []
    for raw in data.split(b"\n"):
        if not any(rx.search(raw) for _, rx in _PATTERNS) and not _MAPPING_RX.search(raw):
            continue
        out.append(raw.decode("utf-8", errors="replace").strip()[:_CONTEXT_LINE_WIDTH])
        if len(out) >= limit:
            break
    return tuple(out)


def signal_families(head: bytes) -> tuple[str, ...]:
    """Famílias de sinais presentes nos bytes (case-insensitive, sem decode)."""
    return tuple(fam for fam, rx in _PATTERNS if rx.search(head))


def signal_families_stream(chunks: Iterable[bytes]) -> tuple[str, ...]:
    """Encontra famílias em stream, preservando padrões entre chunks."""
    found: set[str] = set()
    carry = b""
    for chunk in chunks:
        if not chunk:
            continue
        window = carry + chunk
        found.update(signal_families(window))
        carry = window[-_STREAM_CARRY_BYTES:]
    return tuple(fam for fam, _ in _FAMILIES if fam in found)


def _tier(
    families: frozenset[str], zone: str | None = None
) -> tuple[str, Severity, Confidence] | None:
    enc = "encoding" in families
    high = Confidence(ConfidenceClass.HIGH)
    medium = Confidence(ConfidenceClass.MEDIUM)
    low = Confidence(ConfidenceClass.LOW)
    if enc and (families & {"dynamic_execution", "process", "dynamic_function"}):
        rule_id, severity, confidence = "PHP.HEUR.CHAIN", Severity.HIGH, high
    elif len(families) >= 3:
        rule_id, severity, confidence = "PHP.HEUR.CHAIN", Severity.HIGH, high
    elif "dynamic_execution" in families and (
        families & {"process", "file_network", "dynamic_function"}
    ):
        rule_id, severity, confidence = "PHP.HEUR.COMBO", Severity.MEDIUM, medium
    elif {"process", "file_network"} <= families:
        rule_id, severity, confidence = "PHP.HEUR.COMBO", Severity.MEDIUM, medium
    elif {"function_mapping", "dynamic_function"} <= families:
        rule_id, severity, confidence = "PHP.HEUR.COMBO", Severity.MEDIUM, medium
    elif families & {"dynamic_execution", "process"}:
        rule_id, severity, confidence = "PHP.HEUR.SINGLE", Severity.LOW, low
    else:
        return None

    # Escalation para CRITICAL se zona é CORE_PROTECTED (core WP modificado)
    if zone == WordPressZone.CORE_PROTECTED.value:
        severity = Severity.CRITICAL
        confidence = Confidence(ConfidenceClass.HIGH)

    return (rule_id, severity, confidence)


def _is_php_file(artifact: Artifact) -> bool:
    """Verifica se artifact é arquivo PHP (extensão .php)."""
    return artifact.path.relative.lower().endswith(".php")


def analyze_php(
    artifact: Artifact,
    head: bytes,
    *,
    zone: str | None = None,
    evidence_refs: Sequence[str] = (),
) -> tuple[ProposedFinding, ...]:
    """Uma proposta no máximo (o tier mais alto): sem duplicar por família.

    `evidence_refs` existe por compatibilidade e é ignorado: a ref verdadeira
    é anexada pelo orquestrador ao cunhar a Evidence.

    Só analisa arquivos .php; demais extensões retornam vazio.
    """
    if not _is_php_file(artifact):
        return ()
    _ = evidence_refs
    families = frozenset(signal_families(head))
    if len(_mapping_names(head)) >= _MAPPING_MIN_DISTINCT:
        families |= {"function_mapping"}
    decided = _tier(families, zone)
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
            evidence_content={
                "rule": rule_id,
                "signals": sorted(families),
                "contexts": list(_matching_lines(head)),
            },
            attributes={"signals": sorted(families)},
        ),
    )


def analyze_php_stream(
    artifact: Artifact, chunks: Iterable[bytes], zone: str | None = None
) -> tuple[ProposedFinding, ...]:
    """Analisa o conteúdo inteiro disponibilizado pelo budget, sem materializá-lo.

    Só analisa arquivos .php; demais extensões retornam vazio. Os contexts
    vêm de linhas completas por chunk (padrão cortado na fronteira de chunk
    pode não aparecer no trecho, sem afetar o veredito).
    """
    if not _is_php_file(artifact):
        return ()
    found: set[str] = set()
    contexts: list[str] = []
    carry = b""
    line_carry = b""
    mapping: set[bytes] = set()
    for chunk in chunks:
        if not chunk:
            continue
        window = carry + chunk
        found.update(fam for fam, rx in _PATTERNS if rx.search(window))
        mapping.update(_mapping_names(window))
        carry = window[-_STREAM_CARRY_BYTES:]
        if len(contexts) < _CONTEXT_LINE_CAP:
            parts = (line_carry + chunk).split(b"\n")
            line_carry = parts[-1]
            for raw in parts[:-1]:
                if not any(rx.search(raw) for _, rx in _PATTERNS) and not _MAPPING_RX.search(raw):
                    continue
                linha = raw.decode("utf-8", errors="replace").strip()
                contexts.append(linha[:_CONTEXT_LINE_WIDTH])
                if len(contexts) >= _CONTEXT_LINE_CAP:
                    break
    if line_carry and len(contexts) < _CONTEXT_LINE_CAP:
        if any(rx.search(line_carry) for _, rx in _PATTERNS):
            linha = line_carry.decode("utf-8", errors="replace").strip()
            contexts.append(linha[:_CONTEXT_LINE_WIDTH])
    families = frozenset(fam for fam, _ in _FAMILIES if fam in found)
    if len(mapping) >= _MAPPING_MIN_DISTINCT:
        families |= {"function_mapping"}
    decided = _tier(families, zone)
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
            evidence_content={
                "rule": rule_id,
                "signals": sorted(families),
                "contexts": contexts,
            },
            attributes={"signals": sorted(families)},
        ),
    )
