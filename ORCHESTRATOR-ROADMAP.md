# Roadmap do WIRS

O GitHub Issue de cada Epic é a fonte detalhada. Este arquivo resume objetivo,
estado e ordem estratégica. IDs `E##` são estáveis e nunca reutilizados.
O [Product Charter](docs/PRODUCT-CHARTER.md) define a North Star e os
horizontes; este arquivo não transforma uma visão futura em compromisso atual.

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
  #65 (WIRS-026, artifact canônico completo) foi concluída em schema 2.0; a
  próxima DAG começa em #66. A Epic pai permanece aberta para follow-ons do
  próprio domínio. (Fases A/C)

- [**[E03] Reader, Hashing e Resource Control**](https://github.com/agthinkindigital/wirs/issues/4) - `in_progress`

  ArtifactReader read-only, HashService, profiles (soft/balanced/fast),
  scheduler central, large-file policy, benchmark.
  Slices: #26 (WIRS-030, done), #27 (WIRS-031, done). #67 (WIRS-034,
  fontes locais grandes) fica depois do artifact canônico. (Fases A/B)

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

- [**[E07] External Analyzer Providers**](https://github.com/agthinkindigital/wirs/issues/8) - `in_progress`

  Contrato ExternalAnalyzer, YARA, Wordfence CLI, Semgrep (fase 2), sandbox.
  Inteligência de versões/higiene (componente desatualizado ou recurso
  essencial a remover) como *contexto*, nunca como prova de comprometimento.
  Slices 0.2.0: #60 (WIRS-080, done), #61 (WIRS-081, done), #62 (WIRS-082, done).
  Fechamento operacional: #66 (WIRS-086, YARA no `scan` + Coverage real),
  dependente de #65.
  Wordfence/Semgrep adiados até o fluxo forense local estar completo.
  Issues: WIRS-080–WIRS-086. (Fases C/H)

- [**[E08] Reporting e Redaction**](https://github.com/agthinkindigital/wirs/issues/9) - `in_progress`

  JSON canônico, terminal Rich, redaction, Markdown, atomic writer, HTML
  skeleton com design tokens (ref. OWASP ZAP melhorado), SARIF (futuro).
  Views com lista de findings com cap + paginação e contadores ao vivo.
  Assets de demonstração (prints/GIF de runs reais) para o README quando houver
  detecção operando.
  Slices: #28 (WIRS-090, done), #40 (WIRS-091, done), #41 (WIRS-092, done),
  #59 (WIRS-093, done), #53 (WIRS-094/WIRS-119, writer/export done). #80
  (WIRS-095, HTML forense) e #81 (WIRS-097, PDF opcional) ficam depois do
  artifact canônico e Diagnosis. (Fases A/B/C/F)

- [**[E09] Diagnosis e Correlation**](https://github.com/agthinkindigital/wirs/issues/10) - `todo`

  Relation model, correlation engine, DX001–DX004, renderer, graph export (futuro).
  Diagnoses rendem "próximos checks" e recomendações de higiene (limpeza de
  arquivos/cache/banco como sugestão — remediação automática fora do scan).
  WIRS-100–103 eram placeholders horizontais não publicados e foram substituídos
  pelos slices verticais abaixo; WIRS-104 (graph export) fica pós-1.0.
  Próximo slice: #77 (WIRS-106, Diagnosis file-centric por sinais convergentes),
  dependente de #65 e da content analysis bounded. Depois: #76 (WIRS-105,
  relações), #78 (WIRS-107, phishing/cloaking/backup) e #79 (WIRS-108,
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

- [**[E12] Incident Bundle, Snapshot e Archive Local**](https://github.com/agthinkindigital/wirs/issues/13) - `todo`

  Pasta local com manifesto de fontes/provenance + archive target sem extração
  insegura. Slices: #68 (WIRS-130), #69 (WIRS-131). SSH/SFTP foi removido do
  caminho pré-1.0; WIRS-135 foi incorporado a #68. (Horizonte B)

- [**[E13] PHP Generic**](https://github.com/agthinkindigital/wirs/issues/14) - `todo`

  Discovery, Composer inventory/baseline, zone policies, runtime config, rules.
  Primeiro slice: #70 (WIRS-140, scan PHP genérico local). (Horizonte B)

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

1. FT-1 core seguro (E00, E01, E02, E03, E08-JSON, E10-scan).
2. FT-2 integridade WordPress (E06 + E05-policy).
3. FT-3 detection (E05 + E08-terminal + redaction).
4. FT-4 componentes customizados (E04).
5. Validar em fixtures/snapshots conhecidos antes de adicionar complexidade.
6. Fechar artifact canônico (#65).
7. Hardening do destino `--report` (#82), independente de #65 (concluído).
8. Integrar YARA no scan (#66), após #65.
9. Content analysis bounded (#67 + WIRS-052/056/057/058).
10. Diagnosis file-centric (#77) → HTML filesystem-only (#80).
11. PHP genérico local (#70), sem depender de Incident Bundle ou logs.
12. Incident Bundle (#68) → archive (#69).
13. Evidence temporal (#71) → Coverage de logs (#72) → adapters locais (#73–75).
14. Relações (#76) → Diagnoses adicionais (#78) → contexto offline opcional (#79).
15. PDF opcional (#81), derivado do HTML.

SSH/SFTP, active HTTP, agentes residentes, streaming/SIEM e resposta automática
ficam pós-1.0 em seams separados.

## Critério de done

Uma Epic só é `done` quando: critérios da Issue satisfeitos; testes citados
passam; segurança de output verificada; docs refletem o código; QA aprovou;
sem dependência crítica pendente.
