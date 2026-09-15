# Arquitetura do WIRS

Este documento conta como o sistema foi pensado e como as peças se encaixam.
Glossário em [`CONTEXT.md`](../CONTEXT.md), decisões registradas em
[`adr/`](adr/), especificação completa em
[`WIRS_MASTER_SPEC_PT-BR.md`](../WIRS_MASTER_SPEC_PT-BR.md).

## A dor

Investigar um WordPress comprometido costuma ser um amontoado de ferramentas
desconectadas: integridade diz que um arquivo mudou, o antivírus acusa uma
assinatura, o banco esconde um payload, o cron garante a volta do invasor — e
o analista correlaciona tudo na mão, sem registro do que ficou sem verificar.
Pior: muita ferramenta resume o caso num veredito opaco ("INFECTED 94%") que
ninguém consegue auditar depois.

O WIRS não inventa mais um detector isolado. O valor dele está em **normalizar
evidências heterogêneas, preservar a proveniência de cada fato, medir o que
foi coberto e correlacionar findings em hipóteses explicáveis**.

## A ideia central

Todo scan produz três coisas distintas, nunca misturadas:

1. **Fatos** — observações determinísticas e reproduzíveis (hash calculado,
   checksum oficial divergente, arquivo esperado ausente, IOC literal, versão).
2. **Suspeitas** — heurísticas com chance real de falso positivo (ofuscação,
   PHP em diretório de mídia, entropia alta, persistência anômala).
3. **Diagnósticos** — hipóteses derivadas da correlação ("mismatch confiável +
   assinatura no mesmo arquivo = adulteração provável"), sempre com
   alternativas e próximos checks.

E junto das três, o **coverage**: o que foi analisado, pulado, ilegível, sem
baseline, com provider falho. "Zero findings" sem coverage completo não
significa "limpo" — o relatório diz isso com todas as letras.

## O pipeline alvo

```text
validar config → resolver target → manifest do scan → descobrir plataforma
→ inventariar artifacts → metadata → resolver baselines
→ coletar/ler com redaction de secrets na fronteira
→ checks determinísticos → políticas de zona → IOCs exatos
→ heurísticas leves → analyzers externos (opcionais)
→ collectors de fontes locais → Evidence temporal → normalizar → correlacionar
→ fechar coverage → diagnósticos → validar redaction → relatórios → exit code
```

Na versão atual, o pipeline termina após detecção, content analysis bounded,
analyzers externos, Coverage e views de terminal/JSON/Markdown. O report
canônico publica Artifacts/Evidence e o YARA builtin participa do `scan` quando
o extra opcional está disponível; ausência e falhas ficam explícitas no
Coverage. Incident Bundle, collectors temporais, correlação, Diagnoses e
HTML/PDF são capacidades futuras, não entregas atuais. A próxima DAG é
Diagnosis file-centric.

A ordem importa: o barato e confiável roda primeiro; o caro e incerto, depois.
Falha parcial é o comportamento padrão — um provider ausente vira
`UNAVAILABLE` no coverage, não um abort. Só se aborta quando a validade do
próprio alvo está em jogo.

## Como as pastas conversam

A dependência aponta sempre para dentro, em direção ao domínio:

```text
cli ──▶ application ──▶ domain ◀── ports ◀── infrastructure / providers / adapters
                                    ▲
                              reporting (lê o modelo, nunca o altera)
```

- **`domain/`** — value objects puros, só stdlib. Não sabe o que é WordPress,
  YARA, banco ou terminal. É o vocabulário do negócio (Target, Artifact,
  Evidence, Finding, Diagnosis, Baseline, Coverage).
- **`application/`** — os casos de uso que orquestram um scan
  (`ScanOrchestrator`, `InventoryService`, `IntegrityService`,
  `DetectionService`, `CoverageService`, `CorrelationService`,
  `ReportService`). Conhecem `domain/` + `ports/`, nada de ferramenta externa.
- **`ports/`** — as poucas fronteiras que realmente variam: `ArtifactSource`,
  `ArtifactReader`, `BaselineProvider`, `ExternalAnalyzer`,
  `PlatformAdapter`, `CommandRunner`, `DatabaseReader`, `Reporter`.
- **`infrastructure/`** — implementa ports com filesystem, scheduler central
  (só ele decide concorrência), hashing e config.
- **`detectors/`** — regras internas. Não abrem arquivo direto (usam o
  `ArtifactReader`, que compartilha leitura/hash/budget) e nunca criam
  subprocess — se precisar de processo externo, é provider, via `CommandRunner`.
- **`providers/`** — WP-CLI, YARA, Wordfence CLI. Cada saída cruza uma
  anti-corruption layer que traduz o formato do vendor para o modelo interno;
  código da aplicação nunca toca em campo específico de vendor.
- **`adapters/wordpress/`** — tudo que é específico de WP (discovery por
  combinação de sinais, classificação de zonas, versão/locale, collectors
  `safe_only`). É o único lugar que pode falar `wp-content`.
- **`reporting/`** — consome o modelo final em modo read-only e renderiza as
  views (JSON canônico primeiro; terminal, Markdown e HTML derivam dele).
- **`cli/`** — composition root: monta as implementações, lê config/flags e
  traduz o resultado em exit code.

Um exemplo do fluxo de detecção atual: o inventory cria o `Artifact`; o reader
faz streaming único que alimenta hash, hints e IOC; o comparator de baseline
gera `Evidence` + `Finding` determinístico; a policy de zona e a heurística
somam suspeitas. Nas etapas incrementais, YARA anexa a própria provenance e a
correlação pode juntar mismatch + assinatura no mesmo Artifact em um
`Diagnosis`; o Coverage registra o que não rodou. Conteúdo persistido como
Evidence já cruza redaction na coleta; o reporter valida novamente e serializa
o modelo, e o terminal resume em tabela.

Uma investigação heterogênea usa um **Incident Bundle**: uma pasta local com
manifesto versionado que declara webroots, logs, snapshots e archives. Arquivo
de log continua sendo Artifact; cada registro aceito vira Evidence temporal
ligada ao Artifact e à posição de origem. `occurred_at` registra o horário da
fonte e `collected_at`, o horário da coleta. O WIRS não transforma coincidência
de IP/CIDR/User-Agent em identidade ou autoria.

## Fronteiras que não se atravessam

- Scan **não escreve** no alvo; banco é lido com menor privilégio e só `SELECT`.
- Detector **não executa** código do alvo; WP-CLI roda em `safe_only` por padrão.
- Dado do alvo **nunca** é interpolado em shell (`shell=False`, argv allowlisted).
- **Symlink não é seguido** para fora do root; arquivo especial nunca é lido como comum.
- Componente **sem baseline é `UNVERIFIED`**, nunca malicioso por definição.
- Saída de IA **não é evidência** — o LLM, quando habilitado, só sugere sobre um pacote redigido.
- Domínio **não importa** plataforma, provider, UI ou driver de banco (há teste de arquitetura para isso).

## Saídas

O **JSON é canônico** (versão de schema separada da versão do scanner, ordem
estável, sem conteúdo bruto por padrão). Terminal serve à operação, Markdown
vai para ticket, e HTML/PDF forense são views self-contained. O artifact
canônico deve preservar Scan Manifest, source manifest do Incident Bundle,
Artifacts, Evidence metadata, Findings, Coverage, provider status e Diagnoses.
Nenhuma regra de negócio mora no frontend.

## Para onde vai

WordPress é o adapter #1 porque o ecossistema dá primitives fortes
(checksums oficiais, WP-CLI, layout previsível). Antes de 1.0, a mesma engine
recebe PHP genérico, bundles/archives locais, correlação file-centric e laudo
forense. Logs locais enriquecem o modelo depois do núcleo. SSH/SFTP, runtime
HTTP ativo, agentes residentes e control plane ficam em horizontes posteriores,
em seams separados. O passo a passo está no
[roadmap](../ORCHESTRATOR-ROADMAP.md).
