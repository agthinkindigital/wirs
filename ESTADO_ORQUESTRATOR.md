# Estado do Orquestrador — WIRS

**Data:** 2026-09-08
**Branch:** `main` (repo `agthinkindigital/wirs`, público, criado via `gh`)
**Framework:** skills locais (orchestrator, setup-skills, tdd, qa-analyst, ui-ux-pro-max, ...)

---

## Fase 0 — Pré-condições (ATENDIDAS)

- [x] Git inicializado (branch `main`)
- [x] Remote GitHub configurado (`origin` → `agthinkindigital/wirs`, público)
- [x] Acesso GitHub confirmado (`gh repo view` OK, conta `agthinkindigital`)
- [x] Toolchain: Python 3.14.7 (dev local), `uv` 0.12.5 via scoop, Node 24, PHP 8.3
- [x] Decisões de definição via grill: Python `>=3.11`, Typer+Rich, scaffold do zero, MIT, HTML skeleton desde o início

## Fase 1 — Provisionamento documental (EM ANDAMENTO)

- [x] `AGENTS.md` (protocolo WIRS + 14 invariantes)
- [x] `CONTEXT.md` (glossário: core, confiança, baselines, zones WP)
- [x] `docs/agents/README.md` (domínio, tracker, triage)
- [x] `docs/adr/` (ADR-001..010 conforme Seção 14.13 do spec)
- [x] `ORCHESTRATOR-ROADMAP.md` (E00–E15)
- [ ] Issues GitHub via `/to-issues` (após scaffold)
- [ ] Links Epic→Issue no roadmap (após `/to-issues`)

## Fase 2 — To-issues FT-1 (CONCLUÍDA)

- [x] Labels criadas (triage, tipos, áreas, prioridades)
- [x] 16 Epic issues: #1–#16 (E00–E15)
- [x] 13 slice issues FT-1: #17–#29, modo AFK, `ready-for-agent`, `Blocked by` reais
- [x] #17 (WIRS-001) fechada com evidência do scaffold
- [x] Epics FT-1 (#1, #2, #3, #4, #9, #11) com checklist de slices + `in_progress`
- [x] Roadmap com links diretos Epic→Issue

DAG atual: **v0.1.0 publicada** (tag + Release com artefatos). FT-4: #48 (done),
#49 (done), #50 (done), #51 (done) → {#52}. UX sessão real: #53–55 (E10, HITL).

## Release 0.1.0 (2026-09-10, em andamento)

- Docs sincronizados (README/ROADMAP/ESTADO/CHANGELOG), acceptance marcado nas
  30 slices + 8 Epics, QA completo verde (137 passed), E2E Windows local +
  Linux via CI, golden regenerado (só versão), exemplo reproduzível em
  docs/examples/scan-example.json.

## Sessão site real (2026-09-09, somente leitura, dados anonimizados)

- Full-tree (~5 GB / ~70 mil arquivos) **não concluiu em 30 min**: sem progresso
  ao vivo, sem política de arquivo grande e com dupla leitura por arquivo, o
  scan não escala — evidência para WIRS-034 (large-file) e WIRS-113/115
  (progresso), já no roadmap.
- Escopos funcionaram: uploads (~700 MB) → 0 findings, exit 0; arquivos custom
  em `wp-content/` → zonas corretas, sem policy/heurística.
- **Core via WP-CLI direto: 1 warning** — `readme.html` ausente (hardening
  comum, benigno). Resto íntegro.
- **Policy em cache legítimo**: templates compilados em `uploads/cache`
  disparam em massa — caso textbook para allowlist de cache, não para
  silenciar a regra (e origem da política de scan de cache em etapa separada).
- **MU-plugins desconhecidos**: auto-executam; origem sempre a confirmar
  manualmente (caso para WIRS-067).
- **Plugins majoritariamente premium** → UNVERIFIED por desenho, mas sempre
  escaneados por heurísticas/IOC — nunca pulados (origem da regra E04
  "premium nunca é skip").
- Nada foi escrito no alvo em nenhum momento.

## Sessão WP real (2026-09-09)

- WP oficial pristino + WP-CLI 2.12.0: **0 findings**, 3338 suprimidos,
  exit 0. Plugin sem wp-config: FAILED honesto (nada a verificar sem config).
- Adulterado (version.php + evil.php): **2 findings** (MISMATCH critical +
  UNEXPECTED medium), exit 1. Heurísticas só nos divergentes.
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

## Próximos passos

1. TDD #18 (WIRS-002 boundaries + architecture test) na `develop`.
2. Seguir a DAG em slices verticais (RED→GREEN→refactor), uma issue por vez.
3. QA (`/qa-analyst`) ao fechar cada Epic.
