# WIRS — Matriz Documental

Última revisão: 2026-09-15 · branch `develop` · commit `c08b284`

Esta matriz define qual documento responde a cada pergunta. Ela não substitui
os documentos originais nem transforma uma visão futura em escopo.

| Artefato | Tipo | Fonte de verdade para | Autoridade | Horizonte | Estado | Pode definir prioridade? | Pode criar escopo de implementação? | Upstream obrigatório | Downstream que deve acompanhar | Gatilho de atualização | Drift encontrado | Ação tomada | Última revisão |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `docs/PRODUCT-CHARTER.md` | Charter | Identidade, limites e ordem de expansão | Máxima para produto | A-E | Atualizado | Sim | Indiretamente | Decisão do mantenedor | Spec, Roadmap, Epics, README | Mudança de tese ou limites | Não existia | Criado como North Star curta | 2026-09-15 |
| `docs/PROMPT-REALINHAMENTO-WIRS.md` | Prompt normativo | Procedimento e critérios desta auditoria | Normativa da execução | Atual | Preservado | Não | Não | Pedido do mantenedor | Charter, matriz, audit report | Nova auditoria ou mudança de critério | Não existia no inventário anterior | Mantido como prompt único e fonte do procedimento | 2026-09-15 |
| `AGENTS.md` | Governança | Regras que todo agente deve seguir | Normativa operacional | Todos | Atualizado | Não sozinho | Não sozinho | Charter + matriz | Agentes e docs/agents | Mudança de processo ou invariante | Autoridade linear e sem gate anti-deriva | Reescrito com autoridade por assunto e gate | 2026-09-15 |
| `CONTEXT.md` | Glossário | Vocabulário do domínio | Normativa lexical | Todos | Preservado | Não | Não | Charter + Spec | Código e docs | Termo novo, removido ou ambíguo | Nenhum material | Nenhuma alteração necessária | 2026-09-15 |
| `WIRS_MASTER_SPEC_PT-BR.md` | Spec | Requisitos e contratos gerais | Normativa técnica/produto | A-E | Corrigido | Sim, subordinada ao Charter | Sim | Charter | Architecture, Roadmap, Issues | Requisito ou contrato muda | Estrutura citava docs inexistentes | Referências de estrutura alinhadas aos docs reais | 2026-09-15 |
| `docs/ARCHITECTURE.md` | Arquitetura | Seams, fluxo e responsabilidades | Normativa técnica | Todos | Atualizado | Não | Não | Charter + Spec + ADRs | Código, testes e providers | Seam ou fluxo muda | Capacidades futuras podiam parecer entregues | Separada arquitetura-alvo de estado atual | 2026-09-15 |
| `docs/README.md` | Índice | Navegação da documentação | Informativa | Todos | Atualizado | Não | Não | Matriz | Leitores e agentes | Documento criado/movido | Não listava Charter/Matriz/futuro/case/audits | Índice e autoridade por assunto atualizados | 2026-09-15 |
| `docs/ENTENDENDO-O-WIRS.md` | Didático | Como detecções entregues funcionam | Informativa baseada em código | Atual | Corrigido | Não | Não | Código + Issues fechadas | Analistas | Detecção entregue ou removida | Referência a sessão/arquivo inexistente | Referência tornada reproduzível e afirmações futuras preservadas | 2026-09-15 |
| `docs/adr/*` | ADR | Motivo de decisões arquiteturais | Normativa por decisão | Variável | Preservado | Não sozinho | Não sozinho | Charter + Spec | Architecture e código | Trade-off difícil de reverter | ADR-011 já existia; nenhum ADR faltante confirmado | Mantidos; sem ADR novo nesta auditoria | 2026-09-15 |
| `docs/providers/*` | Contrato externo | API, limites e comportamento de providers | Normativa local do provider | Variável | Revisado | Não | Não | Docs oficiais + ADR | Providers, tests, CI | Lib/API muda | YARA ainda não integrado; WP-CLI histórico | Não implementar nesta auditoria; registrar gaps | 2026-09-15 |
| `ORCHESTRATOR-ROADMAP.md` | Roadmap | Ordem de Epics e marcos | Normativa de sequência | A-E | Corrigido | Sim | Não detalhadamente | Charter + Spec | Epics e Estado | Prioridade/dependência muda | Logs/host P1, E09 sem file-centric, #70/#80 blockers | Ordem reconstruída por horizonte e valor | 2026-09-15 |
| `ESTADO_ORQUESTRATOR.md` | Snapshot | Estado operacional momentâneo | Informativa | Atual | Regenerado após fechamento do realinhamento | Não | Não | GitHub + checkout | Nenhum | Fim/início de DAG | Data/branch/commit, #82 e próximos passos obsoletos | Estado atualizado para `PRODUCT REALIGNMENT: CLOSED` e entrada HITL #65 | 2026-09-15 |
| `README.md` | Entrada pública | Capacidade real e uso rápido | Informativa | Atual | Corrigido | Não | Não | Código testado + Roadmap | Usuários e contribuintes | Release/comando muda | Não separava claramente próximos horizontes | Charter e estado real vinculados | 2026-09-15 |
| `CHANGELOG.md` | Histórico | O que foi lançado | Informativa histórica | Releases | Preservado | Não | Não | Release verificada | README e tags | Release publicada | Nenhum drift a corrigir | Não registrar trabalho não lançado | 2026-09-15 |
| `docs/future/WIRS-MELHORIAS.md` | Future Vision | Possibilidades não comprometidas | Não normativa | C-E | Movido e classificado | Não | Não | Charter | Roadmap só após promoção | Nova hipótese ou promoção | Estava em `docs/` | Movido para `docs/future/` | 2026-09-15 |
| `docs/case-studies/ANFAMOTO-GAPS.md` | Case Study | Lições generalizáveis de incidente | Não normativa | A-E | Movido e classificado | Não | Não | Charter | Future/Issues após generalização | Novo caso ou gap validado | Estava em `docs/` e podia parecer spec | Movido e marcado como laboratório de gaps | 2026-09-15 |
| `docs/WIRS-MATRIZ-DOCUMENTAL-TEMPLATE.md` | Template | Estrutura para futuras matrizes | Não normativa | Todos | Preservado | Não | Não | Prompt de auditoria | `DOCUMENTATION-MATRIX.md` | Nova coluna ou processo | Template era confundível com matriz preenchida | Mantido como template, matriz operacional criada | 2026-09-15 |
| `SKILL_MAP.md` | Governança de agentes | Seleção de skill por contrato | Normativa de processo | Todos | Preservado | Não | Não | Ambiente real | AGENTS e agentes | Skills instaladas mudam | Divergência 85/86 já documentada | Mantida; framework clone não localizado | 2026-09-15 |
| GitHub Epics | Tracker | Objetivo, aceite e estado por Epic | Normativa de execução | A-E | Realinhado | Sim dentro do Roadmap | Sim | Charter + Roadmap | Slices | Fatiamento ou estado muda | Prioridades e checklists divergentes | Bodies/labels/dependências sincronizados | 2026-09-15 |
| GitHub slice Issues | Tracker | Comportamento verificável | Normativa de entrega | A-E | Realinhado | Não acima da Epic | Sim | Epic + docs do módulo | Código/testes/docs | Implementação ou dependência muda | Test paths mortos, semântica mista em #77 e #82 sem estado atualizado | Bodies, labels, blockers, Verification, #77 e fechamento de #82 corrigidos | 2026-09-15 |
| Código + testes reproduzíveis | Prova de implementação | O que realmente funciona | Autoridade factual | Atual | Referência | Não | Não | Spec/Issues | README, State, audit | Código/teste muda | #66/YARA, content analysis e Diagnosis ainda incompletos | #65 concluída: schema 2.0, refs, MISSING, provider runs e redaction cobertos por testes | 2026-09-15 |

## Regras de uso

1. `docs/future/` pode propor, mas não prioriza nem bloqueia P0/P1.
2. `docs/case-studies/` registra lições; não redefine o produto sozinho.
3. `ESTADO_ORQUESTRATOR.md` é snapshot, nunca fonte de produto.
4. Uma referência a arquivo, teste ou ADR inexistente é drift documental.
5. Toda mudança relevante identifica o downstream que precisa acompanhar.
