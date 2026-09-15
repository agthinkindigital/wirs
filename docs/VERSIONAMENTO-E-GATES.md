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
| `0.5.0` | M7: relações, Diagnoses adicionais e laudo forense | futuro |
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

## Responsabilidade Documental

O roadmap define a ordem e os marcos; as Issues definem aceite e estado; este
documento define promoção e versão; o Changelog registra apenas o que chegou à
`main`. Divergências devem ser registradas antes da promoção, nunca resolvidas
alterando o número da versão por conveniência.
