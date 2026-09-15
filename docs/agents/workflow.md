# Instruções de Fluxo

## Tracker

GitHub Issues são a fonte persistente de escopo, dependências, aceite e estado.
O Roadmap resume Epics; a Issue da Epic detalha. `ESTADO_ORQUESTRATOR.md` é
apenas snapshot. Não feche Epic pai sem autorização explícita.

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

Toda detecção nova ganha seção em `docs/ENTENDENDO-O-WIRS.md`. Mudança de seam
ou trade-off difícil pode exigir ADR. Mudança de produto exige Charter antes de
Roadmap e Issues.
