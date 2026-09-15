# Product Realignment Audit

## Baseline

- Branch: `develop`
- Commit: `5175b75cb525ba4106a8b306687b190559965b0c`
- Data: 2026-09-15
- Produto verificado: `wirs 0.1.0`
- Issues analisadas: Epics #1–#16 e slices abertas #63–#82, além dos slices
  concluídos que sustentam o estado 0.1.0.
- Documentos analisados: Charter, prompt, spec, contexto, arquitetura, ADRs,
  roadmap, estado, README, changelog, providers, material ANFAMOTO, matriz e
  mapa de skills.
- Módulos analisados: domain, application, ports, infrastructure, detectors,
  providers, adapters/wordpress, reporting, CLI e testes/CI.

## North Star validada

O WIRS é um scanner read-only de segurança, integridade e código suspeito para
aplicações web, WordPress-first, com core genérico. O resultado operacional é
uma shortlist pequena, priorizada, reproduzível e explicável de Artifacts que
merecem revisão humana. Logs, IP, SSH e IA enriquecem o modelo em horizontes
posteriores; não fundam nem bloqueiam o scanner local.

## O que já estava correto

- O domínio é genérico e a semântica WordPress está no adapter.
- O caminho local é read-only, com SafePath, symlink sem follow e arquivos
  especiais sem leitura como arquivo comum.
- Evidence, Finding, Coverage, severidade e confiança estão modelados.
- Baseline ausente permanece `UNVERIFIED` e não elimina content analysis.
- IOC streaming, heurísticas combinadas, policy de uploads e redaction existem.
- YARA foi isolado como provider opcional, sem execução do Target.
- JSON, terminal e Markdown já são tratados como reporting separado do domínio.
- A decisão de manter Incident Bundle local antes de SSH está registrada no
  ADR-011.

## Drifts encontrados

| ID | Local | Tipo | Evidência | Impacto | Ação |
|---|---|---|---|---|---|
| DRIFT-01 | `src/wirs/reporting/canonical.py` e CLI | IMPLEMENTATION_DRIFT | O JSON publica findings/coverage, mas descarta Artifacts/Evidence; refs não resolvem. | Cadeia de prova canônica incompleta. | Manter #65 como primeira gate; não declarar concluído. |
| DRIFT-02 | `src/wirs/application/orchestrator.py` | IMPLEMENTATION_DRIFT | Integrity Findings usam path em `artifact_ref`; detectores usam ID. | Correlação e referencialidade divergentes. | Registrar em #65; corrigir na implementação futura. |
| DRIFT-03 | `src/wirs/providers/yara_provider.py`, CLI e CI | IMPLEMENTATION_DRIFT | Provider isolado, sem integração no scan; falhas por arquivo são descartadas; CI não prova YARA real. | YARA não entrega valor operacional nem Coverage honesto. | Manter #66 após #65; registrar lacunas no provider doc. |
| DRIFT-04 | `src/wirs/application/orchestrator.py` | IMPLEMENTATION_DRIFT | Heurísticas/content hints recebem somente `head` de 64 KiB. | Backdoor posterior pode escapar. | Promover content analysis bounded para a DAG após #66. |
| DRIFT-05 | `src/wirs/application/orchestrator.py` | IMPLEMENTATION_DRIFT | Coverage registra filesystem, não a cobertura individual de content analysis. | Zero findings pode parecer mais abrangente do que é. | Exigir Coverage por capability na Issue futura. |
| DRIFT-06 | `src/wirs/application/orchestrator.py` | IMPLEMENTATION_DRIFT | Não existe Diagnosis file-centric. | Falta a shortlist correlacionada prevista na North Star. | Reposicionar #77 para file-centric. |
| DRIFT-07 | `src/wirs/adapters/wordpress/` | IMPLEMENTATION_DRIFT | MU-plugin, config, themes, cache e version/locale ainda são parciais. | WordPress-first ainda não é adapter forte completo. | Retirar dependência de logs; priorizar no roadmap. |
| DRIFT-08 | `src/wirs/adapters/` e CLI | IMPLEMENTATION_DRIFT | Não há PHP Generic real nem comando de adapter específico. | Expansão natural ainda não está implementada. | Promover #70 sem depender de Incident Bundle. |
| DRIFT-09 | `src/wirs/reporting/` | IMPLEMENTATION_DRIFT | HTML/PDF não existem. | Laudo ainda é futuro, mas blockers não podem exigir logs. | Desbloquear #80 para filesystem-only; manter #81 posterior. |
| DRIFT-10 | CI e testes | DEAD_REFERENCE | Vários caminhos de teste declarados nas Issues não existem; `tests/e2e` está vazio. | Aceites não são reproduzíveis no checkout. | Corrigir comandos nas Issues e não inventar evidência. |
| DRIFT-11 | Roadmap e Epics E06/E09/E12/E13/E16/E17 | PRIORITY_DRIFT | Logs/cPanel estavam P1 e WordPress/file-centric estavam depois deles. | DAG promovia produto lateral e atrasava o scanner. | Reclassificar horizontes e dependências. |
| DRIFT-12 | #70, #76, #77, #80 | DEPENDENCY_DRIFT | PHP dependia de bundle; Diagnosis dependia de logs; HTML dependia de logs/host. | Capacidades centrais eram bloqueadas por enriquecimentos. | Remover blockers laterais; preservar dependências reais. |
| DRIFT-13 | Documentação | DOC_DRIFT | Charter e matriz inexistiam; material de melhoria ficava fora de `future/` e `case-studies/`. | Não havia fonte curta de direção nem ownership documental. | Criar/mover artefatos e matriz preenchida. |
| DRIFT-14 | `AGENTS.md`/`docs/README.md` | DOC_DRIFT | Autoridade linear não distinguia produto, código, roadmap e case study. | Agentes podiam usar fonte errada para priorizar. | Adotar autoridade por assunto e gate anti-deriva. |
| DRIFT-15 | `ESTADO_ORQUESTRATOR.md` | DOC_DRIFT | Snapshot tinha branch/data/próximos passos inconsistentes. | Estado operacional induzia a próxima DAG errada. | Regenerar snapshot com branch/commit atual. |
| DRIFT-16 | `WIRS_MASTER_SPEC_PT-BR.md` | DEAD_REFERENCE | Estrutura listava `threat-model.md`, `reports.md` e outros arquivos ausentes. | Referências normativas quebradas. | Ajustar a estrutura para docs existentes; não criar docs vazios. |

## Mudanças feitas

- Criado `docs/PRODUCT-CHARTER.md` como North Star normativa curta.
- Criado `docs/DOCUMENTATION-MATRIX.md` preenchido com autoridade, horizonte,
  upstream/downstream, drift e ação.
- Criado este relatório de auditoria.
- Movidos os documentos de melhoria para `docs/future/` e
  `docs/case-studies/`, preservando conteúdo e classificação.
- Atualizados `AGENTS.md`, `docs/README.md`, `README.md`,
  `docs/ARCHITECTURE.md`, `docs/ENTENDENDO-O-WIRS.md`, roadmap, estado e spec.
- Realinhados bodies, labels, prioridades e dependências no GitHub sem fechar
  Epics pai.
- Mantido o ajuste local já existente de rejeição de symlink em `--report`,
  rastreado em #82; nenhuma nova feature de produto foi implementada.

## Issues repriorizadas

| Issue | Antes | Depois | Motivo | Dependências corrigidas |
|---|---|---|---|---|
| E07/#8 | P1 | P0 no tranche YARA | YARA no scan é content/signature core. | Wordfence/Semgrep permanecem posteriores. |
| E13/#14 | P3 | P1 | PHP Generic é expansão natural direta do scanner. | #70 deixa de depender de #68. |
| E12/#13, #68, #69 | P2/P1 | P2 | Bundle/archive local é útil, mas não funda o scanner. | Não bloqueia #70. |
| E16/E17/#63–#75 | P1 | P2/Horizonte C | Logs e hospedagem são enriquecimento opcional. | Permanecem depois do core e sem rede. |
| E09/#10, #76 | P1 | E09-A P1 / E09-B P2 | Diagnosis file-centric precisa vir antes da temporal/host. | #77 não depende de #76; #76 depende de logs. |
| #77 | P1 host-centric | P1 file-centric | Mesmo Artifact + sinais do scan já entrega valor. | Removidos blockers de logs/relations host-centric. |
| #80 | P1 com blockers #72/#77/#78 | P1 após #65 | HTML deve renderizar filesystem-only e `diagnoses: []`. | Removidos blockers opcionais. |
| #81 | P2 | P2 | PDF continua extensão opcional. | Depende apenas de #80. |

## Documentos atualizados

- `docs/PRODUCT-CHARTER.md`
- `docs/DOCUMENTATION-MATRIX.md`
- `docs/PROMPT-REALINHAMENTO-WIRS.md`
- `docs/README.md`
- `docs/ARCHITECTURE.md`
- `docs/ENTENDENDO-O-WIRS.md`
- `docs/future/WIRS-MELHORIAS.md`
- `docs/case-studies/ANFAMOTO-GAPS.md`
- `AGENTS.md`
- `docs/agents/README.md`
- `docs/agents/architecture.md`
- `docs/agents/workflow.md`
- `CONTEXT.md` não foi alterado: o vocabulário existente é suficiente.
- `WIRS_MASTER_SPEC_PT-BR.md`
- `ORCHESTRATOR-ROADMAP.md`
- `ESTADO_ORQUESTRATOR.md`
- `README.md`

## Itens preservados deliberadamente

- WordPress como primeiro adapter.
- `UNVERIFIED` para ausência de baseline.
- Separação entre integrity path e content-security path.
- YARA opcional, sem execução do Target.
- Incident Bundle/archive local como expansão, sem SSH pré-1.0.
- E14/HTTP e E15/IA em horizonte posterior.
- Histórico das Issues e dos IDs E##; nenhuma Epic pai foi fechada.

## Dívidas não corrigidas nesta auditoria

- Implementar #65 e #66 não faz parte desta execução.
- Content analysis além de `head` ainda não foi implementada.
- Diagnosis file-centric ainda não foi implementada.
- WordPress completo, PHP Generic e HTML ainda não existem no código atual.
- Testes referenciados por várias Issues ainda precisam ser criados ou
  substituídos por comandos reais.
- Teste de symlink do #82 continua dependente de ambiente com privilégio; neste
  Windows ele é pulado.
- YARA real e WP-CLI real não são verificáveis neste host sem as dependências.

## Próxima DAG recomendada

1. **#65 — Artifact canônico completo (P0, HITL).** Primeiro porque todas as
   views, YARA e correlação precisam de refs resolvíveis, Evidence e provider
   status no mesmo modelo.
2. **#82 — Hardening do destino `--report` (P0, AFK).** Independente de #65 e
   protege a invariante de não escrita no Target.
3. **#66 — YARA no `scan` (P0, AFK após #65).** Transforma o provider isolado em
   capacidade real com Evidence, status e Coverage honesto.
4. **#67 — Content analysis bounded/profile soft (P1).** Remove a dependência
   exclusiva do `head` sem carregar arquivos grandes arbitrariamente.
5. **E05/E06 file-centric restantes (P0/P1).** Completar rules, config,
   MU-plugins, themes, cache e políticas de WordPress sem esperar logs.
6. **#77 — Diagnosis file-centric (P1).** Correlacionar sinais do mesmo
   Artifact antes de qualquer actor, IP ou timeline.
7. **#80 — HTML self-contained (P1).** Renderizar o modelo canônico mesmo sem
   logs, timeline ou diagnoses.
8. **#70 — PHP Generic local (P1).** Reusar o mesmo engine e funcionar com
   `wirs scan ./legacy-php`, sem bundle, SSH ou logs.
9. **#68 → #69 — Bundle/archive local (P2/Horizonte B).** Entradas locais úteis,
   mas independentes do PHP Generic.
10. **#71 → #75 e #76/#78/#79 (P2/Horizonte C).** Logs, relações temporais,
    adapters de hospedagem e contexto IP somente após o núcleo.
11. **#81 — PDF opcional (P2).** Derivar do HTML sem regra de negócio própria.

## Verification

- Auditoria de checkout: branch `develop`, commit `5175b75`.
- GitHub: Epics e slices abertas consultadas via `gh`; #65/#66/#82 confirmadas.
- Skills exigidas pelo prompt lidas antes da auditoria: `zoom-out`,
  `grill-with-docs`, `grill-feature-with-docs`, `requirements-clarity`,
  `improve-codebase-architecture`, `roadmap`, `triage`, `to-issues`,
  `agent-md-refactor`, `crafting-effective-readmes`, `edit-article`,
  `writing-clearly-and-concisely`, `qa-analyst` e `orchestrator`.
- Antes desta auditoria, a suíte registrada no checkout passou: `181 passed,
  6 skipped`; ruff, format, mypy e `git diff --check` passaram. Os skips são
  limitações conhecidas de symlink/FIFO/WP-CLI neste Windows.
- A execução não implementou #65, #66, PHP Generic, HTML, Diagnosis, logs ou
  SSH.
