# Linguagem do WIRS

Este arquivo é exclusivamente um glossário. Regras, fluxos, comandos e detalhes
de implementação pertencem ao `WIRS_MASTER_SPEC_PT-BR.md`, aos ADRs e aos
documentos do módulo.

## Core genérico

**Scan**: uma execução do scanner sobre um Target.

**Target**: o que está sendo analisado (diretório local, Incident Bundle,
snapshot ou archive; SSH/SFTP somente pós-1.0).

**Incident Bundle**: coleção local e somente leitura que reúne uma ou mais
fontes de uma investigação (webroots, logs, snapshots e archives) sob um
manifesto versionado. O manifesto preserva papel, origem e integridade de cada
fonte; o WIRS não precisa autodescobrir a máquina nem acessar rede.

**Artifact**: objeto lógico analisável (arquivo, diretório, symlink, registro de banco,
entrada de configuração, evento de cron, conta, resposta HTTP, componente, saída de analyzer).

**Evidence**: observação imutável criada por collector ou detector, com
provenance e estado de redaction. Quando representa um evento de log,
`occurred_at` é o horário registrado pela fonte e `collected_at` é o horário em
que o WIRS o coletou; um não substitui o outro.

**Finding**: afirmação normalizada de segurança/integridade sustentada por Evidence
(rule ID, severidade, confiança, categoria, atributos).

**Diagnosis**: hipótese correlacionada a partir de Findings (título, confiança,
base, alternativas, próximos checks). Nunca transforma heurística em fato determinístico.

**Baseline**: expectativa de conteúdo para comparação (checksum oficial upstream,
package confiável do operador, manifest assinado, golden snapshot).

**Provider**: implementação de uma capability, muitas vezes via ferramenta externa
(WP-CLI, YARA, Wordfence CLI). Output cruza anti-corruption layer.

**Rule**: lógica que gera Finding, com severidade/confiança/maturidade declaradas.

**Coverage**: abrangência real da análise. Estados: `COMPLETE`, `PARTIAL`,
`SKIPPED`, `UNAVAILABLE`, `FAILED`, `NOT_APPLICABLE`.

**Actor**: entidade ou conjunto de identificadores que uma fonte associa a uma
ação (conta, IP, sessão, User-Agent). Compartilhar IP, CIDR ou User-Agent é pista
de relação, não prova de que eventos vieram da mesma pessoa.

**Unverified**: sem baseline suficiente para verificação de integridade.

**Skipped**: pulado deliberadamente (política, budget, modo).

**Unavailable**: capability/provider não disponível no ambiente.

## Confiança e severidade

**Confidence**: `DETERMINISTIC`, `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN` (score 0.0–1.0 opcional, complementar).

**Severity**: `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`. Severidade e confiança são independentes.

## Baselines

**TRUSTED_UPSTREAM**: manifest oficial (ex.: WordPress.org).
**TRUSTED_OPERATOR**: package limpo explicitamente confiado pelo operador.
**TRUSTED_SIGNED_INTERNAL**: release manifest assinado / artifact de CI conhecido.
**UNVERIFIED_REFERENCE**: referência que ajuda no diff mas não sustenta linguagem de violação.

## WordPress (adapter — nunca no core)

**Zone**: região do filesystem com expectativa própria (`wp-core-protected`,
`wp-root-special`, `wp-content-plugins`, `wp-content-themes`,
`wp-content-mu-plugins`, `wp-content-uploads`, `wp-content-cache`,
`wp-content-upgrade`, `wp-content-other`).

**VERIFIED / MISMATCH / MISSING_EXPECTED_FILE / UNEXPECTED_FILE /
UNVERIFIED_NO_BASELINE / PROVIDER_FAILED / NOT_APPLICABLE**: estados de
verificação de componente.

**safe_only**: modo WP-CLI padrão — apenas comandos pré-bootstrap; nunca executa
código do alvo para analisá-lo.
