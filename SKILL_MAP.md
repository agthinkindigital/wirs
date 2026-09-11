# SKILL_MAP — Skills disponíveis e uso no WIRS

Inventário verificado em 2026-09-11 contra `C:\Users\Leonardo\.opencode\skills`
+ skills built-in do ambiente. Critério de status: `ATIVA` = já invocada neste
projeto; `PREVISTA` = contrato casa com fase futura; `INAPLICÁVEL` = fora do
escopo (motivo declarado). Regra do `AGENTS.md` continua valendo: skill só é
carregada quando a tarefa corresponde ao seu contrato.

## Contagem verificável

| Origem | Quantidade |
|---|---:|
| alltomatos/skills (engineering 21 + productivity 5 + misc 4 + personal 2) | 32 |
| softaworks/agent-toolkit (todas em `misc/`) | 43 |
| tt-a1i/archify (`misc/archify`, locale pt-BR) | 1 |
| Topo (`banner-design`, `brand`, `design`, `design-system`, `slides`, `ui-styling`, `ui-ux-pro-max`) | 7 |
| Built-in sem pasta (`orchestrator`, `customize-opencode`) | 2 |
| **Total acessível** | **85** |

> Divergência registrada: o anúncio fala em 86 skills; o inventário mecânico
> (`rglob SKILL.md` + built-ins) soma **85**. Falta 1 para esclarecer — sem
> chute: nenhuma skill foi inventada para fechar a conta.

## Núcleo de engenharia (ciclo TDD → Issues → QA)

| Skill | Status | Uso no WIRS |
|---|---|---|
| `orchestrator` | ATIVA | Governança, DAG, QA de fechamento (FT-1…FT-4) |
| `setup-skills` | ATIVA | Artefatos de governança; GitHub como tracker obrigatório |
| `roadmap` | PREVISTA | Epics E## e links; consultar antes de qualquer planejamento |
| `to-issues` | ATIVA | Fatiamento FT-4 (#48–52), UX #53–55; padrão de corpo de Issue |
| `tdd` | ATIVA | Slices verticais RED→GREEN; proibido horizontal slice |
| `diagnose` | PREVISTA | Bugs duros/regressões (reproduzir→minimizar→instrumentar→fix) |
| `secure-e2e` | PREVISTA | E2E + negative testing (fuzz/archive/injection, §9.1 do spec) |
| `qa-analyst` | PREVISTA | Portão obrigatório de DAG (FT-4 pendente) e de Epic |
| `qa-test-planner` | PREVISTA | Planos de teste, casos manuais e regressão (complementa `qa-analyst`) |
| `developer` | PREVISTA | Coordenação por agentes (alternativa/consulta ao `orchestrator`) |
| `query-docs` | PREVISTA | Contratos WP-CLI/YARA/Wordfence via Context7 antes de integrar |
| `triage` | PREVISTA | Vocabulário `needs-triage/ready-for-agent/...` nas Issues |
| `to-prd` | PREVISTA | PRDs futuros (ex.: wizard #54) a partir do contexto |
| `skill-judge` | ATIVA | Critério knowledge-delta para avaliar skills e docs |

## Linguagem e decisão antes de implementar

| Skill | Status | Uso no WIRS |
|---|---|---|
| `grill-with-docs` | PREVISTA | Plano vs modelo de domínio (`CONTEXT.md`, ADRs) |
| `grill-feature-with-docs` | PREVISTA | Evoluir módulo existente com docs sincronizadas |
| `grill-me` | PREVISTA | Stress-test de plano até entendimento compartilhado |
| `gepetto` | PREVISTA | Planos de implementação com revisão multi-LLM (features grandes) |
| `requirements-clarity` | PREVISTA | Perguntas Why?/Simpler? antes de implementar (Definition of Ready) |
| `zoom-out` | PREVISTA | Contexto amplo ao navegar em módulo desconhecido |
| `game-changing-features` | PREVISTA | Pensamento 10x pós-1.0 (sem contaminar o MVP) |

## Arquitetura e qualidade de código

| Skill | Status | Uso no WIRS |
|---|---|---|
| `improve-codebase-architecture` | PREVISTA | Refactors orientados ao domínio (boundaries, testabilidade) |
| `reducing-entropy` | PREVISTA | Minimizar tamanho do codebase (só sob pedido explícito) |
| `naming-analyzer` | PREVISTA | Nomes de variáveis/funções/classes no vocabulário do domínio |
| `lesson-learned` | PREVISTA | Extrair lições do git history após cada DAG |
| `ship-learn-next` | PREVISTA | Transformar aprendizado em planos de ação |
| `agent-md-refactor` | PREVISTA | Manter `AGENTS.md`/docs progressivos sem inchar |
| `caveman` | PREVISTA | Modo comprimido quando economia de tokens importa |

## Diagramas e arquitetura visual

| Skill | Status | Uso no WIRS |
|---|---|---|
| `archify` | PREVISTA | Diagramas de arquitetura/workflow/sequência em HTML standalone (pt-BR) |
| `c4-architecture` | PREVISTA | C4 via Mermaid para `docs/ARCHITECTURE.md` |
| `mermaid-diagrams` | PREVISTA | Diagramas de domínio/fluxo em Mermaid |
| `excalidraw` | PREVISTA | Visualizações delegadas a subagentes (sem estourar contexto) |
| `draw-io` | PREVISTA | Diagramas `.drawio` quando exigidos por consumidor externo |

## Relatórios, README e comunicação

| Skill | Status | Uso no WIRS |
|---|---|---|
| `edit-article` | ATIVA | Revisão do README e `ENTENDENDO-O-WIRS.md` |
| `crafting-effective-readmes` | PREVISTA | Evolução do README por audiência |
| `writing-clearly-and-concisely` | PREVISTA | Docs, mensagens de commit, textos de UI/erro |
| `humanizer` | PREVISTA | Tom humano em textos voltados ao analista |
| `professional-communication` | PREVISTA | E-mails/mensagens técnicas do projeto |
| `web-to-markdown` | PREVISTA | Converter páginas (docs de providers) em Markdown — só sob pedido |
| `marp-slide` / `slides` | PREVISTA | Apresentações do projeto |
| `ui-ux-pro-max` + `design-system` | PREVISTA | CLI/terminal/reports (ref. OWASP ZAP); HTML futuro |
| `design` / `brand` / `banner-design` / `ui-styling` | PREVISTA | Identidade e assets quando houver UI pública/HTML |

## Banco, schemas e dados (Fase D em diante)

| Skill | Status | Uso no WIRS |
|---|---|---|
| `database-schema-designer` | PREVISTA | SQLite futuro (history/cache/compare, §19.11 do spec) |

## Tooling, commits e ambiente

| Skill | Status | Uso no WIRS |
|---|---|---|
| `commit-work` | PREVISTA | Commits semânticos revisados e fatiados |
| `setup-pre-commit` | PREVISTA | Hooks de pre-commit (lint/format/type/test) |
| `dependency-updater` | PREVISTA | Updates seguros de deps (`typer`, `rich`, providers) |
| `devsetup` | PREVISTA | Onboarding Windows (winget, uv, Python, Git) |
| `scaffold-mvp` | PREVISTA | Bootstrap de projetos novos (não do WIRS atual) |
| `prototype` | PREVISTA | Protótipo descartável para validar decisão de desenho |
| `scaffold-exercises` | INAPLICÁVEL | Curso/exercícios — fora do escopo do produto |
| `migrate-to-shoehorn` | INAPLICÁVEL | TypeScript — este repo é Python |

## Skills, comandos e plugins do ambiente

| Skill | Status | Uso no WIRS |
|---|---|---|
| `customize-opencode` | PREVISTA | Config do próprio opencode (só para `.opencode/`, nunca app) |
| `command-creator` | PREVISTA | Slash commands reutilizáveis de workflows (ex.: `/qa-ft`) |
| `plugin-forge` | PREVISTA | Plugins/marketplace se o projeto adotar distribuição por plugins |
| `mcp-builder` | PREVISTA | MCP servers (ex.: expor scan via MCP no futuro) |
| `skill-creator` / `write-a-skill` | PREVISTA | Criar/otimizar skills de domínio do WIRS |

## Handoff e memória entre sessões

| Skill | Status | Uso no WIRS |
|---|---|---|
| `handoff` | PREVISTA | Compactar conversa para outro agente continuar |
| `session-handoff` | PREVISTA | Handoff com salvamento de estado em milestones |

## Observabilidade e deploy (pós-1.0)

| Skill | Status | Uso no WIRS |
|---|---|---|
| `superkuma-monitoring` | PREVISTA | Monitoramento de infra de scans agendados (fleet) |
| `datadog-cli` | INAPLICÁVEL | Sem Datadog no projeto |

## Explicitamente fora do escopo

| Skill | Motivo |
|---|---|
| `expo-expert` | Sem app mobile |
| `react-dev`, `react-useeffect`, `mui` | Sem frontend React |
| `backend-to-frontend-handoff-docs`, `frontend-to-backend-requirements`, `openapi-to-typescript` | Monolito CLI; sem API/frontend |
| `jira` | Tracker obrigatório é GitHub (`setup-skills`) |
| `codex`, `gemini`, `perplexity` | CLIs externos; execução e docs pelos canais do projeto (`query-docs`, `webfetch`) |
| `obsidian-vault` | Notas pessoais; conhecimento do projeto vive no repo |
| `git-guardrails-claude-code` | Hooks para Claude Code; ambiente aqui é opencode |
| `meme-factory`, `domain-name-brainstormer` | Sem uso no produto |
| `difficult-workplace-conversations`, `feedback-mastery`, `daily-meeting-update` | RH/reuniões; projeto solo |
| `design-system-starter` | Redundante com `design-system` já adotado |

## Índice auditável (85 nomes únicos)

1. `agent-md-refactor` · 2. `archify` · 3. `backend-to-frontend-handoff-docs` ·
4. `banner-design` · 5. `brand` · 6. `c4-architecture` · 7. `caveman` ·
8. `codex` · 9. `command-creator` · 10. `commit-work` · 11. `crafting-effective-readmes` ·
12. `customize-opencode` · 13. `daily-meeting-update` · 14. `database-schema-designer` ·
15. `datadog-cli` · 16. `dependency-updater` · 17. `design` · 18. `design-system` ·
19. `design-system-starter` · 20. `developer` · 21. `devsetup` · 22. `diagnose` ·
23. `difficult-workplace-conversations` · 24. `domain-name-brainstormer` · 25. `draw-io` ·
26. `edit-article` · 27. `excalidraw` · 28. `expo-expert` · 29. `feedback-mastery` ·
30. `frontend-to-backend-requirements` · 31. `game-changing-features` · 32. `gemini` ·
33. `gepetto` · 34. `git-guardrails-claude-code` · 35. `grill-feature-with-docs` ·
36. `grill-me` · 37. `grill-with-docs` · 38. `handoff` · 39. `humanizer` ·
40. `improve-codebase-architecture` · 41. `jira` · 42. `lesson-learned` · 43. `marp-slide` ·
44. `mcp-builder` · 45. `meme-factory` · 46. `mermaid-diagrams` · 47. `migrate-to-shoehorn` ·
48. `mui` · 49. `naming-analyzer` · 50. `obsidian-vault` · 51. `openapi-to-typescript` ·
52. `orchestrator` · 53. `perplexity` · 54. `plugin-forge` · 55. `professional-communication` ·
56. `prototype` · 57. `qa-analyst` · 58. `qa-test-planner` · 59. `query-docs` ·
60. `roadmap` · 61. `scaffold-exercises` · 62. `scaffold-mvp` · 63. `secure-e2e` ·
64. `session-handoff` · 65. `setup-pre-commit` · 66. `setup-skills` · 67. `ship-learn-next` ·
68. `skill-creator` · 69. `skill-judge` · 70. `slides` · 71. `superkuma-monitoring` ·
72. `tdd` · 73. `to-issues` · 74. `to-prd` · 75. `triage` · 76. `ui-styling` ·
77. `ui-ux-pro-max` · 78. `web-to-markdown` · 79. `write-a-skill` ·
80. `writing-clearly-and-concisely` · 81. `zoom-out` · 82. `react-dev` ·
83. `react-useeffect` · 84. `reducing-entropy` · 85. `requirements-clarity`

> Validação mecânica: cada nome acima ocorre ≥1 vez nas tabelas; o inventário
> `skills_inventory.txt` (83 no disco + 2 built-in) confere 1:1 com esta lista.
