# WP-CLI — provider de checksums WordPress

- **Versão testada:** nenhuma execução real ainda (WP-CLI ausente neste host).
  Contrato extraído da doc oficial em 2026-09-09; integração real pendente de
  ambiente com `wp` + fixture (`tests/integration/test_wpcli_core.py` pula sem eles).
- **Doc oficial:** https://developer.wordpress.org/cli/commands/core/verify-checksums/
  (repositório do comando: https://github.com/wp-cli/checksum-command)
- **Comandos usados:** `wp --version` (doctor) e
  `wp core verify-checksums --include-root --format=json --path=<target>`
  (`--version`/`--locale` quando WIRS-062 entregar a versão do alvo).
- **Output:** `--format=json` emite lista `[{"file": str, "message": str}]`;
  stdout vazio + exit 0 = tudo verificado. Mensagens conhecidas:
  `File doesn't verify against checksum` → MISMATCH,
  `File doesn't exist` → MISSING,
  `File should not exist`/`was added`/`non-WordPress` → UNEXPECTED.
  Qualquer outra forma = `ProviderInvalidOutput` (estrito de propósito).
- **Exit codes:** diferente de zero quando algo diverge — é *sinal*, não erro:
  com JSON parseável, o report sai normal.
- **Bootstrap:** roda no hook `before_wp_load`, antes do WP carregar
  (não inicializa plugins/themes) — compatível com `safe_only` (ADR-009).
- **Rede:** baixa md5 do WordPress.org por versão+locale (dado egresso
  documentado; modo offline usa cache futuro — WIRS-045).
- **Mutação do target:** nenhuma (somente leitura + download de checksums).
- **Timeout/concorrência:** `timeout_s` configurável (default 60s); processo
  encerrado no estouro; uma execução por vez por enquanto.
- **Licença:** MIT (wp-cli/checksum-command). Integração por subprocess —
  sem vínculo de distribuição.
- **Fallback:** ausente/timeout/saída inválida → `ProviderUnavailable` /
  `ProviderTimeout` / `ProviderInvalidOutput` (Coverage degrada, scan continua).
  Fallback nativo com manifests oficiales é pós-MVP.
- **Riscos:** stderr/stdout podem conter paths do alvo (tratados como dados
  hostis, cap de output, sem interpolação em shell).
