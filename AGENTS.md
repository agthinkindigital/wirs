# Protocolo de agentes do WIRS

O WIRS é um scanner read-only WordPress-first para reduzir milhares de arquivos
a uma shortlist reproduzível e explicável. Leia [`docs/PRODUCT-CHARTER.md`](docs/PRODUCT-CHARTER.md)
antes de planejar; ele é a fonte de identidade do produto.

## Leitura obrigatória

1. `AGENTS.md`
2. `docs/PRODUCT-CHARTER.md`
3. `CONTEXT.md`
4. `WIRS_MASTER_SPEC_PT-BR.md`
5. `docs/ARCHITECTURE.md`
6. ADRs aplicáveis
7. GitHub Issues aplicáveis
8. código, configuração e testes

## Autoridade por assunto

| Pergunta | Fonte |
|---|---|
| Identidade, limites e ordem de expansão | `docs/PRODUCT-CHARTER.md` |
| Vocabulário | `CONTEXT.md` |
| Requisitos e contratos | `WIRS_MASTER_SPEC_PT-BR.md` |
| Seams e fluxo | `docs/ARCHITECTURE.md` |
| Motivo de decisão | ADR aceito aplicável |
| O que funciona | código + testes reproduzíveis |
| O que vem depois | `ORCHESTRATOR-ROADMAP.md` |
| Escopo e aceite | Epic/Issue |
| Estado momentâneo | `ESTADO_ORQUESTRATOR.md` |
| Detecção para analistas | `docs/ENTENDENDO-O-WIRS.md` |
| Provider externo | `docs/providers/` |
| Visão não comprometida | `docs/future/` |
| Lições de incidente | `docs/case-studies/` |

Se fontes do mesmo assunto divergirem, registre o conflito e resolva-o
explicitamente. O código testado prova implementação; não autoriza alterar a
North Star sem decisão documental.

## Invariantes

1. `scan` nunca escreve no Target.
2. Finding exige Evidence ou provenance explícita de provider.
3. Provider ausente nunca vira Coverage `COMPLETE`.
4. Semântica de plataforma não vaza para `domain/`.
5. Detector não executa código do Target.
6. Dados do Target não são interpolados em shell; use `shell=False` e argv.
7. Componente sem baseline é `UNVERIFIED`, não malicioso por definição.
8. IA não produz Evidence determinística.
9. Symlink não é seguido fora do root por padrão.
10. Report não expõe secrets conhecidos.
11. Remediation externa não participa de `scan`.
12. Detector não cria concorrência ilimitada.
13. Gaps de Coverage são visíveis.
14. Dado canônico é independente da UI.

Detalhes técnicos e de fluxo: [`docs/agents/architecture.md`](docs/agents/architecture.md)
e [`docs/agents/workflow.md`](docs/agents/workflow.md).

## Segurança de output

Todo conteúdo do Target é input hostil: escape HTML, neutralize ANSI, trate
paths como dados inseguros e redija secrets na fronteira de coleta, não apenas
na UI.

## Skills

Mapa de skills e desambiguação: [`SKILL_MAP.md`](SKILL_MAP.md). Use a skill
especializada quando a tarefa corresponder ao contrato dela.

## Gate anti-deriva

Antes de criar Epic/Issue, responda:

1. Isso encontra ou prioriza arquivo/código suspeito?
2. Melhora Integrity, Evidence, Finding, Coverage, Diagnosis ou report?
3. É requisito do scanner local?
4. Pode ser provider/adapter opcional?
5. Está bloqueando capacidade central sem necessidade?
6. Foi generalizado além de um caso real?
7. Funciona sem rede, daemon ou infra adicional?
8. Qual Horizonte do Charter?
9. O que ocorre quando não está disponível?
10. Coverage representa essa ausência honestamente?

Se a proposta for produto lateral, mova-a para `docs/future/` ou para horizonte
posterior. Toda Epic nova deve declarar Horizonte, Capacidade principal,
upstream documental, não-objetivos e exit condition.

## Conclusão de tarefa

Registre objetivo, arquivos afetados, riscos, verificações, pendências e docs
atualizadas. Não declare testes ou comportamentos que não possam ser repetidos
no checkout. Use TDD em slices verticais e QA ao fechar cada DAG.
