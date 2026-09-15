# Estado do Orquestrador — WIRS

**Data:** 2026-09-15
**Branch:** `develop` (repo `agthinkindigital/wirs`, público)
**Commit:** `c08b284` (`feat(reporting): complete canonical scan report`)
**Framework:** skills locais; clone remoto do framework não foi encontrado neste checkout.

---

## Fase 0 — Pré-condições (ATENDIDAS)

- [x] Git inicializado (branch `main`)
- [x] Remote GitHub configurado (`origin` → `agthinkindigital/wirs`, público)
- [x] Acesso GitHub confirmado (`gh repo view` OK, conta `agthinkindigital`)
- [x] Toolchain: Python 3.14.7 (dev local), `uv` 0.12.5 via scoop, Node 24, PHP 8.3
- [x] Decisões de definição via grill: Python `>=3.11`, Typer+Rich, scaffold do zero, MIT, HTML skeleton desde o início

## Fase 1 — Provisionamento documental (CONCLUÍDA)

- [x] `AGENTS.md` (protocolo WIRS + 14 invariantes)
- [x] `CONTEXT.md` (glossário: core, confiança, baselines, zones WP)
- [x] `docs/agents/README.md` (domínio, tracker, triage)
- [x] `docs/adr/` (ADR-001..011 conforme Seção 14.13 do spec)
- [x] `ORCHESTRATOR-ROADMAP.md` (E00–E17)
- [x] Issues GitHub via `/to-issues`
- [x] Links Epic→Issue no roadmap
- [x] `docs/PRODUCT-CHARTER.md` e `docs/DOCUMENTATION-MATRIX.md`
- [x] Auditoria de realinhamento em `docs/audits/PRODUCT-REALIGNMENT-2026-09.md`
- [x] `docs/agents/architecture.md` e `docs/agents/workflow.md`

## Fase 2 — To-issues FT-1 (CONCLUÍDA)

- [x] Labels criadas (triage, tipos, áreas, prioridades)
- [x] 16 Epic issues: #1–#16 (E00–E15)
- [x] 13 slice issues FT-1: #17–#29, modo AFK, `ready-for-agent`, `Blocked by` reais
- [x] #17 (WIRS-001) fechada com evidência do scaffold
- [x] Epics FT-1 (#1, #2, #3, #4, #9, #11) com checklist de slices + `in_progress`
- [x] Roadmap com links diretos Epic→Issue

DAG atual: **v0.1.0 publicada** (tag + Release com artefatos).
FT-4 completo: #48–#52 (done) → **QA da DAG APROVADA** (13/13 checks E2E +
suite 150 passed + gates; 2 defeitos achados e corrigidos com regressão).
Fase C E04: #56–58 (done) → **E04 completo** (8/8 slices + QA FT-4 aprovada).
UX da sessão de validação: #53 (done), #54 (done, wizard), #55 (done) — trilogia UX completa.

## Release 0.1.0 (2026-09-10, publicada)

- Docs sincronizados (README/ROADMAP/ESTADO/CHANGELOG), acceptance marcado nas
  30 slices + 8 Epics, QA completo verde (137 passed), E2E Windows local +
  Linux via CI, golden regenerado (só versão), exemplo reproduzível em
  docs/examples/scan-example.json.

## Lições da validação operacional (2026-09-09, somente leitura)

- A varredura de uma árvore grande **não concluiu sob o limite operacional**:
  sem progresso ao vivo, política de arquivo grande e leitura compartilhada, o
  scan não escala — evidência para WIRS-034 (large-file) e WIRS-113/115
  (progresso), já no roadmap.
- Zonas de conteúdo e componentes customizados foram classificadas corretamente,
  sem aplicar policy/heurística fora do escopo.
- **Core via WP-CLI direto:** arquivo oficial ausente gerou warning de
  hardening, sem indicar comprometimento.
- **Policy em cache legítimo**: templates compilados em uma zona regenerável
  disparam em massa — caso textbook para allowlist de cache, não para
  silenciar a regra (e origem da política de scan de cache em etapa separada).
- **MU-plugins desconhecidos**: auto-executam; origem sempre a confirmar
  manualmente (caso para WIRS-067).
- **Componentes premium** → UNVERIFIED por desenho, mas sempre
  escaneados por heurísticas/IOC — nunca pulados (origem da regra E04
  "premium nunca é skip").
- Nada foi escrito no alvo em nenhum momento.

## Validação WordPress local (2026-09-09)

- Instalação oficial pristina: **0 findings**, com supressões de baseline
  visíveis, exit 0. Plugin sem configuração necessária: FAILED honesto (nada a
  verificar sem config).
- Fixture adulterada: divergência de integridade e arquivo inesperado geram
  Findings, exit 1. Heurísticas só nos divergentes.
- Correções que a sessão forçou: contratos reais do WP-CLI (#33/#34),
  supressão por arquivo (não tudo-ou-nada), `.cmd` no Windows (#46).

## QA do orquestrador + --ioc (2026-09-09, APROVADA com ressalvas)

- Suite: 131 passed, 4 skipped; ruff + format + mypy strict + guardas limpos.
- E2E real: scan em WP adulterado gera WP.UPLOAD.EXECUTABLE/high (exit 1,
  exit 0 com --fail-on critical); provider core validado contra WP-CLI 2.12.0
  real (contratos corrigidos — ver #33/#34).
- Ressalvas: (1) plugin JSON validado via fonte, sem execução com DB;
  (2) QA formal de Epic fica para o fechamento do 0.1.0.

## Merge Fase B (2026-09-09)

FT-1 (13 slices) + FT-2 (6) + FT-3 (6) em `main`: núcleo seguro, integridade
WordPress via WP-CLI, detecção (IOC/heurísticas/policy) e relatórios humanos.
Ainda fora do `scan` (sem orquestrador): providers e detectores rodam isolados;
profile `soft` formal e E2E com WP real ficam para o `0.1.0`.

## QA da DAG FT-3 (2026-09-09, APROVADA com ressalvas)

- Suite: 119 passed, 4 skipped (symlink/fifo/wp-cli ausentes neste Windows; rodam no CI Linux).
- Ruff check + format + mypy strict + guardas: limpos.
- Cadeia E2E sobre fixture heuristics/chain.php: IOC achado (1x),
  heurística PHP.HEUR.CHAIN/high, hints text+executable — três detectores
  concordando sobre o mesmo arquivo.
- Aceites das 6 slices conferidos um a um (evidências nos comentários).
- Ressalvas: (1) detectores ainda não plugados no `scan` (orquestrador é
  FT-4); (2) contratos JSON de plugins assumidos; (3) QA formal de Epic fica
  para a Fase B.

## QA da DAG FT-2 (2026-09-09, APROVADA com ressalvas)

- Suite: 96 passed, 4 skipped (symlink/fifo/wp-cli ausentes neste Windows; rodam no CI Linux).
- Ruff check + format + mypy strict + guardas: limpos.
- Cadeia E2E sobre fixture uploads_php: discovery=None (correto — fixture não
  é install completo, anti-falso-positivo funciona) + policy gera
  WP.UPLOAD.EXECUTABLE/high no evil.php e nada no jpg/plugin.
- Aceites das 6 slices conferidos um a um (evidências nos comentários).
- Ressalvas: (1) contratos JSON de plugins assumidos — integração real pendente
  de ambiente com WP-CLI; (2) providers ainda não plugados no `scan`
  (orquestrador é FT-3); (3) QA formal de Epic fica para a Fase B.

## QA da DAG FT-1 (2026-09-09, APROVADA com ressalvas)

- Suite: 74 passed, 2 skipped (symlink+fifo exigem privilégio ausente neste Windows; rodam no CI Linux).
- Ruff check + format + mypy strict: limpos. Guardas de arquitetura verdes.
- E2E real: `wirs scan <fixture> --format json|terminal` → JSON válido, coverage filesystem COMPLETE, exit 3 honesto.
- Sem escrita: único `open(` em `src/` é `"rb"`; nenhum `write/mkdir/unlink/subprocess/shell`.
- Aceites das 13 slices conferidos um a um contra as Issues (evidências nos comentários de fechamento).
- Ressalvas: (1) testes symlink/fifo não executados neste host — CI Linux cobre; (2) QA formal de Epic (`/qa-analyst` completo com plano) fica para o fechamento da Fase B.

## Auditoria de realinhamento (2026-09-15)

- North Star consolidada: scanner read-only de segurança, integridade e código
  suspeito para aplicações web, WordPress-first, com shortlist auditável.
- Charter, matriz documental, relatório de auditoria e instruções progressivas
  de arquitetura/fluxo foram adicionados.
- Material de visão foi movido para `docs/future/`; material ANFAMOTO foi movido
  para `docs/case-studies/`.
- Issues/Epics foram sincronizadas: YARA (#66) P0 após #65; PHP Generic (#70)
  sem dependência de Bundle; Diagnosis (#77) file-centric; HTML (#80)
  filesystem-only; logs/hospedagem (#63–#75) P2/Horizonte C.
- Nenhuma Epic pai foi fechada e nenhuma nova feature foi implementada nesta
  auditoria.

## Estado atual — Fechamento do realinhamento

- `PRODUCT REALIGNMENT: CLOSED`.
- #82 (WIRS-123) está fechado após teste de symlink existente e quebrado; os
  casos executam no CI Linux e são skipped neste Windows sem privilégio.
- HITL #65-01 foi aprovado e a #65 foi concluída em schema 2.0; #66 não foi
  iniciada.
- Próxima DAG: #66 → #67 → #77 → #80 → #70; E12/E16/E17 permanecem
  enriquecimentos posteriores conforme o roadmap.

## Revisão de incidente real (2026-09-14)

- Decisão: WIRS permanece scanner forense local/offline até 1.0. Analisa
  somente pastas, logs, snapshots e archives já acessíveis na máquina.
- Entrada escolhida: Incident Bundle local com manifesto versionado.
- Removidos do caminho pré-1.0: SSH/SFTP, APIs online, agents residentes,
  streaming/SIEM, active HTTP e resposta automática.
- Novos Epics: E16/#63 (Evidence temporal/logs) e E17/#64 (hospedagem local).
- Slices #65–81 publicadas sem dados do cliente; ADR-011 registra a decisão.
- Governança documental: `docs/agents/README.md` aponta para os guias separados
  de arquitetura e workflow, mantendo tracker/triage/domínio no índice.

## Auditoria de hardening (2026-09-15)

- Encontrado bypass P0 da garantia "scan nunca escreve no target": um destino
  `--report` symlink dentro do target podia resolver para fora antes da rejeição.
- Correção local aplicada em `src/wirs/cli/app.py`: destinos que são symlink são
  recusados antes de `resolve()`/writer atômico.
- Regressão adicionada em `tests/integration/test_scan_report.py` para symlink
  existente e quebrado; os casos são `skipped` neste Windows por falta de
  privilégio e devem executar no CI Linux.
- Rastreabilidade: #82 (WIRS-123), fechado após verificação dos critérios.
- Divergência corrigida no roadmap: #65/WIRS-026 está fechada após QA do schema
  2.0; o contrato aprovado está registrado no GitHub e no ADR-004.
