# ADR-005 — WP-CLI como provider preferencial de checksum WordPress

- **Status:** aceito
- **Data:** 2026-09-08

## Contexto

`wp core verify-checksums` e `wp plugin verify-checksums` já resolvem
integridade oficial contra WordPress.org (JSON, `before_wp_load`).

## Decisão

Integrar primeiro via `WpCliCoreChecksumProvider` /
`WpCliPluginChecksumProvider` (CommandRunner seguro, normalização própria,
Coverage explícito). Fallback nativo com manifests oficiais vem depois
(offline, snapshot, remote).

## Consequências

- WIRS nunca exibe stdout cru: transforma em Evidence/Findings com
  provider, versão, comando lógico, tempo e erros.
- Ausência/timeout de WP-CLI degrada Coverage, nunca aborta o scan.
