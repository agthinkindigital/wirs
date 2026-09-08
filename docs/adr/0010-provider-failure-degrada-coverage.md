# ADR-010 — Provider failure degrada coverage

- **Status:** aceito
- **Data:** 2026-09-08

## Contexto

YARA ausente, WP-CLI inexistente, DB indisponível: ambientes reais são parciais.

## Decisão

Falha de provider é resultado de primeira classe: vira status de provider +
Coverage (`UNAVAILABLE`/`FAILED`/`PARTIAL`), nunca `COMPLETE` silencioso e
nunca aborta o scan (salvo invalidade do próprio alvo).

## Consequências

- "Zero findings" sem Coverage completo não significa "limpo" (wording policy).
- `verified + failed + skipped + unavailable = applicable_checks` (invariante testada).
