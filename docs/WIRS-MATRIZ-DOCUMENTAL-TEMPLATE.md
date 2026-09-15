# WIRS — Matriz Documental

> Este arquivo é um template inicial para ser preenchido pelo agente durante a auditoria de realinhamento.
> A matriz não substitui os documentos; ela define responsabilidade, autoridade, dependências e gatilhos de atualização.

## Matriz

| Artefato | Tipo | Fonte de verdade para | Autoridade | Horizonte | Estado | Pode definir prioridade? | Pode criar escopo de implementação? | Upstream obrigatório | Downstream que deve acompanhar | Gatilho de atualização | Drift encontrado | Ação tomada | Última revisão |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `docs/PRODUCT-CHARTER.md` | Charter | identidade, limites e ordem de expansão | máxima para produto | todos | criar | sim | indiretamente | decisão do mantenedor | Spec, Roadmap, Epics, README | mudança de tese/limite | preencher | preencher | preencher |
| `WIRS_MASTER_SPEC_PT-BR.md` | Spec | requisitos e contratos gerais | normativa | A-E | revisar | sim, subordinada ao Charter | sim | Product Charter | Architecture, Roadmap, Issues | mudança de requisito | preencher | preencher | preencher |
| `CONTEXT.md` | Glossário | vocabulário do domínio | normativa lexical | todos | revisar | não | não | Charter + Spec | código/docs | termo novo/removido | preencher | preencher | preencher |
| `docs/ARCHITECTURE.md` | Arquitetura | boundaries e fluxo das peças | normativa técnica | todos | revisar | não diretamente | não | Charter + Spec + ADR | módulos/docs | boundary/flow muda | preencher | preencher | preencher |
| `docs/adr/*` | ADR | decisões arquiteturais específicas | normativa por decisão | variável | revisar | não sozinho | não sozinho | Charter + Spec | Architecture/code | decisão irreversível | preencher | preencher | preencher |
| `ORCHESTRATOR-ROADMAP.md` | Roadmap | ordem de Epics/marcos | normativa de sequência | A-E | corrigir | sim | não detalhadamente | Charter + Spec | Epics/ESTADO | prioridade/dependência muda | preencher | preencher | preencher |
| GitHub Epics | Tracker | objetivo/aceite por Epic | normativa de execução | A-E | corrigir | sim dentro do Roadmap | sim | Charter + Roadmap | slices | fatiamento/estado muda | preencher | preencher | preencher |
| GitHub slices | Tracker | comportamento verificável | normativa de entrega | A-E | corrigir | não acima da Epic | sim | Epic + docs módulo | código/testes/docs | implementação | preencher | preencher | preencher |
| `ESTADO_ORQUESTRATOR.md` | Snapshot | estado operacional atual | informativa | atual | atualizar | não | não | GitHub + checkout | nenhum | fim/início de DAG | preencher | preencher | preencher |
| `README.md` | Entrada | capacidade pública real | informativa | atual | revisar | não | não | código testado + Roadmap | usuários | release/comando muda | preencher | preencher | preencher |
| `docs/ENTENDENDO-O-WIRS.md` | Didático | como e por que o WIRS encontra e prioriza sinais de comprometimento; como interpretar Evidence, Finding, Coverage, Diagnosis, report e limites | informativa baseada em comportamento entregue | atual | preservar/revisar | não | não | código + testes reais + Issues fechadas | usuários/analistas | entrega ou mudança relevante de comportamento que acrescente conhecimento investigativo | preencher | preencher | preencher |
| `docs/providers/*` | Contrato externo | API/comportamento de provider | normativa local do provider | variável | revisar | não | não | docs oficiais + ADR | provider/code | lib/API muda | preencher | preencher | preencher |
| `SKILL_MAP.md` | Governança de agentes | skill correta por tarefa | normativa de processo | todos | revisar | não | não | ambiente real | AGENTS | skills mudam | preencher | preencher | preencher |
| `docs/future/*` | Future Vision | possibilidades não comprometidas | não normativa | C-E | criar/mover | não | não | Charter | Roadmap apenas quando promovido | nova hipótese | preencher | preencher | preencher |
| `docs/case-studies/*` | Case Study | lições de incidentes | não normativa | variável | criar/mover | não | não | Charter | Future/Issues após generalização | incidente analisado | preencher | preencher | preencher |

## Regras

1. Future Vision nunca bloqueia P0/P1.
2. Case Study não redefine produto.
3. Roadmap não pode conter Epic ausente no tracker.
4. Epic nova declara horizonte do Product Charter.
5. Issue não pode depender de capacidade posterior sem justificativa técnica.
6. README descreve somente capacidade real ou marca explicitamente o que é futuro.
7. ESTADO é regenerável/snapshot e não acumula planejamento histórico como fonte normativa.
8. Referência a ADR/teste/doc inexistente é erro documental.
9. Toda mudança relevante registra downstream que precisa ser sincronizado.
10. O agente deve preencher `Drift encontrado`, `Ação tomada` e `Última revisão` nesta auditoria.
