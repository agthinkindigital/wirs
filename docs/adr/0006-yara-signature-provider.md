# ADR-006 — YARA como signature provider opcional

- **Status:** aceito
- **Data:** 2026-09-08

## Contexto

Regex/heuística interna cobre sinais baratos; assinaturas ricas pedem engine madura.

## Decisão

YARA é o primeiro signature provider extensível (`rules/yara/{builtin,wordpress,php,experimental}`),
sempre opcional: ausência ou erro de compilação vira Coverage `UNAVAILABLE`/`FAILED`, nunca aborta.

## Consequências

- Não reimplementar corpus concorrente no MVP; Wordfence CLI entra como analyzer opcional separado.
- Matches preservam rule/tags/namespace + provenance do provider.
