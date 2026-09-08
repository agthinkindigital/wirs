# ADR-004 — Canonical JSON schema

- **Status:** aceito
- **Data:** 2026-09-08

## Contexto

Terminal, Markdown e HTML são views; é preciso um formato canônico estável
para automação, comparação e re-análise.

## Decisão

JSON é o formato canônico: separa `schema_version` de `scanner_version`,
ordering estável, sem conteúdo bruto de arquivo por padrão. Breaking change
de campo implica major de schema (golden tests travam compatibilidade).

## Consequências

- `wirs scan --format json` é a fonte de verdade; demais formatos derivam dela.
- SARIF e HTML consomem o modelo em modo read-only.
