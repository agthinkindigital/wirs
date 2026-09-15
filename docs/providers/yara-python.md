# docs/providers/yara-python.md

Contrato validado via `query-docs` (fontes oficiais) em 2026-09-12.

## Fontes

- https://yara.readthedocs.io/en/stable/yarapython.html (YARA 4.4.0)
- https://github.com/VirusTotal/yara/blob/master/docs/yarapython.rst
- https://pypi.org/project/yara-python/ (versão consultada: **4.5.4**)

## Contrato relevante para o WIRS

| Ponto | Contrato |
|---|---|
| Compile | `yara.compile(filepath=…)` / `source=` / `filepaths=` / `sources=`; `externals=`; `includes=` (default True); `error_on_warning=` |
| Erro de compilação | `yara.SyntaxError`; outros erros: `yara.Error` |
| Match | `rules.match(filepath=…)` / `data=` / `pid=`; `timeout=` (segundos); `externals=` |
| Resultado | lista de `yara.Match`: `.rule`, `.namespace`, `.tags`, `.meta`, `.strings[]` (`.identifier`, `.instances[]` com `.offset`, `.matched_length`) |
| Timeout | `yara.TimeoutError` |
| Save/load | `rules.save(filepath=…)` (compilado reutilizável) |

## Decisões WIRS (ADR-006 + E07)

- `yara-python` é **dependência opcional** (`pip install wirs[yara]`); ausente → provider `UNAVAILABLE`, scan continua.
- Match só sobre **bytes lidos pelo ArtifactReader** (`data=`), nunca `filepath=` direto do alvo (o reader impõe budget; detector não abre arquivo).
- `timeout` sempre configurado (default de 60s por Artifact).
- Regras builtin em `rules/yara/` (WIRS-082); `include` desabilitado nos packs builtin (`includes=False`) — pack é dado versionado, não programa.
- Saída cruza anti-corruption layer: `ProviderFinding` vaza para o application e é convertido em `Evidence` + `Finding` com provenance do provider.

## Checklist /query-docs do provider

1. Executa código do target? Não (match sobre bytes; regras são do pack versionado).
2. Modifica o target? Não.
3. Rede? Não.
4. API key? Não.
5. Exit codes? N/A (binding, exceções tipadas).
6. Machine-readable? Sim (objetos Match).
7. Output com texto do target? Strings casadas contêm bytes do alvo → snippets limitados + redaction.
8. Timeout/cancel? `timeout=`; cancel cooperativo entre arquivos.
9. Concurrency? Scheduler central (provider não cria pool).
10. Falha parcial distinguível? SyntaxError vs TimeoutError vs Error.
11. Licença? YARA BSD-3-Clause; yara-python mesma licença (verificar na integração).
12. Offline? Sim.
13. Egresso? Não.
14. Compatibilidade? 4.x API estável (compile/match/Match).
15. Fallback? Ausência graciosa (UNAVAILABLE); falhas de leitura/match são PARTIAL.

## Integração atual

`wirs scan` monta o pack builtin a partir do checkout ou do wheel, executa o
analyzer sobre os Artifacts `FILE` e publica refs canônicas. O pack é compilado
com `includes=False`; nenhum include externo pode abrir arquivos durante a
compilação. O YARA recebe bytes via `ArtifactReader`, nunca o path do target.
