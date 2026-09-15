# WIRS - WordPress Incident Response Scanner

[![CI](https://github.com/agthinkindigital/wirs/actions/workflows/ci.yml/badge.svg)](https://github.com/agthinkindigital/wirs/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/agthinkindigital/wirs)](https://github.com/agthinkindigital/wirs/releases/latest)
[![Python](https://img.shields.io/badge/python-%3E%3D3.11-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-pre--alpha-orange)](#em-desenvolvimento)

O WIRS é um scanner read-only para resposta a incidentes em aplicações web,
WordPress-first. Ele
combina integridade, indicadores e heurísticas com Coverage explícito. Findings
referenciam Evidence no modelo interno; a exportação autocontida dessas
evidências no artifact canônico está em desenvolvimento.

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
3. **Diagnósticos:** hipóteses baseadas na correlação dos findings; a primeira
   deve ser file-centric e ainda está em desenvolvimento.

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
- relatórios no terminal e em JSON determinístico;
- redaction de secrets e Coverage explícito;
- perfis de recursos `soft`, `balanced` e `fast`;
- falha graciosa quando um provider integrado não está disponível.

O `scan` nunca altera o alvo, não segue symlinks para fora da raiz e não
executa o código analisado. WP-CLI opera em modo seguro, anterior ao bootstrap,
nos providers usados pelo fluxo atual.

## Em desenvolvimento

A branch `develop` prepara a linha `0.2.0` (Horizonte A). Baselines
custom/premium, ZIP, trust/cache/assinatura, relatório Markdown e o provider/pack
YARA já existem. A próxima DAG deve primeiro completar o artifact canônico,
integrar YARA ao `scan` e aprofundar content analysis antes de promover logs ou
outras expansões.

| Capacidade | Estado |
|---|---|
| Baseline custom/premium + ZIP | Implementado em `develop` |
| Relatório Markdown | Implementado em `develop` |
| YARA provider + pack | Implementado isoladamente; integração no `scan` pendente |
| Content analysis bounded + Diagnosis file-centric | Próximo Horizonte A |
| PHP genérico, Incident Bundle e archive local | Horizonte B |
| Logs locais, Evidence temporal e adapters de hospedagem | Horizonte C |
| Correlação temporal, IP/ASN e laudo enriquecido | Horizonte C |
| Banco/cron WordPress e providers externos | Planejado após o fluxo forense local |
| SSH/SFTP, runtime ativo e plataforma contínua | Pós-1.0 |

Leia primeiro o [Product Charter](docs/PRODUCT-CHARTER.md). Veja também o
[roadmap](ORCHESTRATOR-ROADMAP.md), o [changelog](CHANGELOG.md) e a
[especificação viva](WIRS_MASTER_SPEC_PT-BR.md) para o escopo detalhado.

## Instalação

Escolha um caminho: **usar** (só o comando `wirs`) ou **desenvolver**
(código + testes). Nos dois, o pré-requisito é o [uv](https://docs.astral.sh/uv/):
no Windows, `scoop install uv` ou `winget install --id astral-sh.uv -e`.

### Só usar (recomendado para escanear)

Em qualquer pasta, rode:

```bash
uv tool install git+https://github.com/agthinkindigital/wirs@main
```

Feche e reabra o terminal (o instalador registra o `wirs` no PATH).
Confira:

```bash
wirs version
wirs doctor
```

Se o terminal disser que `wirs` não existe, ele abriu antes do registro
no PATH — feche tudo e abra de novo. O `wirs doctor` mostra os providers
opcionais (`wp`, `yara`, `wordfence`). No fluxo atual, somente providers WP-CLI
integrados ao `scan` registram ausência no Coverage; YARA entra nesse contrato
ao fechar a linha `0.2.0`, e Wordfence permanece planejado.

### Desenvolver

```bash
git clone https://github.com/agthinkindigital/wirs.git
cd wirs
git switch develop
uv sync --extra dev
uv run pytest
```

Detalhes do ambiente de dev em [Desenvolvimento](#desenvolvimento).

Por padrão o scan mostra o andamento em texto (`--cli`); com `--gui` abre
uma tela de acompanhamento. O progresso vai para o stderr, então o JSON
do stdout continua parseável por automação.

## Primeiro scan

O formato é sempre `wirs scan <pasta> [opções]`, onde `<pasta>` é o
diretório a analisar e toda opção com valor **exige o valor junto**
(`--report` sozinho falha — ele precisa do caminho do arquivo).

Exemplo completo no Windows (ajuste as pastas para as suas):

```bash
wirs scan "C:\sites\meu-wordpress" --format terminal --report "C:\Users\Voce\Downloads\wirs-reports\scan.json"
```

No Linux/macOS, a mesma ideia:

```bash
wirs scan /srv/www/site --format terminal --report ./scan.json
```

### Todas as opções do `scan`

| Opção | Preenchimento | Padrão | Efeito |
|---|---|---|---|
| `<pasta>` (argumento) | caminho do diretório | — | Alvo do scan (obrigatório) |
| `--profile` | `soft`, `balanced`, `fast` | `soft` | Orçamento de recursos (1 worker, limites de leitura) |
| `--format` | `terminal`, `json`, `markdown` | `terminal` | View de saída; JSON é o canônico |
| `--fail-on` | `info`, `low`, `medium`, `high`, `critical` | `high` | Severidade mínima para exit 1 |
| `--ioc` | caminho de arquivo `kind:value` | — | IOCs literais extras (ex.: `literal:eval(`) |
| `--baseline` | caminho de mapping JSON | — | `{dir: manifest}` do operador (premium/custom) |
| `--report` | caminho do arquivo | — | Grava o JSON canônico (fora do alvo, atômico) |
| `--cache-dir` | caminho do diretório | `~/.wirs/cache` | Cache de baselines do operador |
| `--sign-key` | caminho do arquivo-chave | — | Chave HMAC para manifests assinados |
| `--gui` | (flag) | — | Tela Rich de acompanhamento no stderr |
| `--cli` | (flag) | ligado | Guia textual de progresso no stderr |
| `--wizard` | (flag) | — | Assistente interativo: plataforma, formatos, target, confirmação |

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

### Outros comandos

| Comando | Para quê |
|---|---|
| `wirs doctor` | Ambiente e providers detectados (`wp`, `yara`, `wordfence`) |
| `wirs version` | Versão do scanner |
| `wirs baseline create <dir> --name X [--version V] [--output F]` | Manifest SHA-256 de um diretório limpo |

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
