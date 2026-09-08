# Roadmap do WIRS

O GitHub Issue de cada Epic é a fonte detalhada. Este arquivo resume objetivo,
estado e ordem estratégica. IDs `E##` são estáveis e nunca reutilizados.
Issues serão criadas via `/to-issues` antes da execução de cada Epic.

## Epics

### [E00] Fundação do Repositório — `todo`

Python importável, boundaries de arquitetura, CI, SECURITY.md, ADRs.
Issues: WIRS-001–WIRS-005. (Fase A — Skeleton)

### [E01] Target e Artifact — `todo`

Target model, SafePath, Artifact model, inventory seguro, special files, type hints.
Issues: WIRS-010–WIRS-015. (Fase A — Skeleton)

### [E02] Evidence, Findings e Coverage — `todo`

Schemas, severidade/confiança, Coverage model, Scan Manifest, versionamento.
Issues: WIRS-020–WIRS-025. (Fase A — Skeleton)

### [E03] Reader, Hashing e Resource Control — `todo`

ArtifactReader read-only, HashService, profiles (soft/balanced/fast),
scheduler central, large-file policy, benchmark.
Issues: WIRS-030–WIRS-035. (Fase A/B)

### [E04] Baseline e Integrity — `todo`

Manifest schema, comparator, `baseline create`, ZIP baseline, trust explícito.
Issues: WIRS-040–WIRS-046. (Fase C)

### [E05] IOC e Rule Engine Genérico — `todo`

IOC schema, literal scanner, regex, zone policy engine, executable detector,
PHP heuristics v0, entropy, rule metadata.
Issues: WIRS-050–WIRS-058. (Fase B)

### [E06] WordPress Adapter — `todo`

Discovery, zones, versão/locale, doctor, core/plugin checksum providers,
premium baseline, MU-plugins, upload policy, config collector.
Issues: WIRS-060–WIRS-069. (Fase B)

### [E07] External Analyzer Providers — `todo`

Contrato ExternalAnalyzer, YARA, Wordfence CLI, Semgrep (fase 2), sandbox.
Issues: WIRS-080–WIRS-085. (Fase C/E)

### [E08] Reporting e Redaction — `todo`

JSON canônico, terminal Rich, redaction, Markdown, atomic writer, HTML
skeleton com design tokens (ref. OWASP ZAP melhorado), SARIF (futuro).
Issues: WIRS-090–WIRS-096. (Fase A/B/C)

### [E09] Diagnosis e Correlation — `todo`

Relation model, correlation engine, DX001–DX004, renderer, graph export (futuro).
Issues: WIRS-100–WIRS-104. (Fase D)

### [E10] CLI e Configuração — `todo`

`wirs scan`, config schema, `wirs doctor`, verbose/debug, exit codes, progress/cancel.
Issues: WIRS-110–WIRS-115. (Fase A)

### [E11] Hardening do Scanner — `todo`

CommandRunner obrigatório, output cap, env sanitizer, symlink/special suites,
output injection tests, archive sandbox, regex fuzz, SBOM, rule signing.
Issues: WIRS-120–WIRS-128. (contínuo)

### [E12] Snapshot e Remote — `todo`

Snapshot directory, archive target, SSH/SFTP read-only, snapshot manifest.
Issues: WIRS-130–WIRS-136. (Fase F)

### [E13] PHP Generic — `todo`

Discovery, Composer inventory/baseline, zone policies, runtime config, rules.
Issues: WIRS-140–WIRS-145. (Fase H)

### [E14] Runtime HTTP — `todo`

HTTP collector, redirects, origins, request profiles, correlação, browser provider.
Issues: WIRS-150–WIRS-155. (Fase G)

### [E15] AI Analysis Opcional — `todo`

AnalysisPacket, redaction gate, LLM provider interface, prompt-injection-safe
framing. Invariante: IA não modifica fatos determinísticos.
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
