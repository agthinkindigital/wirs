# ADR-002 — Read-only por padrão

- **Status:** aceito
- **Data:** 2026-09-08

## Contexto

Ferramenta de incident response operando sobre alvos potencialmente
comprometidos e em produção compartilhada.

## Decisão

`wirs scan` nunca escreve no target (P1 do spec). Remediação fica fora do
MVP: outro subsistema, outro namespace, outro modelo de autorização.

## Consequências

- Testes E2E devem provar zero escrita (mtime/hash do target inalterados).
- `ScanOrchestrator` não importa nenhum módulo de remediação (architecture test).
