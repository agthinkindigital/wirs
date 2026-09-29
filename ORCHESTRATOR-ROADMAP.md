# Roadmap do WIRS

O GitHub Issue de cada Epic é a fonte detalhada. Este arquivo resume objetivo,
estado e ordem estratégica. IDs `E##` são estáveis e nunca reutilizados.
O [Product Charter](docs/PRODUCT-CHARTER.md) define a North Star e os
horizontes; este arquivo não transforma uma visão futura em compromisso atual.
Promoção entre `develop` e `main`, e os gates de versão, seguem
[`docs/VERSIONAMENTO-E-GATES.md`](docs/VERSIONAMENTO-E-GATES.md).

## Status de execução atual

- Versão publicada: `0.1.0` (`main`).
- Versão em desenvolvimento: `0.2.0` (`develop`, não promovida).
- Próximo slice formal a entregar: **#76 (WIRS-105, relações)** — predecessor de #78 e #79.
- Próximo marco: **M4 — Content analysis + Diagnosis (Horizonte A)**.
- Commit de referência para `develop`: `074677c` (CI verde: [35006528607](https://github.com/agthinkindigital/wirs/actions/runs/35006528607)).

## Próximos passos (sequência linear única)

O próximo trabalho é **#76 (WIRS-105, relações)** — precede #78 e #79. Ele é o
próximo slice de Diagnosis após DX001 (#77) e do HTML filesystem-only (#80). Depende
apenas de #65 (artifact canônico, done) e da content analysis bounded entregue.

Após #76: #78 (WIRS-107, phishing/cloaking/backup) → #79 (WIRS-108, contexto
offline de IP/CIDR/UA).

Não iniciar #69, #71, #72, #73–75, #81, nem qualquer trabalho pós-1.0 até #76 e
a sequência de Diagnosis estarem entregues formalmente.

> **Nota:** itens marcados `(implementado_localmente)` no texto têm código no
> worktree, mas ainda não passaram por Issue/QA/promoção e não contam como entrega
> formal (ver [`docs/VERSIONAMENTO-E-GATES.md`](docs/VERSIONAMENTO-E-GATES.md)).

## Epics

- [**[E00] Fundação do Repositório**](https://github.com/agthinkindigital/wirs/issues/1) - `in_progress`

  Python importável, boundaries de arquitetura, CI, SECURITY.md, ADRs.
  Slices: #17 (WIRS-001, done), #18 (WIRS-002). (Fase A — Skeleton)

- [**[E01] Target e Artifact**](https://github.com/agthinkindigital/wirs/issues/2) - `in_progress`

  Target model, SafePath, Artifact model, inventory seguro, special files, type hints.
  Slices: #19 (WIRS-010), #20 (WIRS-011), #21 (WIRS-012), #22 (WIRS-013). (Fase A — Skeleton)

- [**[E02] Evidence, Findings e Coverage**](https://github.com/agthinkindigital/wirs/issues/3) - `in_progress`

  Schemas, severidade/confiança, Coverage model, Scan Manifest, versionamento.
  Slices: #23 (WIRS-020, done), #24 (WIRS-021, done), #25 (WIRS-023, done).
  #65 (WIRS-026, artifact canônico completo) foi concluída em schema 2.0 e #66
  (WIRS-086, YARA no `scan`) também foi concluída. A próxima DAG é #67. A Epic
  pai permanece aberta para follow-ons do próprio domínio. (Fases A/C)

  Status interno: 5 slices concluídos (#23, #24, #25, #65, #66); próximo slice
  dentro do epícilio é #67 (WIRS-034, fontes locais grandes, done).

- [**[E03] Reader, Hashing e Resource Control**](https://github.com/agthinkindigital/wirs/issues/4) - `in_progress`

  ArtifactReader read-only, HashService, profiles (soft/balanced/fast),
  scheduler central, large-file policy, benchmark.
  Slices: #26 (WIRS-030, done), #27 (WIRS-031, done), #67 (WIRS-034, fontes
  locais grandes, done). (Fases A/B)

  Status interno: 3 slices concluídos (#26, #27, #67); próximo slice dentro do
  epícilio é #67 (WIRS-034, fontes locais grandes, done).

- [**[E04] Baseline e Integrity**](https://github.com/agthinkindigital/wirs/issues/5) - `done`

  Manifest schema, comparator, `baseline create`, ZIP baseline, trust explícito.
  Premium/custom nunca é skip: baseline do operador (ZIP/manifest) + código
  sempre submetido a heurísticas/IOC + UNVERIFIED com detalhes acionáveis para
  decisão humana.
  Slices FT-4: #48 (WIRS-040, done), #49 (WIRS-041, done), #50 (WIRS-042, done),
  #51 (WIRS-043, done), #52 (WIRS-066, done). Fase C: #56 (WIRS-044, done),
  #57 (WIRS-045, done), #58 (WIRS-046, done). E04 completo.
  Issues: WIRS-040–WIRS-046. (Fase C)

- [**[E05] IOC e Rule Engine Genérico**](https://github.com/agthinkindigital/wirs/issues/6) - `in_progress`

  IOC schema, literal scanner, regex, zone policy engine, executable detector,
  PHP heuristics v0, entropy, rule metadata.
  Scan em fases: corpo primeiro, cache (regenerável) como etapa adicional sob
  demanda/flag — se nada no corpo, vale consultar o cache antes de encerrar.
  Slices FT-3: #36 (WIRS-050), #37 (WIRS-051), #38 (WIRS-054), #39 (WIRS-055).
  Restante (WIRS-052, 056, 057, 058): bounded content analysis, a fatiar
  depois de #65 e antes de Diagnosis. (Fase A/B)
  Issues: WIRS-050–WIRS-058. (Fase B)

- [**[E06] WordPress Adapter**](https://github.com/agthinkindigital/wirs/issues/7) - `in_progress`

  Discovery, zones, versão/locale, doctor, core/plugin checksum providers,
  premium baseline, MU-plugins, upload policy, config collector.
  Slices FT-2: #30 (WIRS-060), #31 (WIRS-061), #32 (WIRS-063), #33 (WIRS-064),
  #34 (WIRS-065), #35 (WIRS-068). WIRS-066 foi entregue como dependência
  cross-Epic em #52/E04. Restante (WIRS-062, 067, 069–073): separar entre
  file-centric no Horizonte A/B e runtime/state posterior. Nenhum item
  file-centric depende de logs, cPanel, E16 ou E17. (Fases B/G)

- [**[E07] External Analyzer Providers**](https://github.com/agthinkindigital/wirs/issues/8) - `done`

  Contrato ExternalAnalyzer, YARA, Wordfence CLI, Semgrep (fase 2), sandbox.
  Inteligência de versões/higiene (componente desatualizado ou recurso
  essencial a remover) como *contexto*, nunca como prova de comprometimento.
  Slices 0.2.0: #60 (WIRS-080, done), #61 (WIRS-081, done), #62 (WIRS-082, done),
  #66 (WIRS-086, done). YARA no `scan` publica Coverage real e dependeu de #65.
  Wordfence/Semgrep adiados até o fluxo forense local estar completo.
  (Fases C/H)

- [**[E08] Reporting e Redaction**](https://github.com/agthinkindigital/wirs/issues/9) - `in_progress`

  JSON canônico, terminal Rich, redaction, Markdown, atomic writer, HTML
  skeleton com design tokens (ref. OWASP ZAP melhorado), SARIF (futuro).
  Views com lista de findings com cap + paginação e contadores ao vivo.
  Assets de demonstração (prints/GIF de runs reais) para o README quando houver
  detecção operando.
  Slices: #28 (WIRS-090, done), #40 (WIRS-091, done), #41 (WIRS-092, done),
  #59 (WIRS-093, done), #53 (WIRS-094/WIRS-119, writer/export done). #80
  (WIRS-095, HTML forense filesystem-only, implementada localmente) e #81
  (WIRS-097, PDF opcional) ficam depois do artifact canônico e Diagnosis.
  (Fases A/B/C/F)

  Status interno: 5 slices concluídos (#28, #40, #41, #59, #53); #80
  (WIRS-095, HTML forense filesystem-only) é implementado localmente mas não
  formalizado; próximo slice dentro do epícilio é #80 após formalização.

- [**[E09] Diagnosis e Correlation**](https://github.com/agthinkindigital/wirs/issues/10) - `todo`

  Relation model, correlation engine, DX001–DX004, renderer, graph export (futuro).
  Diagnoses rendem "próximos checks" e recomendações de higiene (limpeza de
  arquivos/cache/banco como sugestão — remediação automática fora do scan).
  WIRS-100–103 eram placeholders horizontais não publicados e foram substituídos
  pelos slices verticais abaixo; WIRS-104 (graph export) fica pós-1.0.
  Próximo slice: #77 (WIRS-106, Diagnosis file-centric por sinais convergentes),
  dependente de #65 e da content analysis bounded já entregue. Depois: #76
  (WIRS-105, relações), #78 (WIRS-107, phishing/cloaking/backup) e #79 (WIRS-108,
  contexto offline de IP/CIDR/UA). (Fase A/B, depois F)

- [**[E10] CLI e Configuração**](https://github.com/agthinkindigital/wirs/issues/11) - `in_progress`

  `wirs scan`, config schema, `wirs doctor`, verbose/debug, exit codes, progress/cancel.
  Progresso ao vivo no terminal (barra, contadores, arquivo atual, mensagens de
  etapa, erros somados na tela) em WIRS-113/115.
  Slices: #29 (WIRS-110, done). Orquestrador: #42 (WIRS-116, done), #43 (WIRS-117, done).
  Flag --ioc: #44 (WIRS-118). UX da sessão de validação: #53 (WIRS-119, --report/export, done),
  #54 (WIRS-129, wizard, done), #55 (WIRS-139, --gui/--cli + progresso, done).
  Restante (WIRS-111–115): config e progresso. (Fase A/B)

- [**[E11] Hardening do Scanner**](https://github.com/agthinkindigital/wirs/issues/12) - `todo`

  CommandRunner obrigatório, output cap, env sanitizer, symlink/special suites,
  output injection tests, archive sandbox, regex fuzz, SBOM, rule signing.
  Slice entregue: #46 (WIRS-120, resolução segura de commands/providers no
  Windows, done).
  #82 (WIRS-123, rejeição de symlink no destino de `--report`) foi concluída;
  os demais itens WIRS-120–WIRS-128 continuam no backlog. (contínuo)

- [**[E12] Incident Bundle, Snapshot e Archive Local**](https://github.com/agthinkindigital/wirs/issues/13) - `done`

  Pasta local com manifesto de fontes/provenance + archive target sem extração
  insegura. Slices: #68 (WIRS-130, done), #69 (WIRS-131). SSH/SFTP foi removido do
  caminho pré-1.0; WIRS-135 foi incorporado a #68. (Horizonte B)

  Status interno: #68 (WIRS-130) está done; #69 (WIRS-131, archive local) ainda
  não é entregue formalmente e depende de #68.

- [**[E13] PHP Generic**](https://github.com/agthinkindigital/wirs/issues/14) - `done`

  Discovery, Composer inventory/baseline, zone policies, runtime config, rules.
  Primeiro slice: #70 (WIRS-140, done). PHP discovery is delivered; zonas e Composer
  são P3 e chegam em iterações posteriores. (Horizonte B)

  Status interno: #70 (WIRS-140, PHP discovery) está done; zonas, Composer e
  runtime config são P3 e não estão implementados. Próximo trabalho possível é
  verificar e formalizar #70 antes de avançar para P3.

- [**[E14] Runtime HTTP**](https://github.com/agthinkindigital/wirs/issues/15) - `todo`

  HTTP collector, redirects, origins, request profiles, correlação, browser provider.
  Active HTTP não é parser de access log e fica pós-1.0.
  Issues: WIRS-150–WIRS-155. (pós-1.0)

- [**[E15] AI Analysis Opcional**](https://github.com/agthinkindigital/wirs/issues/16) - `todo`

  AnalysisPacket, redaction gate, LLM provider interface, prompt-injection-safe
  framing. Invariante: IA não modifica fatos determinísticos.
  Inclui resumo em linguagem humana + recomendação de próximos passos (opt-in,
  só sobre pacote redigido).
  Issues: WIRS-160–WIRS-164. (pós-1.0)

- [**[E16] Evidência Temporal e Ingestão de Logs**](https://github.com/agthinkindigital/wirs/issues/63) - `todo`

  Logs locais viram Evidence temporal (`occurred_at` ≠ `collected_at`) ligada ao
  Artifact/posição de origem. Parsing, rotação e retenção degradam Coverage.
  Slices: #71 (WIRS-170), #72 (WIRS-171). (Horizonte C)

- [**[E17] Adapter de Hospedagem Local**](https://github.com/agthinkindigital/wirs/issues/64) - `todo`

  cPanel access/login/session + web server/PHP logs já presentes no Incident
  Bundle, sem rede nem inferência de autoria no collector.
  Slices: #73 (WIRS-180), #74 (WIRS-181), #75 (WIRS-182). (Horizonte C)

## Marcos

| Marco | Epics | Saída verificável |
|---|---|---|
| M1 Skeleton 0.0.x (Fase A) — `done` | E00, E01, E02, E03(parcial), E08(parcial), E10(parcial) | `wirs scan tests/fixtures/generic/clean_tree` produz report válido |
| M2 WordPress slice 0.1.0 (Fase B) — `done` | E05, E06, E10 | discovery + core/plugin integrity + zone policy + IOC + heurísticas + terminal/JSON |
| M3 Artifact + YARA 0.2.0 (Horizonte A) | E02, E04, E07, E08 | artifact canônico + operator baselines + YARA no scan + Markdown |
| M4 Content analysis + Diagnosis (Horizonte A) | E03, E05, E09 | análise bounded + Diagnosis file-centric auditável |
| M5 Entradas forenses locais (Horizonte B) | E12, E13 | Incident Bundle + archive + PHP genérico |
| M6 Evidência temporal local (Horizonte C) | E16, E17 | logs locais → Evidence temporal + Coverage de retenção |
| M7 Correlação e laudo (Horizonte C) | E09, E08 | relações/Diagnoses + HTML/PDF forense |
| M8 Estado WordPress e ecossistema externo (posterior) | E06, E07, E11 | DB/config + Wordfence/Semgrep + sandbox |

## Ordem de execução

Esta seção é ao mesmo tempo **registro histórico** (como as coisas foram feitas)
e **guia de leitura** (o que foi entregue, o que ainda falta, e em que ordem o
trabalho avança):\

- itens com `(done)` ou `(implementado_localmente)` são histórico;
- itens com `(todo)` ou `(in_progress)` são próximos passos;
- a distinção entre `implementado_localmente` e entrega formal
  (Issue/QA/promoção) está na nota de rodapé ao final desta seção;
- o **planejamento formal** mora nos Epics deste arquivo, em
  [`docs/VERSIONAMENTO-E-GATES.md`](docs/VERSIONAMENTO-E-GATES.md) e nas Issues do GitHub;
  esta lista não substitui nenhum deles.

1. `(done)` FT-1 core seguro (E00, E01, E02, E03, E08-JSON, E10-scan).
2. `(done)` FT-2 integridade WordPress (E06 + E05-policy).
3. `(done)` FT-3 detection (E05 + E08-terminal + redaction).
4. `(done)` FT-4 componentes customizados (E04).
5. `(done)` Validar em fixtures/snapshots conhecidos antes de adicionar complexidade.
6. `(done)` Fechar artifact canônico (#65) — entregue em schema 2.0, refém do
   orquestrador e dos adapters de evidência.
7. `(done)` Hardening do destino `--report` (#82), independente de #65 (concluído).
8. `(done)` Integrar YARA no scan (#66), após #65 (done) — publica Coverage real e
   dependeu de #65.
9. `(done)` Content analysis bounded (#67), concluída.
10. `(implementado_localmente)` Diagnosis file-centric (#77) → HTML filesystem-only
    (#80), implementados localmente; **próximo slice formal** é #76
    (WIRS-105, relações) → #78 (WIRS-107, phishing/cloaking/backup) → #79
    (WIRS-108, contexto offline de IP/CIDR/UA); #80 deriva do artifact canônico.
11. `(implementado_localmente)` PHP genérico local (#70), implementado localmente
    como discovery by extension, sem depender de Incident Bundle ou logs; zonas e
    Composer são P3 e chegam em iterações posteriores.
12. `(implementado_localmente)` Incident Bundle (#68), implementado localmente →
    archive (#69) ainda não entregue formalmente.
13. `(todo)` Evidence temporal (#71) → Coverage de logs (#72) → adapters locais
    (#73–75).
14. `(todo)` Relações (#76) → Diagnoses adicionais (#78) → contexto offline opcional
    (#79).
15. `(todo)` PDF opcional (#81), derivado do HTML.

SSH/SFTP, active HTTP, agentes residentes, streaming/SIEM e resposta automática
ficam pós-1.0 em seams separados.

> **Nota de rodapé — implementado_localmente vs. entrega formal**
>
> Itens marcados `(implementado_localmente)` têm código no worktree atual, mas
> ainda não passaram pelo fluxo de Issue/QA e promoção de versão descrito em
> [`docs/VERSIONAMENTO-E-GATES.md`](docs/VERSIONAMENTO-E-GATES.md). Enquanto não
> passarem por esse fluxo, não contam como entrega formal da versão e não
> movem o marco correspondente no roadmap. A vantagem é que a base técnica já está
> quieta para quando o slice for formalmente aprovado; a ressalva é que o que está
> no worktree não é garantido até passar pelo gate.
>
> **Próximos slices não-entregues formalmente (forward-looking):**
>
> - #76 (WIRS-105, relações) → #78 (WIRS-107, phishing/cloaking/backup) → #79
>   (WIRS-108, contexto offline de IP/CIDR/UA) — sequência de Diagnosis pós-DX001.
> - #69 (WIRS-131, archive local) depende de #68 (Incident Bundle, já
>   implementado_localmente).
> - #71 (WIRS-170, Evidence temporal) → #72 (WIRS-171, Coverage de logs) →
>   #73–75 (WIRS-180–182, adapters locais).
> - #81 (WIRS-097, PDF opcional) deriva do HTML.
>
> SSH/SFTP, active HTTP, agentes residentes, streaming/SIEM e resposta automática
> permanecem pós-1.0 e não entram na sequência acima.

## Critério de done

Uma Epic só é `done` quando: critérios da Issue satisfeitos; testes citados
passam; segurança de output verificada; docs refletem o código; QA aprovou;
sem dependência crítica pendente.
