# ADR-008 — Symlink não seguido por padrão

- **Status:** aceito
- **Data:** 2026-09-08

## Contexto

Alvo hostil controla symlinks: escape do root, loops, FIFOs disfarçados.

## Decisão

Inventory registra symlink como metadata (caminho, destino, escape, loop)
e nunca atravessa fora do root por padrão.

## Consequências

- `SafePath` nunca resolve para fora do `TargetRoot` (property test).
- Escape/loop viram Findings ou Coverage explícito, não travamento.
