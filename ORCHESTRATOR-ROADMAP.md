# Roadmap do WIRS

O GitHub Issue de cada Epic é a fonte detalhada. Este arquivo resume objetivo,
estado e ordem estratégica. IDs `E##` são estáveis e nunca reutilizados.

## Epics

- [**[E00] Fundação do Repositório**](https://github.com/agthinkindigital/wirs/issues/1) - `in_progress`

  Python importável, boundaries de arquitetura, CI, SECURITY.md, ADRs.
  Slices: #17 (WIRS-001, done), #18 (WIRS-002). (Fase A — Skeleton)

- [**[E01] Target e Artifact**](https://github.com/agthinkindigital/wirs/issues/2) - `in_progress`

  Target model, SafePath, Artifact model, inventory seguro, special files, type hints.
  Slices: #19 (WIRS-010), #20 (WIRS-011), #21 (WIRS-012), #22 (WIRS-013). (Fase A — Skeleton)

- [**[E02] Evidence, Findings e Coverage**](https://github.com/agthinkindigital/wirs/issues/3) - `in_progress`

  Schemas, severidade/confiança, Coverage model, Scan Manifest, versionamento.
  Slices: #23 (WIRS-020), #24 (WIRS-021), #25 (WIRS-023). (Fase A — Skeleton)

- [**[E03] Reader, Hashing e Resource Control**](https://github.com/agthinkindigital/wirs/issues/4) - `in_progress`

  ArtifactReader read-only, HashService, profiles (soft/balanced/fast),
  scheduler central, large-file policy, benchmark.
  Slices: #26 (WIRS-030), #27 (WIRS-031). (Fase A/B)

- [**[E04] Baseline e Integrity**](https://github.com/agthinkindigital/wirs/issues/5) - `todo`

  Manifest schema, comparator, `baseline create`, ZIP baseline, trust explícito.
  Issues: WIRS-040–WIRS-046. (Fase C)

- [**[E05] IOC e Rule Engine Genérico**](https://github.com/agthinkindigital/wirs/issues/6) - `todo`

  IOC schema, literal scanner, regex, zone policy engine, executable detector,
  PHP heuristics v0, entropy, rule metadata.
  Issues: WIRS-050–WIRS-058. (Fase B)

- [**[E06] WordPress Adapter**](https://github.com/agthinkindigital/wirs/issues/7) - `in_progress`

  Discovery, zones, versão/locale, doctor, core/plugin checksum providers,
  premium baseline, MU-plugins, upload policy, config collector.
  Slices FT-2: #30 (WIRS-060), #31 (WIRS-061), #32 (WIRS-063), #33 (WIRS-064),
  #34 (WIRS-065), #35 (WIRS-068). Restante (WIRS-062, 066, 067, 069–073): fatiar na Fase D.
  Issues: WIRS-060–WIRS-069. (Fase B)

- [**[E07] External Analyzer Providers**](https://github.com/agthinkindigital/wirs/issues/8) - `todo`

  Contrato ExternalAnalyzer, YARA, Wordfence CLI, Semgrep (fase 2), sandbox.
  Issues: WIRS-080–WIRS-085. (Fase C/E)

- [**[E08] Reporting e Redaction**](https://github.com/agthinkindigital/wirs/issues/9) - `in_progress`

  JSON canônico, terminal Rich, redaction, Markdown, atomic writer, HTML
  skeleton com design tokens (ref. OWASP ZAP melhorado), SARIF (futuro).
  Views com lista de findings com cap + paginação e contadores ao vivo.
  Assets de demonstração (prints/GIF de runs reais) para o README quando houver
  detecção operando.
  Slices: #28 (WIRS-090). (Fase A/B/C)

- [**[E09] Diagnosis e Correlation**](https://github.com/agthinkindigital/wirs/issues/10) - `todo`

  Relation model, correlation engine, DX001–DX004, renderer, graph export (futuro).
  Diagnoses rendem "próximos checks" e recomendações de higiene (limpeza de
  arquivos/cache/banco como sugestão — remediação automática fora do scan).
  Issues: WIRS-100–WIRS-104. (Fase D)

- [**[E10] CLI e Configuração**](https://github.com/agthinkindigital/wirs/issues/11) - `in_progress`

  `wirs scan`, config schema, `wirs doctor`, verbose/debug, exit codes, progress/cancel.
  Progresso ao vivo no terminal (barra, contadores, arquivo atual, mensagens de
  etapa, erros somados na tela) em WIRS-113/115.
  Slices: #29 (WIRS-110). (Fase A)

- [**[E11] Hardening do Scanner**](https://github.com/agthinkindigital/wirs/issues/12) - `todo`

  CommandRunner obrigatório, output cap, env sanitizer, symlink/special suites,
  output injection tests, archive sandbox, regex fuzz, SBOM, rule signing.
  Issues: WIRS-120–WIRS-128. (contínuo)

- [**[E12] Snapshot e Remote**](https://github.com/agthinkindigital/wirs/issues/13) - `todo`

  Snapshot directory, archive target, SSH/SFTP read-only, snapshot manifest.
  Issues: WIRS-130–WIRS-136. (Fase F)

- [**[E13] PHP Generic**](https://github.com/agthinkindigital/wirs/issues/14) - `todo`

  Discovery, Composer inventory/baseline, zone policies, runtime config, rules.
  Issues: WIRS-140–WIRS-145. (Fase H)

- [**[E14] Runtime HTTP**](https://github.com/agthinkindigital/wirs/issues/15) - `todo`

  HTTP collector, redirects, origins, request profiles, correlação, browser provider.
  Issues: WIRS-150–WIRS-155. (Fase G)

- [**[E15] AI Analysis Opcional**](https://github.com/agthinkindigital/wirs/issues/16) - `todo`

  AnalysisPacket, redaction gate, LLM provider interface, prompt-injection-safe
  framing. Invariante: IA não modifica fatos determinísticos.
  Inclui resumo em linguagem humana + recomendação de próximos passos (opt-in,
  só sobre pacote redigido).
  Issues: WIRS-160–WIRS-164. (pós-1.0)

## Marcos

| Marco | Epics | Saída verificável |
|---|---|---|
| M1 Skeleton 0.0.x (Fase A) | E00, E01, E02, E03(parcial), E08(parcial), E10(parcial) | `wirs scan tests/fixtures/generic/clean_tree` produz report válido |
| M2 WordPress slice 0.1.0 (Fase B) | E05, E06, E10 | discovery + core/plugin integrity + zone policy + IOC + heurísticas + terminal/JSON |
| M3 Custom + YARA 0.2.0 (Fase C) | E04, E07(parcial) | operator baselines + YARA + Markdown |
| M4 Application state 0.3.0 (Fase D) | E09, DB (WIRS-070–073) | DB IOC + diagnoses iniciais |
| M5 Ecossistema 0.4.0 (Fase E) | E07 | Wordfence + Semgrep opcional |
| M6 Snapshot/Remote 0.5.0 (Fase F) | E12 | archive/snapshot + SSH read-only |

## Ordem de execução

1. FT-1 core seguro (E00, E01, E02, E03, E08-JSON, E10-scan).
2. FT-2 integridade WordPress (E06 + E05-policy).
3. FT-3 detection (E05 + E08-terminal + redaction).
4. FT-4 componentes customizados (E04).
5. Validar em fixtures/snapshots conhecidos antes de adicionar complexidade.

## Critério de done

Uma Epic só é `done` quando: critérios da Issue satisfeitos; testes citados
passam; segurança de output verificada; docs refletem o código; QA aprovou;
sem dependência crítica pendente.
