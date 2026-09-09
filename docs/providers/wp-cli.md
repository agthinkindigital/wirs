# WP-CLI — provider de checksums WordPress

- **Versão testada:** 2.12.0, validada contra binário real em 2026-09-09
  (WordPress oficial baixado, adulterado de propósito, provider executado de
  verdade: MISMATCH + UNEXPECTED detectados corretamente).
- **Doc oficial:** https://developer.wordpress.org/cli/commands/core/verify-checksums/
  e https://developer.wordpress.org/cli/commands/plugin/verify-checksums/
  (fonte: https://github.com/wp-cli/checksum-command — lida para o formato de plugins).
- **Comandos usados:** `wp --version` (doctor),
  `wp core verify-checksums --include-root --path=<target>` (**sem**
  `--format`: o core 2.12.0 rejeita) e
  `wp plugin verify-checksums --all --strict --format=json --path=<target>`
  (`--version`/`--locale` quando WIRS-062 entregar a versão do alvo).
- **Output core (REAL):** tudo no STDERR, stdout vazio. Linhas
  `Warning: File doesn't verify against checksum: <file>` → MISMATCH,
  `Warning: File doesn't exist: <file>` → MISSING,
  `Warning: File should not exist: <file>` → UNEXPECTED.
  `Success:`/`Error:` são resumo, não evidência. Warning desconhecido =
  `ProviderInvalidOutput`. Sem warnings + exit != 0 = `ProviderExecutionError`
  (quebrou antes de verificar, ex.: sem rede).
- **Output plugins (REAL, fonte lida):** erros em JSON
  `[{plugin_name, file, message}]` no STDOUT (`'File was added'` → UNEXPECTED,
  `'Checksum does not match'` → MISMATCH); plugins sem baseline **não aparecem
  no JSON** — viram warnings no STDERR (`Could not retrieve the ... skipping`,
  `main file is missing`, `appears to be a custom file`) → `unverified_plugins`.
  Resumo final em texto puro é ignorado (não é evidência).
- **Exit codes:** diferente de zero quando algo diverge — é *sinal*, não erro:
  com saída parseável, o report sai normal.
- **Bootstrap:** core roda no hook `before_wp_load` (não inicializa
  plugins/themes) — compatível com `safe_only` (ADR-009). Atenção: `plugin
  verify-checksums` exige `wp-config.php` (+ DB para enumerar) — documentado
  como requisito, não como escrita nossa.
- **Rede:** baixa md5 do WordPress.org por versão+locale (dado egresso
  documentado; modo offline usa cache futuro — WIRS-045).
- **Mutação do target:** nenhuma (somente leitura + download de checksums).
- **Timeout/concorrência:** `timeout_s` configurável (60s core, 120s plugins);
  processo encerrado no estouro; uma execução por vez por enquanto.
- **Licença:** MIT (wp-cli/checksum-command). Integração por subprocess —
  sem vínculo de distribuição.
- **Fallback:** ausente/timeout/saída inválida → `ProviderUnavailable` /
  `ProviderTimeout` / `ProviderInvalidOutput` (Coverage degrada, scan continua).
  Fallback nativo com manifests oficiais é pós-MVP.
- **Riscos:** stderr/stdout podem conter paths do alvo (tratados como dados
  hostis, cap de output, sem interpolação em shell).
- **Windows:** shims `.cmd`/`.bat` não executam via CreateProcess direto — o
  CommandRunner prefixa `cmd.exe /d /c` com argv em lista (`shell=False`
  mantido) e o doctor executa o caminho resolvido, nunca o nome nu.
