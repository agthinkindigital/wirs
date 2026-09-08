# Protocolo de agentes do WIRS

## Leitura obrigatória

Antes de analisar ou alterar o projeto, leia nesta ordem:

1. `AGENTS.md`
2. `CONTEXT.md`
3. `WIRS_MASTER_SPEC_PT-BR.md` (especificação viva — autoridade de produto e arquitetura)
4. `docs/adr/` aplicáveis
5. GitHub Issues aplicáveis
6. somente então, código, configuração e testes

Se um arquivo estiver ausente ou contradisser o código, registre a divergência.
Ordem de autoridade: código testado < docs do módulo < ADRs < `WIRS_MASTER_SPEC_PT-BR.md`.

## Regras obrigatórias (invariantes arquiteturais)

1. `scan` nunca escreve no target.
2. Finding não existe sem Evidence ou provenance explícita de provider.
3. Provider ausente nunca vira Coverage completo.
4. Conceito de plataforma (`wp-content`, `artisan`, etc.) não vaza para o domain genérico.
5. Detector não executa código do alvo (`include`/`require`/import dinâmico proibidos).
6. Dado controlado pelo target nunca é interpolado em shell command (`shell=False`, argv).
7. Componente sem baseline é `UNVERIFIED`, nunca "malicioso" por definição.
8. Output de IA não é Evidence determinística.
9. Symlink não é seguido fora do root por padrão.
10. Report não expõe secrets conhecidos.
11. Remediation externa não participa de `scan`.
12. Detector não controla concorrência ilimitada (scheduler central decide).
13. Coverage gap é sempre visível.
14. Dado canônico é independente da UI.

## Domínio

- `domain/` usa apenas stdlib e value objects. Proibido importar `wordpress`,
  `yara`, `wordfence`, `rich`, `mysql`, `typer` a partir de `domain/`.
- `application/` depende de `domain/` + `ports/` apenas.
- `infrastructure/` e `providers/` implementam ports.
- `adapters/wordpress/` adiciona semântica de plataforma sem contaminar o core.
- `reporting/` consome o modelo em modo read-only.
- CLI é composition root.

## Segurança de output

Todo conteúdo do alvo é input hostil: escapar HTML, neutralizar ANSI,
tratar paths como dados inseguros, redigir secrets na fronteira de coleta
(não só na UI).

## GitHub e planejamento

- GitHub Issues são a fonte persistente de escopo, dependências e aceite.
- `ORCHESTRATOR-ROADMAP.md` resume Epics com IDs estáveis (`E##`) e links diretos.
- `ESTADO_ORQUESTRATOR.md` é apenas a visão operacional da DAG.
- Uma Epic só é `done` quando código, testes, documentação e evidência concordam.
- Ao final de uma DAG, execute a revisão de QA prevista pelo Orchestrator.

## Skills

Use a skill especializada quando a tarefa corresponder ao seu contrato:

- `orchestrator`: governança, roadmap, Issues, execução e QA.
- `setup-skills`: artefatos de governança.
- `roadmap`: Epics e links GitHub.
- `grill-with-docs` ou `grill-feature-with-docs`: linguagem e decisões antes de implementar.
- `grill-me`: interrogatório de plano/design até entendimento compartilhado.
- `to-issues`: decomposição em Issues rastreáveis.
- `tdd`: implementação test-first (vertical slices, nunca horizontal slices).
- `diagnose`: bugs duros e regressões.
- `secure-e2e`: validação E2E e de segurança (negative testing).
- `qa-analyst`: verificação final obrigatória da DAG.
- `query-docs`: contrato atual de bibliotecas externas e providers.
- `improve-codebase-architecture`: melhoria arquitetural orientada ao domínio.
- `ui-ux-pro-max` + `design-system`: CLI, terminal, reports (referência OWASP ZAP).
- `scaffold-mvp`: bootstrap de projeto novo.
- `prototype`: protótipo descartável para validar decisão.

## Critério de conclusão

Uma tarefa relevante deve registrar objetivo, arquivos afetados, riscos,
verificações executadas, pendências e atualizações de documentação. Não declare
testes, comandos ou comportamentos que não possam ser reproduzidos no checkout atual.
