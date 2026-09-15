# Instruções de Fluxo

## Tracker

GitHub Issues são a fonte persistente de escopo, dependências, aceite e estado.
O Roadmap resume Epics; a Issue da Epic detalha. `ESTADO_ORQUESTRATOR.md` é
apenas snapshot. Não feche Epic pai sem autorização explícita.

## Branches e versões

- `develop` deve ser atualizado continuamente com mudanças aprovadas.
- `main` só recebe promoção formal após os gates da versão.
- Não confunda Issue/Epic/capability concluída com release; consulte
  [`docs/VERSIONAMENTO-E-GATES.md`](../VERSIONAMENTO-E-GATES.md).

## Issues Lock

Não trocar de tarefa ou abrir nova Issue/Epic enquanto a atual não estiver com:
- critérios de aceite verificados;
- testes e gates aprovados;
- documentação sincronizada;
- estado no tracker refletindo a realidade (fechada ou com pendência registrada).
Uma mudança de contexto sem conclusão documentada é considerada navegação sem rumo.
## Desenvolvimento

- Use TDD em slices verticais: RED, GREEN, refactor.
- Uma slice declara a capability concreta entregue ao usuário.
- Não implemente uma feature de horizonte posterior para preencher documentação.
- Registre riscos, arquivos afetados e verificações reproduzíveis.

## QA

Ao fechar uma DAG, confronte requisitos, código, testes, segurança, docs e
Issues. Testes ausentes, skips e referências quebradas são pendências, não
evidência de sucesso.

## Documentação

Atualize `docs/ENTENDENDO-O-WIRS.md` quando uma entrega ou mudança de
comportamento acrescentar conhecimento útil à segurança ou à investigação:
interpretação de sinal, Evidence, Finding, Coverage, Diagnosis, report,
limites ou próximos passos humanos. Uma Issue fechada não exige
automaticamente nova seção; Issues relacionadas podem alimentar a mesma seção
conceitual. Refactors, tooling, plumbing, CI, testes e detalhes internos sem
impacto interpretativo ficam fora do guia. Mudança de seam ou trade-off difícil
pode exigir ADR. Mudança de produto exige Charter antes de Roadmap e Issues.
