# ADR-001 — Python no MVP

- **Status:** aceito
- **Data:** 2026-09-08

## Contexto

Precisamos de linguagem para o MVP do scanner: ecossistema de CLI, testes
e providers (WP-CLI, YARA, MySQL) com baixo custo de integração.

## Decisão

Python 3.11+ (`requires-python >=3.11`), CLI com Typer, terminal com Rich,
testes com pytest + Hypothesis, lint/format Ruff, tipos mypy.

## Alternativas

Go/Rust: binário único e performance, porém custo maior de prototipação de
providers e heurísticas. Adiado até profiling provar gargalo (Seção 19.17).

## Consequências

- Distribuição inicial via pip/pipx; binário standalone pós-MVP.
- Hot paths em Rust/Go só com evidência de profiling.
