"""Scanner literal em streaming: bytes always, fronteira de chunk, cap, contexto.

- Opera só em bytes (nunca decodifica binário como texto).
- IOC que cruza fronteira de chunk é achado via carry de (max_len - 1).
- Cap de ocorrências por IOC preserva o count total (`truncated=True`).
- Contexto limitado a `context_bytes` por lado (redação de secrets chega na #41).
- Kind SHA256 não é literal: ignorado aqui (comparação via HashService, no orquestrador).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType

from wirs.domain import IOC, IOCKind

_LITERAL_KINDS = (IOCKind.LITERAL, IOCKind.DOMAIN, IOCKind.URL_FRAGMENT, IOCKind.PATH_FRAGMENT)


@dataclass(frozen=True)
class IocMatch:
    ioc_id: str
    kind: IOCKind
    offset: int
    context: bytes


@dataclass(frozen=True)
class IocScanResult:
    matches: tuple[IocMatch, ...] = ()
    total_counts: Mapping[str, int] = field(default_factory=lambda: MappingProxyType({}))
    truncated: bool = False


def _patterns(iocs: Sequence[IOC]) -> list[tuple[IOC, bytes, bool]]:
    out: list[tuple[IOC, bytes, bool]] = []
    for ioc in iocs:
        if ioc.kind not in _LITERAL_KINDS:
            continue
        raw = ioc.value.encode("utf-8")
        out.append(
            (ioc, raw.lower() if ioc.kind is IOCKind.DOMAIN else raw, ioc.kind is IOCKind.DOMAIN)
        )
    return out


def scan_stream(
    chunks: Iterable[bytes],
    iocs: Sequence[IOC],
    *,
    occurrence_cap: int = 100,
    context_bytes: int = 64,
) -> IocScanResult:
    patterns = _patterns(iocs)
    if not patterns:
        return IocScanResult()
    max_len = max(len(p) for _, p, _ in patterns)
    carry_len = max(max_len - 1, context_bytes, 1)

    matches: list[IocMatch] = []
    totals: dict[str, int] = {}
    truncated = False
    carry = b""
    consumed = 0  # bytes totais antes da janela atual

    for chunk in chunks:
        if not chunk:
            continue
        window = carry + chunk
        lowered = window.lower()
        base = consumed - len(carry)  # offset absoluto do início da janela
        for ioc, pattern, ci in patterns:
            hay = lowered if ci else window
            start = 0
            while True:
                at = hay.find(pattern, start)
                if at == -1:
                    break
                end = at + len(pattern)
                start = at + 1
                if end <= len(carry):
                    continue  # já reportado no chunk anterior
                totals[ioc.id] = totals.get(ioc.id, 0) + 1
                if len([m for m in matches if m.ioc_id == ioc.id]) >= occurrence_cap:
                    truncated = True
                    continue
                lo = max(0, at - context_bytes)
                matches.append(
                    IocMatch(
                        ioc_id=ioc.id,
                        kind=ioc.kind,
                        offset=base + at,
                        context=window[lo : end + context_bytes],
                    )
                )
        consumed += len(chunk)
        carry = window[-carry_len:]
    return IocScanResult(
        matches=tuple(matches), total_counts=MappingProxyType(dict(totals)), truncated=truncated
    )


def scan_bytes(
    data: bytes,
    iocs: Sequence[IOC],
    *,
    occurrence_cap: int = 100,
    context_bytes: int = 64,
) -> IocScanResult:
    return scan_stream([data], iocs, occurrence_cap=occurrence_cap, context_bytes=context_bytes)
