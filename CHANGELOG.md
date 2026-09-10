# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

## [0.1.0] — 2026-09-10

Primeira baseline funcional: scanner WordPress operacional de ponta a ponta.

### Adicionado

- Núcleo seguro: Target, SafePath, Artifact, inventory com symlink sem follow,
  ArtifactReader read-only, HashService com memo por scan.
- Modelo: Evidence, Finding (severidade × confiança), Coverage (6 estados),
  IOC (5 tipos), integridade normalizada.
- Adapter WordPress: discovery por sinais, 9 zonas, doctor e providers de
  checksum do core e plugins via WP-CLI (contratos validados contra binário real).
- Detecção: IOC em streaming, hints compartilhados, heurísticas PHP v0,
  policy de executável em uploads, redaction de secrets na fronteira.
- Orquestrador v1 com baseline confiável absolvendo verificados, `--ioc`,
  `--fail-on` e exit codes documentados.
- Relatórios: JSON canônico versionado (golden), terminal Rich com sanitize.
- Governança e ensino: ADRs, roadmap com Epics rastreadas, `ENTENDENDO-O-WIRS.md`.

### Segurança

- `scan` nunca escreve no alvo; subprocess só via CommandRunner (`shell=False`);
  relatórios nunca expõem secrets; fixtures sintéticas e inertes (regra anti-AV).
