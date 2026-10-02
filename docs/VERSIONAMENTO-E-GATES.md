# Versionamento e Gates de Promoção

Este documento define quando o trabalho do WIRS pode avançar de `develop` para
`main` e receber uma nova versão. Uma capability, uma Issue ou uma Epic isolada
não altera a versão por si só.

## Regra de Branches

- `develop` é a linha de desenvolvimento e deve ser atualizada continuamente
  com as mudanças aprovadas e verificadas que fizermos.
- `main` é a linha publicada. Só recebe uma promoção formal de `develop` depois
  dos gates da versão serem aprovados.
- Toda promoção para `main` deve gerar tag, release, Changelog e documentação
  sincronizados.
- Trabalho existente em `develop` não é automaticamente uma release. Enquanto a
  promoção não ocorrer, ele é trabalho pós-última versão publicada.

Fluxo normal:

```text
Issue/slice → testes/QA → develop atualizado
             → Epic/fase/marco fechado
             → gate da versão aprovado
             → promoção develop → main
             → tag + Release + Changelog
```

Não se deve trabalhar diretamente em `main` para implementar uma capability.

## SemVer do WIRS

O WIRS segue a forma `MAJOR.MINOR.PATCH`:

| Mudança | Forma | Regra |
|---|---|---|
| Correção compatível, documentação ou ajuste sem nova capacidade | `X.Y.Z` | incrementa `PATCH` |
| Capacidade coerente concluída, sem quebra de contrato | `X.Y.0` | incrementa `MINOR` |
| Quebra de CLI, schema, contrato ou promessa pública | `X.0.0` | incrementa `MAJOR` |

Assim, `0.2.X`, `0.X.Y`, `X.0.1`, `X.0.Z`, `X.1.Z` e `X.Y.Z` são releases
possíveis conforme o tipo de mudança. O número não descreve a quantidade de
features: descreve o conjunto de contratos e gates que foi promovido.

Família de versões suportada pelo processo:

```text
0.1.0 | 0.2.0 | 0.2.X | 0.X.0 | 0.X.1 | 0.X.Y |
X.0.0 | X.0.1 | X.0.Z | X.1.Z | X.Y.Z
```

## Gates em Camadas

### Gate de Slice/Issue

Uma Issue só pode ser marcada como concluída quando:

- critérios de aceite verificáveis estão implementados;
- testes positivos, negativos e de segurança aplicáveis passam;
- invariantes do WIRS permanecem preservadas;
- documentação de comportamento foi atualizada quando necessário;
- riscos e pendências estão registrados.

### Gate de Epic

Uma Epic só pode ser marcada como `done` quando todas as Issues necessárias e
seus critérios estão concluídos, a QA da DAG foi aprovada e não há dependência
crítica aberta. A Epic pai não é fechada porque uma slice filha terminou.

### Gate de Fase/Milestone

Uma fase ou milestone só fecha quando sua saída verificável no roadmap existe no
checkout, os testes citados são reproduzíveis e o conjunto de Epics previsto foi
avaliado. Capabilities antecipadas de outro horizonte não substituem os itens
faltantes da fase.

### Gate de Release

Antes de promover `develop` para `main`, confirmar:

1. versão-alvo e escopo estão escritos no roadmap;
2. todas as Epics e Issues que compõem a versão estão fechadas no GitHub;
3. QA da DAG e QA de release foram aprovadas;
4. suíte completa, lint, formatação, type-check, security gates e build passam;
5. fixtures/golden/E2E necessários foram executados;
6. schema, CLI, exit codes e compatibilidade estão documentados;
7. README, `CHANGELOG.md`, estado, matriz e guias afetados estão sincronizados;
8. nenhum provider ausente ou capability parcial está representado como
   cobertura completa;
9. tag e artefatos da release podem ser reproduzidos a partir de `main`.

Se qualquer item não estiver confirmado, a versão não é promovida. O estado
correto é “develop atualizado, release ainda não elegível”.

## Mapa de Releases

Este mapa associa versões a conjuntos coerentes de marcos, não a uma feature
isolada:

| Versão | Conjunto mínimo | Situação |
|---|---|---|
| `0.1.0` | M2: primeiro fluxo WordPress operacional | publicada em `main` |
| `0.2.0` | M3/M4: artifact canônico, baselines/YARA, content analysis e Diagnosis | em preparação em `develop`; gates não promovidos |
| `0.3.0` | M5: Incident Bundle, archive local e PHP genérico | não elegível só por PHP coverage |
| `0.4.0` | M6: Evidence temporal e logs locais com Coverage de retenção | futuro |
| `0.5.0` | M7: relações, Diagnoses adicionais e laudo forense | futuro (subset filesystem de relações em `develop` desde 2026-10-02) |
| `0.6.0` | M8: estado WordPress e ecossistema externo previsto | futuro |
| `0.7.0` | external ecosystem conforme escopo aprovado | futuro |
| `0.8.x–0.9.x` | hardening, compatibilidade e preparação de estabilidade | futuro |
| `1.0.0` | CLI/schema estáveis, engine genérico, adapters e evidências locais maduras | futuro |

O fato de PHP genérico estar implementado em `develop` não torna o produto
`0.5.0`: a versão `0.5.0` depende do conjunto M7, e PHP genérico pertence ao
conjunto M5/`0.3.0` junto das demais entradas necessárias.

## Estado Atual

- `main`: `0.1.0`, última versão publicada.
- `develop`: trabalho pós-`0.1.0`, incluindo slices locais de `0.2.0` e o início
  de M5; ainda não é uma versão publicada.
- Próxima decisão de promoção: fechar e auditar o conjunto completo de `0.2.0`,
  não promover por causa de uma capability isolada.

## Estado de execução

Esta seção registra o estado do worktree atual como fato, separado da auditoria de
elegibilidade de versão que segue abaixo. Um LLM ou analista que ler este documento
primeiro deve ler esta seção para saber em que ponto do desenvolvimento se encontra
o WIRS antes de interpretar a auditoria.

- `main`: tag `0.1.0` publicada (última versão publicada).
- `develop`: trabalhando para `0.2.0` (M3/M4).

### Epics em estado atual

- E00 (Fundação do Repositório) — `in_progress`. Slices: #17 (done), #18 (aberto).
- E01 (Target e Artifact) — `in_progress`. Slices: #19–#22 (nenhum fechado).
- E02 (Evidence, Findings e Coverage) — `in_progress`. Slices concluídos: #23, #24,
  #25, #65, #66. Próximo slice dentro do epícilio: #67 (WIRS-034, fontes locais
  grandes).
- E03 (Reader, Hashing e Resource Control) — `in_progress`. Slices concluídos: #26,
  #27, #67. Próximo slice dentro do epícilio: #67 (já concluído).
- E04 (Baseline e Integrity) — `done`. Todos os slices (#40–#46) concluídos.
- E05 (IOC e Rule Engine Genérico) — `in_progress`. Slices FT-3: #36–#39 (nenhum
  fechado). Restante (WIRS-052, 056–058): a fatiar.
- E06 (WordPress Adapter) — `in_progress`. Slices FT-2: #30–#35 (nenhum fechado).
- E07 (External Analyzer Providers) — `done`. Slices 0.2.0: #60, #61, #62, #66
  concluídos.
- E08 (Reporting e Redaction) — `in_progress`. Slices concluídos: #28, #40, #41,
  #59, #53, #80 (fechada).
- E09 (Diagnosis e Correlation) — `todo`. #77 fechada; #76 fechada (subset
  filesystem, P2 / Horizonte F); depois: #78 (bloqueada por #75) → #79.
- E10 (CLI e Configuração) — `in_progress`. Slices: #29 (done); orquestrador:
  #42, #43 (done); flag --ioc: #44 (aberto); UX validação: #53–#55 (done).
- E11 (Hardening do Scanner) — `todo`. Slice entregue: #46 (done). #82
  (WIRS-123) foi concluído; restante em backlog.
- E12 (Incident Bundle, Snapshot e Archive Local) — `done`. #68 (WIRS-130) está
  done; #69 (WIRS-131) ainda não entregue formalmente.
- E13 (PHP Generic) — `done`. #70 (WIRS-140, PHP discovery) está done; zonas,
  Composer e runtime config (P3) não estão implementados.
- E14 (Runtime HTTP) — `todo` (pós-1.0).
- E15 (AI Analysis Opcional) — `todo` (pós-1.0).
- E16 (Evidência Temporal e Ingestão de Logs) — `todo`.
- E17 (Adapter de Hospedagem Local) — `todo`.

### Canal de desenvolvimento atual

- Branch: `develop`.
- Próximo slice a atacar: **#78 (WIRS-107)** — bloqueada por #75; #76 foi
  fechada em 2026-10-02.
- Commit de referência: `074677c` (CI verde em [35006528607](https://github.com/agthinkindigital/wirs/actions/runs/35006528607)).
- Não tocar em #69, #71, #72, #73–75, #81, nem qualquer trabalho pós-1.0 até
  a sequência de Diagnosis estar entregue formalmente (#76 entregue em
  2026-10-02).

## Auditoria de Elegibilidade — 2026-09-15

**Resultado: NÃO ELEGÍVEL para promoção de `0.2.0` neste momento.**

| Gate | Resultado | Evidência/pendência |
|---|---|---|
| Escopo e versão-alvo | parcial | Este documento define `0.2.0`, mas o marco M3/M4 ainda não está fechado no tracker |
| Issues da versão | bloqueado | #77 e #80 continuam abertas; #67 está fechada, mas seu checklist de aceite no GitHub permanece desmarcado |
| Epics da versão | bloqueado | E02, E03, E07, E08 e E09 continuam `OPEN`/`in_progress` no GitHub |
| QA técnico local | aprovado | `216 passed, 10 skipped`; Ruff, formatação, mypy strict e build passaram |
| CI de `develop` | aprovado | Execução [35006528607](https://github.com/agthinkindigital/wirs/actions/runs/35006528607) verde para `074677c` |
| Artefato versionado | bloqueado | O build atual produz `wirs-0.1.0`; ainda não existe build/tag/release `0.2.0` |
| Reprodução a partir de `main` | bloqueado | `develop` contém trabalho posterior a `main`; a promoção ainda não foi aprovada |
| Release GitHub | bloqueado | A única release publicada é `v0.1.0` |

Para liberar `0.2.0`, ainda é necessário concluir/validar as Issues que compõem
M3/M4, sincronizar checklists e estados das Epics no GitHub, manter o commit
aprovado em `develop`, executar o gate de release e só então atualizar a versão
do pacote (`pyproject.toml` e `wirs.__version__`), promover para `main`, criar a
tag/release e atualizar o Changelog.

### Decisão Operacional

O próximo trabalho deve fechar o conjunto de `0.2.0` antes de iniciar a próxima
versão. Em particular, a implementação local de #77 e #80 precisa passar pelo
fluxo de Issue/QA e ser incorporada ao `develop`; não basta o código existir no
worktree. A CI verde do commit anterior de `develop` não valida mudanças locais
não commitadas.

### Atualização — 2026-10-02 (sem reescrever a auditoria acima)

Entradas que mudaram desde 2026-09-15, verificadas no tracker: #77 e #80 estão
fechadas; #76 (subset filesystem, P2 / Horizonte F) e #70 estão fechadas. O
veredito de elegibilidade continua pendente de reavaliação formal: seguem
abertos o fechamento do conjunto M3/M4 no tracker, o build/tag/release
`0.2.0` e a CI do `develop` atual.

## Responsabilidade Documental

O roadmap define a ordem e os marcos; as Issues definem aceite e estado; este
documento define promoção e versão; o Changelog registra apenas o que chegou à
`main`. Divergências devem ser registradas antes da promoção, nunca resolvidas
alterando o número da versão por conveniência.

### Addendum de estado — 2026-10-02

O plano operacional auditado está em
[`docs/audits/GATE-0.2.0-PLANO-OPERACIONAL-2026-10.md`](audits/GATE-0.2.0-PLANO-OPERACIONAL-2026-10.md), publicado no commit `ddf1a94`.

- A linha publicada continua `main`/`v0.1.0`; não houve promoção, mudança de
  versão ou atualização do Changelog.
- O alvo de promoção continua `0.2.0`, não `0.1.1`: M3/M4 incluem capacidades
  coerentes e schema canônico 2.0, não apenas uma correção compatível de patch.
- `main` e `develop` estão divergentes (`ahead_by=42`, `behind_by=6`); nenhuma
  promoção pode presumir fast-forward.
- #68 permanece fora de M3/M4; #75 continua bloqueando #78; #78 e #79 não serão
  implementadas nesta execução.
- #84 e #87 continuam P1 abertos e são blockers de release até decisão formal e
  evidência futura. Não foram fechados nem implementados.
- A CI do candidato anterior falhou no `ruff format --check` em quatro arquivos.
  Por decisão explícita, a formatação não foi corrigida nesta execução; o gate
  de CI permanece vermelho e não é tratado como sucesso.

Este addendum atualiza o estado operacional sem reescrever a auditoria histórica
de 2026-09-15 acima.
