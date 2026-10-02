"""Relações entre findings (WIRS-105): pistas de correlação, nunca atribuição.

Vocabulário em CONTEXT.md (Actor): compartilhar IP, CIDR ou User-Agent é
pista de relação, não prova de que eventos vieram da mesma pessoa. Por isso
`attribution` é False em toda relação derivada de rede, e `cue` nunca admite
attribution True (regra estrutural, não convenção).

Chaves (§12.3 do spec, subconjunto filesystem desta DAG): mesmo artifact,
component, IOC, rede exata, owner e janela temporal. CIDR e família de
User-Agent entram como `cue`. Chaves de log (conta/sessão) e DB chegam com
os adapters (#73–#75, #85); o modelo já as aceita via attributes.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any

from wirs.domain.finding import Finding

_StrongRule = str


class RelationKind(Enum):
    """Força da pista: identidade observada (STRONG) ou pista fraca (CUE)."""

    STRONG = "strong"
    CUE = "cue"


def _relation_id(rule_id: str, refs: Sequence[str], key: str, window: str, kind: str) -> str:
    canonical = json.dumps(
        {
            "rule_id": rule_id,
            "refs": sorted(refs),
            "key": key,
            "window": window,
            "kind": kind,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"rel_{hashlib.sha256(canonical.encode()).hexdigest()[:16]}"


@dataclass(frozen=True)
class FindingRelation:
    """Pista de que findings se relacionam; não cria Evidence nem muda confiança."""

    rule_id: str
    kind: RelationKind
    finding_refs: tuple[str, ...]
    key: str
    window: str
    justification: str
    attribution: bool = True
    id: str = ""

    def __post_init__(self) -> None:
        refs = tuple(sorted(self.finding_refs))
        object.__setattr__(self, "finding_refs", refs)
        if len(refs) < 2:
            raise ValueError("Relation exige pelo menos 2 findings")
        if len(set(refs)) != len(refs):
            raise ValueError("Relation não referencia o mesmo finding 2x")
        if not self.rule_id:
            raise ValueError("Relation exige rule_id")
        if not self.key:
            raise ValueError("Relation exige key explícita")
        if not self.window:
            raise ValueError("Relation exige window explícita")
        if not self.justification:
            raise ValueError("Relation exige justification")
        if self.kind is RelationKind.CUE and self.attribution:
            raise ValueError("cue nunca admite attribution (NAT/proxy/CDN compartilham pista)")
        if not self.id:
            object.__setattr__(
                self,
                "id",
                _relation_id(self.rule_id, refs, self.key, self.window, self.kind.value),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "kind": self.kind.value,
            "finding_refs": list(self.finding_refs),
            "key": self.key,
            "window": self.window,
            "justification": self.justification,
            "attribution": self.attribution,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> FindingRelation:
        try:
            kind = RelationKind(str(data["kind"]))
        except (KeyError, ValueError) as e:
            raise ValueError(f"kind de Relation inválido: {data.get('kind')!r}") from e
        return cls(
            rule_id=str(data["rule_id"]),
            kind=kind,
            finding_refs=tuple(str(ref) for ref in data["finding_refs"]),
            key=str(data["key"]),
            window=str(data["window"]),
            justification=str(data["justification"]),
            attribution=bool(data.get("attribution", True)),
            id=str(data.get("id", "")),
        )


def _str_attr(finding: Finding, *names: str) -> str | None:
    for name in names:
        value = finding.attributes.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _day_bucket(raw: str) -> str | None:
    try:
        moment = datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return None
    day: date = moment.date()
    return f"{day.isoformat()}"


def _cidr(raw_ip: str) -> str | None:
    try:
        parsed = ipaddress.ip_address(raw_ip.strip())
    except ValueError:
        return None
    if isinstance(parsed, ipaddress.IPv4Address):
        return f"{ipaddress.ip_network(f'{parsed}/24', strict=False)}"
    return f"{ipaddress.ip_network(f'{parsed}/64', strict=False)}"


def correlate_relations(findings: Sequence[Finding]) -> tuple[FindingRelation, ...]:
    """Agrupa findings por chaves explícitas; sem dados na chave, sem relação."""
    indexed = [finding for finding in findings if finding.id]
    groups: dict[tuple[str, RelationKind, str, str], list[str]] = defaultdict(list)
    justifications: dict[tuple[str, RelationKind, str, str], str] = {}
    attributions: dict[tuple[str, RelationKind, str, str], bool] = {}

    def link(
        rule_id: str,
        kind: RelationKind,
        key: str,
        window: str,
        ref: str,
        justification: str,
        attribution: bool,
    ) -> None:
        slot = (rule_id, kind, key, window)
        groups[slot].append(ref)
        justifications[slot] = justification
        attributions[slot] = attribution

    for finding in indexed:
        ref = finding.id
        link(
            "REL.SAME_ARTIFACT",
            RelationKind.STRONG,
            f"artifact:{finding.artifact_ref}",
            "exact",
            ref,
            f"{finding.artifact_ref}: findings no mesmo artifact; triar o arquivo uma vez.",
            True,
        )
        component = _str_attr(finding, "component")
        if component is not None:
            link(
                "REL.SAME_COMPONENT",
                RelationKind.STRONG,
                f"component:{component}",
                "exact",
                ref,
                f"{component}: findings no mesmo component; checar o pacote inteiro.",
                True,
            )
        ioc = _str_attr(finding, "ioc_id")
        if ioc is not None:
            link(
                "REL.SAME_IOC",
                RelationKind.STRONG,
                f"ioc:{ioc}",
                "exact",
                ref,
                f"{ioc}: mesmo indicador em vários pontos; validar o indicador.",
                True,
            )
        domain = _str_attr(finding, "domain")
        if domain is not None:
            link(
                "REL.SAME_NETWORK",
                RelationKind.STRONG,
                f"domain:{domain.lower()}",
                "exact",
                ref,
                f"{domain}: mesmo domínio observado; hosting compartilhado é alternativa válida.",
                False,
            )
        raw_ip = _str_attr(finding, "ip")
        if raw_ip is not None:
            link(
                "REL.SAME_NETWORK",
                RelationKind.STRONG,
                f"ip:{raw_ip}",
                "exact",
                ref,
                f"{raw_ip}: mesmo IP; NAT/proxy/CDN compartilham IP: pista, não ator.",
                False,
            )
            network = _cidr(raw_ip)
            if network is not None:
                link(
                    "REL.SAME_CIDR",
                    RelationKind.CUE,
                    f"cidr:{network}",
                    "exact",
                    ref,
                    f"{network}: mesma faixa; atores distintos dividem CIDR.",
                    False,
                )
        owner = _str_attr(finding, "owner", "account")
        if owner is not None:
            link(
                "REL.SAME_OWNER",
                RelationKind.STRONG,
                f"owner:{owner}",
                "exact",
                ref,
                f"{owner}: mesma conta/owner; admin legítimo automatiza mudanças em massa.",
                True,
            )
        ua_family = _str_attr(finding, "ua_family")
        if ua_family is not None:
            link(
                "REL.SAME_UA_FAMILY",
                RelationKind.CUE,
                f"ua_family:{ua_family}",
                "exact",
                ref,
                f"{ua_family}: mesma família de UA; bots compartilham UA: pista, não ator.",
                False,
            )
        occurred = _str_attr(finding, "occurred_at")
        day = _day_bucket(occurred) if occurred is not None else None
        if day is not None:
            link(
                "REL.SAME_WINDOW",
                RelationKind.STRONG,
                f"day:{day}",
                "24h",
                ref,
                f"{day}: mesma janela de 24h; lote ou coincidência de coleta.",
                True,
            )

    relations: list[FindingRelation] = []
    seen: set[str] = set()
    for slot in sorted(groups):
        rule_id, kind, key, window = slot
        refs = sorted(set(groups[slot]))
        if len(refs) < 2:
            continue
        relation = FindingRelation(
            rule_id=rule_id,
            kind=kind,
            finding_refs=tuple(refs),
            key=key,
            window=window,
            justification=justifications[slot],
            attribution=attributions[slot],
        )
        if relation.id in seen:
            continue
        seen.add(relation.id)
        relations.append(relation)
    return tuple(sorted(relations, key=lambda item: item.id))
