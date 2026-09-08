# WIRS — WordPress Incident Response Scanner

Motor genérico de scanning para **resposta a incidentes, integridade e
orquestração de evidências**. O primeiro adapter é WordPress; o core não
conhece `wp-content`, plugins ou qualquer conceito de plataforma.

> Especificação viva: [`WIRS_MASTER_SPEC_PT-BR.md`](WIRS_MASTER_SPEC_PT-BR.md).
> Glossário: [`CONTEXT.md`](CONTEXT.md). Decisões: [`docs/adr/`](docs/adr/).

## Princípios

- **Read-only**: `scan` nunca escreve no target.
- **Evidence-first**: finding sem evidência não existe.
- **Determinístico antes de heurístico**.
- **Coverage é resultado de primeira classe**: "zero findings" ≠ "limpo".
- Conteúdo do alvo é **input hostil**.

## Execução local

```powershell
# pré-requisitos: Python 3.11+ e uv (scoop install uv)
uv venv
uv pip install -e ".[dev]"
wirs --help
wirs doctor
wirs scan ./tests/fixtures/generic/clean_tree --format json
```

## Layout

```text
src/wirs/         CLI (composition root), domain, application, ports,
                  infrastructure, detectors, providers, adapters/, reporting, config
rules/            builtin, wordpress, php, experimental (YARA packs)
tests/            unit, integration, e2e, security, fixtures/, golden/
docs/             adr/, agents/, providers/
```

## Status

Fase A — Skeleton (`0.0.x`): target/artifact, evidence/finding/coverage,
inventory seguro, reader/hash, JSON canônico.
Critério de saída: `wirs scan tests/fixtures/generic/clean_tree` produz report válido.
