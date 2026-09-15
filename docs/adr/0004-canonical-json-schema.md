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

## Atualização contratual — #65-01

O `CanonicalReport` evolui para o schema `2.0`. O report contém `manifest`,
`artifacts`, `evidence`, `findings`, `coverage`, `provider_runs` e
`diagnoses`. `artifact_ref` passa a aceitar somente identidades canônicas
resolvíveis; a identidade de Artifact usa `source_ref`, `kind` e caminho
relativo normalizado, nunca o root absoluto. Uma entrada esperada pelo
baseline e ausente no filesystem é serializada como Artifact lógico.

A transformação de `ScanResult` para o report ocorre em um único ponto, com
validação referencial e redaction final antes da escrita. Coleções canônicas
têm ordenação determinística e `diagnoses` pode ser vazio nesta fase.
