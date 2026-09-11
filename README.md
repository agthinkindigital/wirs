# WIRS - WordPress Incident Response Scanner

[![CI](https://github.com/agthinkindigital/wirs/actions/workflows/ci.yml/badge.svg)](https://github.com/agthinkindigital/wirs/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/agthinkindigital/wirs)](https://github.com/agthinkindigital/wirs/releases/latest)
[![Python](https://img.shields.io/badge/python-%3E%3D3.11-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-pre--alpha-orange)](#em-desenvolvimento)

O WIRS é um scanner read-only para resposta a incidentes em WordPress. Ele
combina integridade, indicadores e heurísticas em um relatório reproduzível,
sempre acompanhado pelas evidências e pela cobertura real da análise.

O objetivo não é emitir um veredito opaco de "infectado" ou "limpo". O WIRS
mostra o que observou, por que aquilo importa e quais verificações não puderam
ser concluídas.

> [![ENTENDA O WIRS](https://img.shields.io/badge/ENTENDA_O_WIRS-conceitos_e_decisões-21759B?style=for-the-badge)](docs/ENTENDENDO-O-WIRS.md)
>
> Aprenda como o scanner reconhece sinais de comprometimento e por que cada
> verificação foi desenhada dessa forma.

## Por que ele existe

Uma investigação de WordPress costuma juntar checksums, buscas manuais e
ferramentas desconectadas. No fim, é difícil provar o que foi verificado,
reproduzir a conclusão ou perceber o que ficou sem cobertura.

O WIRS organiza esse trabalho em três camadas que nunca se confundem:

1. **Fatos:** observações determinísticas, como hash divergente ou IOC literal.
2. **Suspeitas:** sinais heurísticos com possibilidade real de falso positivo.
3. **Diagnósticos:** hipóteses futuras baseadas na correlação dos findings.

Cada resultado inclui **Coverage**. Portanto, zero findings significa apenas
que nenhum finding atingiu o limite nas verificações que terminaram, não que o
site esteja necessariamente limpo.

## Disponível agora

A release [`v0.1.0`](https://github.com/agthinkindigital/wirs/releases/tag/v0.1.0)
entrega o primeiro fluxo operacional:

- inventário seguro de diretórios locais e snapshots;
- descoberta de WordPress e classificação de zonas;
- integridade oficial de core e plugins via WP-CLI opcional;
- detecção de arquivos inesperados no core e PHP em `uploads`;
- busca de IOCs literais em streaming;
- heurísticas PHP com severidade e confiança separadas;
- relatórios no terminal e em JSON canônico;
- redaction de secrets e Coverage explícito;
- perfis de recursos `soft`, `balanced` e `fast`;
- falha graciosa quando um provider não está disponível.

O `scan` nunca altera o alvo, não segue symlinks para fora da raiz e não
executa o código analisado. WP-CLI opera em modo seguro, anterior ao bootstrap,
nos providers usados pelo fluxo atual.

## Em desenvolvimento

A branch `develop` iniciou a linha `0.2.0`. O schema de manifests com trust
explícito já está implementado; comparação e uso desses manifests pelo scan
ainda estão em construção.

| Capacidade | Estado |
|---|---|
| Schema de baseline custom/premium | Em `develop` |
| Comparator e `baseline create` | Em desenvolvimento |
| Baseline seguro a partir de ZIP | Planejado para `0.2.0` |
| YARA e relatório Markdown | Planejado para `0.2.0` |
| Banco, cron e diagnósticos | Planejado para `0.3.0` |
| Wordfence CLI e Semgrep | Planejado para `0.4.0` |
| Snapshot remoto, SSH/SFTP | Planejado para `0.5.0` |

Veja o [roadmap](ORCHESTRATOR-ROADMAP.md), o [changelog](CHANGELOG.md) e a
[especificação viva](WIRS_MASTER_SPEC_PT-BR.md) para o escopo detalhado.

## Instalação

Pré-requisitos: [Git](https://git-scm.com/) e
[uv](https://docs.astral.sh/uv/). O `uv` prepara o ambiente Python 3.11+ usado
pelo projeto.

Instalação da release atual:

```bash
git clone --branch v0.1.0 --depth 1 https://github.com/agthinkindigital/wirs.git
cd wirs
uv tool install .
wirs version
```

O fluxo funciona em Windows, Linux e macOS. WP-CLI e PHP são opcionais, mas
necessários para verificar checksums oficiais de uma instalação WordPress.
Quando ausentes, o scan continua e registra a lacuna no Coverage.

Confira o ambiente antes do primeiro scan:

```bash
wirs doctor
```

## Primeiro scan

Analise um diretório ou snapshot local:

```bash
wirs scan /srv/www/site
```

Use o perfil conservador e gere JSON para automação:

```bash
wirs scan /srv/www/site --profile soft --format json
```

Adicione uma lista de IOCs no formato `kind:value`:

```bash
wirs scan /srv/www/site --ioc iocs.txt --fail-on high
```

Grave o relatório canônico em arquivo (sempre JSON, fora do alvo):

```bash
wirs scan /srv/www/site --format json --report ./scan.json
```

Sem `--report`, o JSON vai para o stdout (dá para redirecionar com `>`).
O arquivo existente é sobrescrito via escrita atômica: ou o report
completo está lá, ou nada foi escrito.

Um [relatório JSON de exemplo](docs/examples/scan-example.json) mostra o modelo
canônico sem exigir uma instalação WordPress local.

### Exit codes

| Código | Significado |
|---:|---|
| `0` | Nenhum finding atingiu o threshold nas verificações concluídas |
| `1` | Um finding atingiu o threshold configurado |
| `2` | Target ou argumento inválido |
| `3` | Scan incompleto por falha crítica de coleta |
| `4` | Erro interno do scanner |
| `5` | Regra ou configuração inválida |

## Como funciona

```text
target -> inventory -> WordPress discovery -> zones -> trusted integrity
       -> policies -> IOCs -> heuristics -> Coverage -> terminal / JSON
```

O barato e determinístico roda primeiro. Um arquivo confirmado por baseline
oficial não recebe heurísticas desnecessárias; um arquivo divergente continua
pela detecção para que evidências independentes possam se reforçar.

Falhas parciais degradam a cobertura em vez de esconder o problema ou abortar
toda a execução. A arquitetura completa está em
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Desenvolvimento

Prepare o checkout da branch `develop`:

```bash
git clone https://github.com/agthinkindigital/wirs.git
cd wirs
git switch develop
uv sync --extra dev
```

Execute os quality gates locais:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
```

### Estrutura

| Caminho | Papel |
|---|---|
| `src/wirs/domain/` | Modelo genérico puro, sem WordPress ou dependências externas |
| `src/wirs/application/` | Casos de uso e orquestração do scan |
| `src/wirs/ports/` | Contratos para fronteiras que realmente variam |
| `src/wirs/infrastructure/` | Filesystem, leitura, hashing e execução segura |
| `src/wirs/detectors/` | Regras internas sem subprocess ou execução do alvo |
| `src/wirs/providers/` | Integrações externas normalizadas por anti-corruption layer |
| `src/wirs/adapters/wordpress/` | Conhecimento específico de WordPress |
| `src/wirs/reporting/` | JSON canônico e views humanas read-only |
| `tests/` | Fixtures, testes unitários, integração, segurança, E2E e golden |

## Contribuindo

Toda contribuição começa por uma [Issue](https://github.com/agthinkindigital/wirs/issues)
com comportamento, critério de aceite e verificação reproduzível. O fluxo usa
TDD em slices verticais pequenos e QA ao final de cada DAG.

Leia [`AGENTS.md`](AGENTS.md) antes do primeiro PR. As decisões arquiteturais
estão em [`docs/adr/`](docs/adr/) e as invariantes de segurança não são
negociáveis.

## Segurança

Encontrou uma vulnerabilidade no scanner? Siga [`SECURITY.md`](SECURITY.md).
Nunca publique dumps, secrets, paths identificáveis ou dados de alvos reais em
uma Issue.

## Licença

MIT. Veja [`LICENSE`](LICENSE).
