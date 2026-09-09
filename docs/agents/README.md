# Operação com agentes

## Domínio

O glossário canônico é [`CONTEXT.md`](../../CONTEXT.md). Use os termos de lá
em nomes de módulos, classes e regras — se um termo do glossário não aparece
no código, sinalize como linguagem morta; se o código introduz um conceito
novo, o glossário precisa ser atualizado na mesma entrega.

## Tracker

A fonte persistente de escopo, dependências, aceite e status são as **GitHub
Issues** de `agthinkindigital/wirs`. Uma issue por slice vertical
(comportamento completo, pequeno, verificável), com objetivo, critérios de
aceite, `Blocked by` com IDs reais e evidência de verificação. O roadmap
resume as Epics; a issue da Epic detalha. `ESTADO_ORQUESTRATOR.md` é só a
visão operacional do momento — nunca a fonte. Não feche issue pai sem
autorização explícita.

## Triage

Labels padrão: `needs-triage`, `needs-info`, `ready-for-agent`,
`ready-for-human`, `wontfix`. Tipos: `type:feature`, `type:security`,
`type:test`, `type:docs`, `type:refactor`, `type:provider`, `type:adapter`.
Áreas: `area:core`, `area:wordpress`, `area:reporting`, `area:rules`,
`area:database`, `area:remote`. Prioridades: `priority:P0` (primeiro slice
útil), `P1` (MVP confiável), `P2` (pós-MVP), `P3` (expansão).
