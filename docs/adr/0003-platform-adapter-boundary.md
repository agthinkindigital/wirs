# ADR-003 — Platform adapter boundary

- **Status:** aceito
- **Data:** 2026-09-08

## Contexto

WordPress é o adapter #1, mas o produto é um motor genérico de IR
(PHP, Laravel, Joomla, host Linux no futuro).

## Decisão

`domain/` conhece apenas Target, Artifact, Evidence, Finding, Diagnosis,
Baseline, Provider, Rule, Coverage. Conceitos de plataforma (`wp-content`,
`artisan`, `composer.lock`) vivem em `adapters/` + rule packs.

## Consequências

- Architecture test: `domain` não importa `wordpress`, `yara`, `wordfence`,
  `rich`, `mysql`, `typer`.
- Remover o adapter WordPress não quebra testes do core.
