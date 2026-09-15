# ADR-012 — `develop` contínuo e promoção versionada para `main`

- **Status:** aceito
- **Data:** 2026-09-15

## Contexto

O WIRS trabalha em slices verticais e pode entregar capabilities em ordem
antecipada. Uma capability isolada, como PHP generic coverage, não representa
sozinha uma versão de produto. Sem uma regra explícita, `develop`, `main`,
roadmap, Changelog e tags podem afirmar estados diferentes.

## Decisão

`develop` será atualizado continuamente com o trabalho aprovado. `main` só será
atualizada por promoção formal quando os gates da fase/milestone e da release
estiverem aprovados. A versão publicada representa um conjunto coerente de
Epics, contratos, testes, QA e documentação, não a última Issue concluída.

O mapa de versões e os critérios verificáveis ficam em
[`docs/VERSIONAMENTO-E-GATES.md`](../VERSIONAMENTO-E-GATES.md). A primeira
versão publicada permanece `0.1.0`; trabalho posterior em `develop` não é
chamado de `0.2.0` até a promoção ser aprovada.

## Consequências

- Toda mudança de implementação deve manter `develop` sincronizada.
- `main` permanece uma referência reproduzível da última release.
- Tags, Release, Changelog, README e estado só são atualizados como parte de uma
  promoção aprovada.
- QA e gates de segurança passam a ser condição de versão, não apenas condição
  de uma Issue.
- Features antecipadas não mudam artificialmente o número da versão nem fecham
  marcos incompletos.
