# ADR-009 — Safe WP-CLI mode sem bootstrap por padrão

- **Status:** aceito
- **Data:** 2026-09-08

## Contexto

Comandos WP-CLI que fazem bootstrap da aplicação executam código
(possivelmente comprometido) de plugins/themes.

## Decisão

`wp_cli_mode: safe_only` por padrão: apenas comandos documentados pré-load.
`allow_application_bootstrap` é opt-in explícito e classificado como modo
de maior risco. Nunca rodar como root por conveniência.

## Consequências

- Collector que exige bootstrap e está bloqueado registra skip explícito no Coverage.
- `wirs doctor` reporta modo, path, versão e disponibilidade do WP-CLI.
