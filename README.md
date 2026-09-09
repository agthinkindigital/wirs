# WIRS — WordPress Incident Response Scanner

[![CI](https://github.com/agthinkindigital/wirs/actions/workflows/ci.yml/badge.svg)](https://github.com/agthinkindigital/wirs/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-%3E%3D3.11-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey)](#instalação)

Quando um WordPress é comprometido, a investigação vira uma colagem de comandos
soltos: um checksum aqui, um `grep` ali, um print do banco acolá — e no fim
ninguém consegue dizer com certeza o que foi verificado, o que ficou de fora,
nem reproduzir a conclusão. O WIRS existe para acabar com isso: ele é um
**motor de scanning para resposta a incidentes** que inventaria o alvo,
verifica integridade contra baselines confiáveis, caça indicadores conhecidos,
aplica heurísticas com honestidade sobre incerteza e entrega tudo com
**evidências, cobertura explícita e conclusões reproduzíveis**.

Se esse problema já te custou uma madrugada, dá uma estrela para acompanhar —
e se manja de Python, PHP ou forense web, as [issues](https://github.com/agthinkindigital/wirs/issues)
estão abertas para contribuir.

## O que ele faz

- Aponta **quais arquivos diferem de uma origem confiável** (checksums oficiais do core e plugins via WP-CLI, baselines do operador para temas/plugins premium).
- Encontra **arquivos onde não deveriam existir** (PHP em `uploads`, executáveis em zonas de conteúdo, extras em áreas protegidas do core).
- Diz claramente **o que não pôde verificar** — sem baseline confiável, o componente é `UNVERIFIED`, nunca "malicioso" por definição.
- Procura **IOCs literais**, aplica um **pacote heurístico PHP** e pluga **YARA / Wordfence CLI** como analyzers opcionais.
- Mapeia **persistências** (MU-plugins, cron, config) e superfícies de **banco de dados** que merecem investigação.
- Separa **fatos** (determinísticos) de **suspeitas** (heurísticas) e de **diagnósticos** (hipóteses correlacionadas) — nunca resume tudo num "INFECTED" sem explicar o porquê.
- Gera relatório **JSON canônico** + terminal, Markdown e HTML.

## O que ele não faz

Não remove malware, não é EDR/WAF/daemon, não substitui Wordfence, WPScan,
YARA ou WP-CLI — ele **orquestra e correlaciona** essas ferramentas. Também
não declara "site limpo": a formulação honesta é *"nenhum finding acima do
threshold nas verificações que concluíram"*, sempre acompanhada da cobertura.

## Como funciona (resumo)

```text
inventory → metadata → hash/baseline → policies → IOCs → heurísticas
→ analyzers externos → correlação → coverage → diagnósticos → relatórios
```

O scan é **100% read-only**: nada é apagado, renomeado, quarentenado ou
alterado no alvo. Funciona sobre diretório local, snapshot copiado, filesystem
montado ou archive — sem precisar instalar nada no servidor investigado.
Como o alvo é tratado como hostil, todo conteúdo dele é sanitizado antes de
chegar ao relatório. O desenho completo está em [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

Exemplo da visão de saída no terminal:

```text
WIRS 0.1.0 · Target: /srv/www/site · Platform: WordPress · Profile: soft · Mode: read-only

SUMMARY                          COVERAGE
CRITICAL  0                      Filesystem           COMPLETE
HIGH      1                      Core baseline        COMPLETE
MEDIUM    3                      Plugin baseline      PARTIAL (2 unverified)
LOW       2                      YARA                 COMPLETE
INFO      14                     Database             NOT RUN
```

## Status do projeto

Estamos na **Fase A — Skeleton**: fundação do motor genérico (target, artifact,
evidence, finding, coverage, inventory seguro, JSON). O primeiro slice
operacional com WordPress (Fase B — `0.1.0`) vem a seguir. Acompanhe pelo
[roadmap](ORCHESTRATOR-ROADMAP.md) e pela [especificação viva](WIRS_MASTER_SPEC_PT-BR.md)
(em português).

## Instalação

Pré-requisitos: **Python 3.11+**, **Git** e o gerenciador [**uv**](https://docs.astral.sh/uv/).
Providers como WP-CLI (precisa de PHP) e YARA são opcionais — o scan degrada a
cobertura com elegância quando eles não existem.

**Windows (recomendado: scoop)**

```powershell
scoop install python uv git
git clone https://github.com/agthinkindigital/wirs.git
cd wirs
uv venv
uv pip install -e ".[dev]"
wirs --help
```

**Linux (Debian/Ubuntu)**

```bash
sudo apt install python3 git curl
curl -LsSf astral.sh/uv/install.sh | sh
git clone https://github.com/agthinkindigital/wirs.git
cd wirs
uv venv
uv pip install -e ".[dev]"
wirs --help
```

**macOS (Homebrew)**

```bash
brew install python@3.11 uv git
git clone https://github.com/agthinkindigital/wirs.git
cd wirs
uv venv
uv pip install -e ".[dev]"
wirs --help
```

Opcionais por plataforma: `wp` ([WP-CLI](https://wp-cli.org/) + PHP),
`yara`, `wordfence`. O comando `wirs doctor` mostra o que foi detectado.

## Uso básico

```bash
wirs doctor                                        # ambiente e providers
wirs scan /srv/www/site --profile soft             # resumo no terminal
wirs scan /srv/www/site --format json --report scan.json
wirs scan ./snapshot --ioc iocs.txt --baseline baselines.yaml
```

Exit codes documentados: `0` limpo no threshold · `1` findings acima do
threshold · `2` target/config inválido · `3` scan incompleto · `4` erro
interno · `5` rule pack inválido.

## Estrutura do projeto

| Caminho | Papel |
|---|---|
| `src/wirs/domain/` | Modelo genérico puro (só stdlib) — Target, Artifact, Evidence, Finding, Diagnosis, Coverage |
| `src/wirs/application/` + `ports/` | Casos de uso e fronteiras (hexagonal sem burocracia) |
| `src/wirs/infrastructure/` | Filesystem, scheduler, hashing, config |
| `src/wirs/detectors/` | Regras internas (sem subprocess, sem I/O direto) |
| `src/wirs/providers/` | WP-CLI, YARA, Wordfence via anti-corruption layer |
| `src/wirs/adapters/wordpress/` | Todo o conhecimento WordPress mora aqui — e só aqui |
| `src/wirs/reporting/` | JSON canônico + views (terminal, Markdown, HTML) |
| `rules/` · `tests/` | Packs de regras e fixtures/TDD (inclui golden tests) |

## Contribuindo

Toda contribuição começa por uma **Issue**: descreva o comportamento, o critério
de aceite e como verificar. O fluxo é TDD em slices verticais pequenos
(um teste → código mínimo → refator), com QA ao final de cada entrega.
Leia [`AGENTS.md`](AGENTS.md) antes do primeiro PR — lá estão as invariantes
que não negociamos (read-only, evidência antes de interpretação, coverage
sempre visível). Documentação de decisões vive em [`docs/adr/`](docs/adr/).

## Segurança

Encontrou uma vulnerabilidade no próprio scanner? Abra uma issue com
`type:security` ou fale em privado com o mantenedor — nunca anexe dumps,
secrets ou dados de alvos reais. Detalhes em [`SECURITY.md`](SECURITY.md).

## Licença

MIT — veja [`LICENSE`](LICENSE).
