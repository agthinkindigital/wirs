# Entendendo o WIRS: o porquê de cada peça

Este documento é para aprender. Cada seção explica **uma slice do projeto**
com as mesmas palavras usadas nas revisões de entrega: primeiro **o que** a
peça é e **por que** ela existe, depois as **decisões de desenho** que a
moldaram. Leia na ordem — cada peça se apoia nas anteriores, igual ao código.

Toda slice nova ganha sua seção aqui antes de ser dada como concluída. É
assim que o conhecimento da construção vira conhecimento do time.

---

## #17 — Scaffold: o terreno antes da casa (WIRS-001)

### O que é o scaffold e por que ele vem primeiro

Antes de qualquer detector, precisávamos de um repositório que compila, testa,
passa lint, checa tipos e publica no CI — porque ferramenta de segurança sem
esteira confiável é opinião, não engenharia. O scaffold entregou o pacote
Python importável, a CLI mínima (`version`, `doctor`, `scan`), a suite de
testes, o Ruff, o `mypy strict` e o CI na matrix 3.11–3.14. E o `wirs scan`
nasceu como **esqueleto honesto**: valida o target (inválido → exit 2) e
declara "engine em construção" com coverage explícito (exit 3) em vez de
fingir um resultado.

### Decisões de desenho

- **Python `>=3.11`, sem exigir o bleeding edge**: o dev roda no 3.14 local,
  mas o scanner precisa funcionar em VPS e hospedagem comum (Ubuntu 22.04
  entrega 3.10, 24.04 entrega 3.12). Travar no 3.14 seria excluir os
  ambientes que mais precisam da ferramenta.
- **Typer + Rich**: CLI declarativa com `--help` de graça e terminal legível
  sem reinventar formatação — o foco é WordPress e incident response, não
  framework de CLI.
- **`uv` via scoop**: venv + lock + instalação rápida no mesmo canal das
  outras ferramentas da máquina, sem poluir o Python global.
- **Esqueleto que confessa, não que finge**: exit 3 com coverage explícito em
  vez de "0 findings". A honestidade do relatório começou no dia zero.
- **LF travado no `.gitattributes`**: diverging CRLF/LF já mordeu outro
  projeto da casa; aqui o repo normaliza na entrada.

**Verificar:** `pyproject.toml`, `src/wirs/cli/app.py`, `.github/workflows/ci.yml` · **Issue:** #17 (fechada).

---

## #18 — Fronteiras que o compilador não vê (WIRS-002)

### O que são os guardas de arquitetura e por que testes, não convenção

Python não tem visibilidade de pacote como Java: nada na linguagem impede
`domain/` de importar `wordpress`, um detector de chamar `subprocess` ou um
provider de espalhar formato de vendor pela aplicação. Como as invariantes
arquiteturais são o coração do produto (é nelas que mora a segurança do
scanner), elas viraram **testes que varrem imports reais via AST** e quebram
o build quando a fronteira é cruzada. Convenção se esquece; teste quebrado
não passa no CI.

### Decisões de desenho

- **Três guardas, três fronteiras**: domain só-stdlib (sem wordpress, yara,
  wordfence, rich, mysql, typer), detectors sem subprocess, subprocess em
  geral só via `CommandRunner` (allowlist com um único futuro morador).
- **Prova por mutação, não por fé**: cada guarda foi verificado injetando a
  violação de propósito (quebra), revertendo (volta ao verde) e conferindo a
  árvore limpa. Teste de guarda que nunca foi visto quebrar é decoração.
- **Helper compartilhado, sem especulação**: a varredura AST mora num helper
  comum do arquivo de teste — o suficiente para hoje, sem framework de
  "architecture tests" antes da hora.

**Verificar:** `tests/unit/test_architecture.py` · **Issue:** #18 (fechada).

---

## #19 — Target: onde é permitido olhar (WIRS-010)

### O que é o Target e por que ele congela a pergunta inicial

Todo scan começa respondendo "o quê, exatamente, estou analisando?" — e essa
resposta precisa ser **congelada**, porque todo o resto (IDs, coverage,
comparação entre scans) depende dela não mudar no meio do caminho. O `Target`
é um dataclass imutável com kind (`local_directory`, `snapshot_directory`,
`archive`), root normalizado e metadata imutável. Raiz inexistente ou
arquivo-como-root vira `TargetError`: alvo inválido nunca produz "scan vazio
válido" — que seria o falso negativo mais perigoso do produto, um relatório
limpo sobre nada.

### Decisões de desenho

- **ID determinístico** (`tgt_<sha256:16>` de kind + root): dois scans do
  mesmo alvo geram o mesmo ID, base para comparar relatórios no tempo e,
  no futuro, cachear trabalho.
- **Metadata em `MappingProxyType`, não dict**: dicionário mutável num objeto
  "imutável" é mentira — o congelamento é real, testado por tentativa de
  escrita.
- **Normalização com `pathlib` apenas**: o SafePath (#20) ainda não existia
  (ordem da DAG), então o Target resolve o root sozinho sem criar dependência
  para frente. Cada slice usa só o que já existe.
- **`WirsError` como base da hierarquia**: `TargetError` herda dela para que
  camadas externas capturem "erro do scanner" sem conhecer cada tipo — o
  núcleo do modelo de erros do spec.

**Verificar:** `src/wirs/domain/target.py`, `src/wirs/domain/errors.py`,
`tests/unit/test_target.py` · **Issue:** #19 (fechada).

---

## #20 — SafePath: o único lugar onde path sujo vira path confiável (WIRS-011)

### O que é o SafePath e por que ele é security critical

Todo o resto do scanner vai manipular caminhos vindos de um **alvo hostil**:
nomes criados por um invasor para escapar do diretório (`../../etc/cron.d/x`),
para quebrar relatórios (`<script>`, ANSI, quebras de linha) ou para explorar
peculiaridades do Windows (`C:\...`, `\\server\...`). O `SafePath` é o
**único lugar** onde um caminho sujo vira confiável — um value object imutável
que carrega `root` + `relative` canônico e só existe se o confinamento for
válido. Sem ele, cada detector validaria path por conta própria, e algum dia
algum deles erraria.

### Decisões de desenho

- **Confinamento lexical, sem tocar o filesystem**: `..` que escapa, path
  absoluto, drive e UNC viram `SecurityBoundaryError`. `a/b/../c` resolve para
  `a/c`, mas `a/../..` é rejeitado — e o TDD forçou a explicitar que `a/..`
  é o próprio root (benigno), não ataque.
- **`\` sempre vira `/`**: código único para Windows e Linux, e o `relative`
  é estável no JSON independente da plataforma que escaneou.
- **NUL rejeitado em voz alta** (nunca truncado em silêncio) e **Unicode em
  NFC** (`e + acento combinante` vira `é`), para que comparação e exibição não
  tenham duas formas do "mesmo" nome.
- **O achado do property test**: o Hypothesis gerou `raw='::'` e quebrou o
  invariante — no Windows, `Path(root).joinpath('::')` **descarta o root
  inteiro** (o segmento é interpretado como drive). O `full` passou a ser
  construído por concatenação em parse único e ancorado, que mantém contenção
  para qualquer segmento. Virou regressão parametrizada.
- **Fora de escopo de propósito**: escape via symlink (é do inventory, nunca
  follow — ADR-008) e nomes de dispositivo (`CON`, `NUL` — não escapam o root,
  viram erro de OS tratado como gap na #22).

**Verificar:** `src/wirs/domain/safepath.py`, `tests/unit/test_safepath.py`
(inclui property test) · **Issue:** #20 (fechada).

---

## #21 — Artifact: a unidade que atravessa o pipeline (WIRS-012)

### O que é o Artifact e por que ele é o centro do sistema

Com *onde* olhar (Target) e *como* nomear com segurança (SafePath), faltava
*o que* é analisável. O `Artifact` é essa peça: a unidade lógica que atravessa
o pipeline inteiro — o inventory os produz, o hash/IOC/heurísticas os
consomem, os findings os referenciam, o coverage os conta. Sem um modelo
único, cada detector inventaria sua própria representação de "arquivo" e a
correlação futura seria impossível.

### Decisões de desenho

- **4 kinds, sem hierarquia de classes**: `FILE`, `DIR`, `SYMLINK` e `SPECIAL`
  como enum, não subclasses. A distinção que importa para as regras é kind +
  metadata, e um único tipo congelado mantém serialização e comparação
  triviais. FIFO/socket/device viram `SPECIAL` — o scanner nunca os abre como
  arquivo comum.
- **ID estável que inclui o kind** (`art_<sha256:16>`): um path que vira de
  arquivo para symlink *é* outro artifact, e dois scans geram os mesmos IDs —
  base para comparar relatórios e, no futuro, cachear hashes.
- **Construído sobre SafePath, não sobre string**: impossível criar Artifact
  com path fora do root — a garantia da #20 é herdada, não revalidada.
- **`from_stat` puro, sem I/O**: recebe o `stat` já coletado e só mapeia
  campos (com `getattr` defensivo para `uid`/`gid`, ausentes no Windows).
  Quem toca disco é o inventory; o modelo interpreta.
- **Symlink carrega o destino como dado** (`symlink_target: str`), nunca
  seguido — coerente com o ADR-008.
- **Metadata honesta sobre ausência**: tudo opcional (`None` quando
  indisponível) em vez de zeros inventados que pareceriam fatos.
- **Round-trip total** (`to_dict`/`from_dict` com igualdade completa): o que
  vai permitir o JSON canônico sem camada extra de conversão.

**Verificar:** `src/wirs/domain/artifact.py`, `tests/unit/test_artifact.py` ·
**Issue:** #21 (fechada).

---

## #22 — Inventory: a fronteira onde o scanner toca o disco (WIRS-013)

### O que é o inventory e por que ele concentra as decisões de leitura

Até aqui, tudo era modelo puro: nenhum módulo lia nada do alvo. O
`LocalArtifactSource` é a fronteira onde isso muda — e justamente por isso
concentra **todas** as decisões de segurança de leitura num lugar só, para
que nenhum detector precise pensar nisso depois. A regra: o inventory
caracteriza entradas (*o que* cada coisa é) mas nunca interpreta conteúdo
(isso é dos detectores, via `ArtifactReader`).

### Decisões de desenho

- **Um gerador, memória bounded**: função geradora com pilha explícita — nunca
  materializa a árvore. Em 100 mil arquivos, o pico fica proporcional à
  profundidade, não ao total. O teste prova streaming pelo tipo
  (`isgeneratorfunction`), não por medição frágil de RSS.
- **Ordem determinística**: entradas ordenadas por nome em cada diretório
  (pilha LIFO com subdirs em reverso mantém depth-first ordenado). Sem isso,
  relatórios e IDs correlacionados seriam instáveis entre runs.
- **Symlink: dado, nunca caminho**: registrado como `SYMLINK` com destino de
  `readlink` (que não segue), e o walker jamais desce por ele. Loops e escapes
  impossíveis *por construção*. Prova com link interno, externo e quebrado.
- **`SPECIAL` como quarentena**: FIFO/socket/device viram `SPECIAL` via
  `stat` e jamais são abertos. A prova é um teste que *travaria para sempre*
  se tentássemos abrir o FIFO.
- **Falha parcial como tipo**: entrada ilegível vira `InventoryGap(path,
  reason)` e o scan continua; só root ilegível vira `TargetError`. Os gaps
  são o insumo direto do Coverage.
- **Portabilidade honesta**: symlink e FIFO exigem privilégio/recursos que o
  Windows de dev não tem — skip explícito aqui, execução no CI Linux — em vez
  de cobertura fingida. Permissão negada é simulada via `monkeypatch` (testa
  o *tratamento*, portável, não o chmod do OS, que não é).

**Verificar:** `src/wirs/infrastructure/filesystem.py`,
`tests/integration/test_inventory.py` · **Issue:** #22 (fechada).

---

## #23 — Evidence: a moeda da explicabilidade (WIRS-020)

### O que é a Evidence e por que nada existe sem ela

Princípio P2, "evidência antes de interpretação": a `Evidence` é a
**observação imutável** que um collector ou detector produziu — a outra metade
do Artifact (ele diz *o que foi olhado*, ela diz *o que foi visto*). Findings
vão apenas referenciar evidências; diagnósticos vão correlacionar findings.
Toda a cadeia de explicabilidade do relatório nasce aqui.

### Decisões de desenho

- **ID determinístico, não aleatório** (`ev_<sha256:16>` de scan + kind +
  artifact + conteúdo canônico, *sem* timestamp): a mesma observação deduplica
  entre scans. O timestamp registra *quando*, não compõe *o quê*.
- **`kind` aberto (string), não enum**: nenhum detector existe ainda para
  fixar o vocabulário, e rule packs futuros vão inventar kinds. Rígida é a
  *estrutura*, não o vocabulário.
- **`Provenance` obrigatória sem default**: sem `collector` + `version`, o
  construtor nem aceita. A invariante "finding não existe sem provenance"
  começa a ser imposta aqui — o finding herdará de graça.
- **`content` restrito a JSON-serializável na construção**: bytes ou objetos
  arbitrários viram `ValueError` na hora, não na hora do relatório. É a
  fundação do "dado canônico independente da UI". O próprio TDD pegou a
  armadilha: o congelamento com `mappingproxy` quebrou a canonicalização e
  foi preciso serializar o `dict` interno.
- **`RedactionState` explícito** (`none`/`redacted`): distingue "não havia
  secret" de "houve e foi redigido" — prepara a redaction na fronteira.
- **`artifact_ref` como string, não objeto**: sem import circular,
  serialização trivial, pronto para o futuro evidence graph.

**Verificar:** `src/wirs/domain/evidence.py`, `tests/unit/test_evidence.py` ·
**Issue:** #23 (fechada).

---

## #24 — Finding: a linha entre fato e chute (WIRS-021)

### O que é o Finding e por que severidade e confiança não se misturam

Evidências ninguém lê em volume; findings dizem o que elas *significam* —
"este arquivo do core diverge do baseline oficial". Cada finding carrega
**severidade** (quão grave, *se* verdade) e **confiança** (quão certo estamos)
como eixos *independentes*. Um `CRITICAL + DETERMINISTIC` (checksum oficial
divergiu) e um `CRITICAL + LOW` (heurística isolada) coexistem no relatório sem
se confundir — é isso que impede o produto de colapsar tudo num "INFECTED"
opaco.

### Decisões de desenho

- **Invariante 2 como exceção**: sem `evidence_refs` e sem `provenance`, o
  construtor levanta `ValueError`. Finding órfão é impossível por construção.
  A válvula (`provenance` de provider, ex. Wordfence CLI) existe porque finding
  externo chega sem evidência interna — mas aí a proveniência viaja junto.
- **Confiança em duas partes**: classe honesta + score 0–1 validado, que
  complementa sem fingir precisão. Número inventado em relatório de incidente
  é pior que ausência de número.
- **O ID ignora severidade e ordem**: deriva de regra + artifact + evidências
  + atributos — reclassificar a gravidade não muda a identidade (histórico e
  correlação estáveis quando a regra amadurece), e `("ev_2","ev_1")` gera o
  mesmo ID que `("ev_1","ev_2")`.
- **`category` aberta como `kind`**: `integrity`, `policy`, `ioc`... virão das
  regras; travar enum agora seria adivinhar o futuro.
- **`status` com default `"open"`**: o único default — ciclo de vida pertence
  a outra Epic; o default só evita burocracia no construtor agora.

**Verificar:** `src/wirs/domain/finding.py`, `tests/unit/test_finding.py` ·
**Issue:** #24 (fechada).

---

## #25 — Coverage: o antídoto contra o "está limpo" (WIRS-023)

### O que é o Coverage e por que o falso negativo silencioso é o pior bug

O problema mais caro em incident response não é o falso positivo — é o
**falso negativo silencioso**: o scanner roda, não acha nada, e o analista
conclui "limpo" sem saber que o YARA estava ausente e 300 arquivos eram
ilegíveis. O `CoverageEntry` torna essa ignorância *visível e tipada*: cada
capability declara seu estado em 6 valores, com a contabilidade exata de cada
check aplicável.

### Decisões de desenho

- **O invariante como exceção**: `verified + failed + skipped + unavailable`
  precisa igualar `applicable_checks` — nem check em dois baldes, nem check
  perdido. Contador negativo também recusa.
- **Estado e contadores amarrados**: `COMPLETE` exige tudo verificado (completo
  vazio é suspeito, não vitória); `PARTIAL` exige ao menos 1 não-verificado;
  `UNAVAILABLE`/`SKIPPED`/`NOT_APPLICABLE` têm forma própria. YARA com 10
  indisponíveis **não compila** como `COMPLETE` — o teste nominal do ADR-010.
- **`FAILED` deliberadamente frouxo**: capability que quebrou por inteiro
  descreve o estrago como estava — impor forma ali seria inventar precisão
  sobre naufrágio.
- **`note` livre para contexto humano**: "2 plugins premium sem baseline"
  viaja com os números, porque coverage sem explicação vira outro número opaco.
- **Só o tijolo, sem a parede**: o relatório consolidado pertence ao futuro
  `ReportService` — aqui sai a entry validada, sem especular o agregador.

**Verificar:** `src/wirs/domain/coverage.py`, `tests/unit/test_coverage.py` ·
**Issue:** #25 (fechada).

---

## #26 — ArtifactReader: o gargalo obrigatório (WIRS-030)

### O que é o reader e por que todo detector lê por ele

O inventory só fez `stat` — nunca abriu conteúdo. Mas hash, IOC e heurísticas
precisam *ler* arquivos. Se cada detector abrisse por conta própria, teríamos
N leituras do mesmo arquivo, N políticas de limite e N chances de abrir a
coisa errada (FIFO que trava, symlink para fora do root, 40 GB na RAM). O
`ArtifactReader` é o **único caminho para conteúdo**: todo detector futuro lê
por ele, herdando streaming, budget, cancelamento e travas de graça.

### Decisões de desenho

- **Recusa antes do disco**: não-`FILE` levanta `SecurityBoundaryError` sem
  nenhuma chamada ao filesystem. O caso crítico é o symlink — abrir o `full`
  seguiria o destino. O teste usa paths inexistentes de propósito: se tocasse
  o disco, daria `FileNotFoundError` em vez do guarda.
- **Sempre `rb`, nunca texto**: bytes crus (o teste cobre os 256 valores,
  incluindo não-UTF-8). Decoding é decisão do detector — sem `UnicodeDecodeError`
  em arquivo hostil.
- **Budget com fronteira exata**: `BudgetExceeded` carrega `bytes_read`
  (permite relatar "hash parcial de X bytes"); arquivo que termina *exatamente*
  no limite não é erro — punir o caso-limite geraria falsos gaps.
- **Cancelamento cooperativo, sem threads**: `should_stop()` por chunk levanta
  `ReadCancelled`. O scheduler futuro só passa o callback.
- **`ReadBudget` validado na construção**: limite inválido silencioso
  significaria "leia tudo" ou "leia nada" conforme o cliente.
- **Erros na família `WirsError`**: `BudgetExceeded` e `ReadCancelled` são
  recuperáveis, feitos para virar Coverage — nunca abortar scan. A decisão do
  que fazer com falha de leitura é do orquestrador, não do leitor.

**Verificar:** `src/wirs/infrastructure/reader.py`, `tests/unit/test_reader.py` ·
**Issue:** #26 (fechada).

---

## #27 — HashService: ler uma vez, servir N detectores (WIRS-031)

### O que é o HashService e por que ele é separado do reader

O reader sabe *ler bytes com segurança*; mas quase todo detector vai precisar
do *hash* do mesmo arquivo — integridade, IOC por SHA-256, identidade,
deduplicação. Sem serviço central, cada detector leria tudo de novo ou
inventaria seu cache com sua invalidação. O `HashService` resolve: **uma
instância por scan, dona do cache, alimentada pelo reader em streaming**.

### Decisões de desenho

- **Memo na instância, não global**: o cache morre com o scan. Vazamento entre
  scans seria um falso `VERIFIED` catastrófico — impossível por construção, sem
  precisar lembrar de invalidar.
- **Chave `(artifact.id, algorithm)`**: o ID já é determinístico, então a chave
  herda estabilidade; o algoritmo entra porque o mesmo arquivo tem digest
  diferente em SHA-256 e MD5 — sem isso, pedir MD5 depois devolveria o hash
  errado em silêncio.
- **SHA-256 interno, MD5 só compatível**: o parâmetro `algorithm` existe para
  respeitar baseline upstream (checksums MD5 do WordPress.org). O linter
  acusou S324 e a resposta documenta `usedforsecurity=False` — MD5 aqui é
  *comparação com referência oficial*, nunca prova de segurança.
- **Prova de leitura única via spy, não mock**: subclasse que conta invocações
  reais e delega ao comportamento verdadeiro. Duas consultas → 1 leitura de
  disco, testado pela interface pública.
- **Erros propagam intactos**: não-FILE, budget, cancelamento sobem do reader
  sem tradução — o hasher não inventa semântica de falha.

**Verificar:** `src/wirs/infrastructure/hashing.py`, `tests/unit/test_hash.py` ·
**Issue:** #27 (fechada).

---

## #28 — JSON canônico: a fonte de verdade (WIRS-090)

### O que é o JSON canônico e por que ele vem antes das views

Terminal bonito, Markdown e HTML são *apresentação* — e apresentação muda toda
hora. Se cada formato lesse o modelo do seu jeito, qualquer mudança de layout
arriscaria mudar o *significado*. O `CanonicalReport` é a **fonte de verdade
serializada**: um JSON com contrato versionado do qual todas as views derivam
mecanicamente. Automação, comparação entre scans e re-análise falam com ele;
humanos falam com as views.

### Decisões de desenho

- **`schema_version` ≠ `scanner_version`**: o schema ("1.0") só muda com
  breaking change de campo; a versão do scanner muda a cada release. Sem isso,
  seria impossível saber se um JSON antigo ainda é legível — compatibilidade
  de relatório é promessa de produto, não detalhe.
- **Ordem determinística por construção**: findings por ID estável, coverage
  por capability. A ordem de chegada do pipeline (threads, OS, fases) *não*
  vaza para o relatório — provado com entradas embaralhadas gerando byte
  idêntico. Sem isso, `diff` entre scans seria ruído.
- **`generated_at` injetável**: o primeiro teste pegou um vazamento real —
  `now()` na construção fazia duas montagens "iguais" diferirem. Default
  prático, valor fixo nos testes e no golden. Determinismo é pré-requisito de
  reprodutibilidade, não estética.
- **Sem conteúdo bruto por estrutura**: os modelos nem têm campo para conteúdo
  de arquivo — a asserção do teste é rede de segurança, não a trava principal.
- **Golden revisado, nunca abençoado cego**: o fixture foi gerado, lido por
  humano e congelado; o teste compara byte-a-byte. Schema que evolui exige ler
  o diff e atualizar conscientemente — teste quebrar é o sistema funcionando.

**Verificar:** `src/wirs/reporting/canonical.py`,
`tests/unit/test_canonical.py`, `tests/golden/` · **Issue:** #28 (fechada).

---

## #29 — `wirs scan`: o primeiro comando que conta a verdade (WIRS-110)

### O que é o scan mínimo e por que ele sai com exit 3

Até aqui, cada peça foi testada isolada; o `wirs scan` é a primeira vez que
elas trabalham juntas: valida o target (`LocalDirectoryTarget`, inválido →
exit 2), roda o inventory de verdade, dobra os resultados num `CoverageEntry`
de filesystem, monta o `CanonicalReport` e imprime JSON ou terminal. E sai com
**exit 3** — pipeline incompleto por construção. Seria tentador retornar 0
("nenhum finding!"), mas sem detectores isso seria o falso negativo
institucionalizado: o relatório diz "Fase A" com todas as letras, e o exit
code concorda.

### Decisões de desenho

- **Gaps viram PARTIAL automaticamente**: cada `InventoryGap` conta como
  `failed` na entry — o teste com `scandir` sabotado prova a dobra
  inventory→coverage sem camada intermediária.
- **`findings` vazio, sem vergonha**: lista vazia com nota explícita, nunca
  omitida. Ausência de findings com coverage honesto é informação; sem
  coverage seria propaganda.
- **Budgets por perfil provisórios** (soft 64 MiB, balanced 256, fast 1 GiB):
  marcados como provisórios até a large-file policy (#034) — número chutado
  documentado vale mais que número mágico silencioso.
- **Terminal como view, não como segunda fonte**: a tabela Rich consome o
  mesmo `CanonicalReport` do JSON. Duas saídas, uma verdade.
- **`scan_id` único por execução** (`uuid4`): aqui determinismo seria bug —
  cada execução real é um evento distinto, diferente dos IDs de modelo.

**Verificar:** `src/wirs/cli/app.py`, `tests/integration/test_scan.py` ·
**Issue:** #29 (fechada).

---

## #30 — Discovery: provando que é WordPress sem acreditar em nome (WIRS-060)

### O que é o discovery e por que combinação de sinais, não nome de pasta

O FT-2 é o primeiro contato do motor genérico com o mundo real — e a primeira
pergunta é "isto é mesmo um WordPress?". Responder "tem `wp-content`, logo é"
seria o falso positivo inaugural do produto: qualquer backup, tema solto ou
diretório com nome famoso enganaria o scanner. O discovery exige **combinação
de sinais** (`wp-includes/version.php` como arquivo, `wp-admin/` e
`wp-content/` como diretórios, `wp-config.php` como arquivo): no mínimo 2 dos
4 precisam existir *com o tipo certo*. E tudo **sem banco e sem ler conteúdo
nenhum** — só `lstat`, que nunca segue symlink e nunca abre arquivo.

### Decisões de desenho

- **Limiar 2 de 4, pinado em teste**: 1 sinal nunca decide (o teste prova com
  `wp-content` solitário); 2 sinais disparam. O próprio TDD calibrou o limiar:
  meu caso inicial achava que `wp-content` + `wp-config.php` era "1 sinal",
  e o teste me corrigiu — são 2, e o limiar fez sentido exatamente ali.
- **Tipo importa, não só existência**: `wp-config.php` precisa ser *arquivo*,
  `wp-admin` precisa ser *diretório* — e symlink com nome famoso não conta
  (rejeitado no `lstat`). Nome sem tipo é fantasia.
- **Sem leitura de conteúdo**: descobrir não abre `version.php` — extrair
  versão com segurança é outra slice (WIRS-062, Fase D). Aqui, existir basta;
  interpretar vem depois.
- **Protocolo antes da implementação**: `PlatformAdapter` (runtime_checkable)
  + `PlatformDiscovery` moram em `ports/` — o contrato que Laravel, Joomla e
  PHP genérico vão implementar sem tocar no core. O teste asserta
  `isinstance(adapter, PlatformAdapter)`: conformidade executável, não
  documentada.
- **Versão fica `None` de propósito**: preencher versão agora seria ou
  executar PHP (proibido) ou ler arquivo no adapter (papel do reader). Ausência
  honesta até a slice certa.

**Verificar:** `src/wirs/ports/platform.py`,
`src/wirs/adapters/wordpress/discovery.py`,
`tests/unit/test_wordpress_discovery.py` · **Issue:** #30 (fechada).

---

## #31 — Zones: o mapa de expectativas do WordPress (WIRS-061)

### O que são as zonas e por que o mesmo arquivo significa coisas diferentes por lugar

Um `loader.php` em `mu-plugins/` (carregado automaticamente) e o mesmo nome
em `uploads/` (conteúdo que deveria ser inerte) são situações opostas — mas o
filesystem genérico vê dois arquivos iguais. As zonas resolvem isso: dividem
o WordPress em 9 regiões, cada uma com sua **expectativa** (core protegido
espera igualdade com upstream; uploads espera não-executável; cache espera
churn). Regras futuras não perguntam "o que é este arquivo?" no vazio —
perguntam "o que significa este arquivo *nesta zona*?".

### Decisões de desenho

- **Função pura sobre path relativo**: `classify("a/b") -> Zona`, sem I/O,
  sem banco, sem estado. Testável por tabela, reusável por qualquer pipeline —
  inclusive futuros adapters com suas próprias zonas.
- **Raiz em três destinos**: arquivo oficial (lista estável do core:
  `index.php`, `wp-login.php`, `xmlrpc.php`...) → protegido (comparável com
  upstream); config visível (`wp-config.php`, `.htaccess`...) → especial
  (política/heurística, nunca igualdade); desconhecido (`backup.zip`) →
  especial também, porque raiz é área sensível e merece atenção, não
  silêncio.
- **Desconhecido tem endereço, não limbo**: `wp-content/custom/x` e o próprio
  `wp-content` viram `OTHER`; fora de `wp-content`, desconhecido aninhado vira
  `OTHER`. Toda entrada classifica em algo — "não sei onde pôr" não existe.
- **MU-plugin é zona, não veredito**: classificar como `MU_PLUGINS` apenas
  posiciona; dizer se é malicioso é trabalho de regra futura com evidência.
  A zona informa, nunca condena — coerente com "sem baseline não é malicioso".
- **Sem dobra de caixa**: `wp-admin` casa o diretório e os filhos pela mesma
  regra de prefixo. Maiúsculas não são dobradas (Linux é case-sensitive;
  preservar é o comportamento honesto).

**Verificar:** `src/wirs/adapters/wordpress/zones.py`,
`tests/unit/test_wordpress_zones.py` · **Issue:** #31 (fechada).

---

## #32 — Doctor: perguntando ao ambiente antes de prometer (WIRS-063)

### O que é o doctor e por que disponibilidade é dado, não exceção

Todo provider futuro (WP-CLI, YARA, Wordfence) pode faltar — e o ADR-010 manda
degradar coverage, nunca abortar. Mas para degradar com precisão, o scanner
precisa *saber* o que existe: path, versão, tempo de resposta. O `WpCliDoctor`
transforma "será que tem wp?" num `WpCliStatus` estruturado (available, path,
version, duration, error) — nunca texto solto, nunca exceção para caso
esperado. Ausência vira dado que o coverage consome; só o inesperado vira erro.

### Decisões de desenho

- **Só comando pré-load**: `wp --version` não inicializa plugins/themes, logo
  é seguro no `safe_only` (ADR-009). O teste asserta o argv exato —
  `["wp", "--version"]` — travando qualquer tentativa futura de usar um
  comando com bootstrap aqui.
- **Comando explícito não passa no `which`**: quem passa o caminho assume a
  existência (útil em testes e installs fora do PATH). O TDD pegou o desenho
  inicial errado, que fazia lookup sempre e quebrava o caso explícito.
- **Runner injetável, fakes como subclasses**: ausência/timeout/falha usam
  `FakeRunner(CommandRunner)` — tipado, sem mocks mágicos — e um teste com o
  runner real prova o timeout matando um sleep de 30s em 0,5s.
- **CommandRunner mínimo agora, endurecido depois**: argv-sequência,
  `shell=False`, timeout com kill, cap de output e decode tolerante. A
  allowlist do guarda da #18 já previa exatamente este endereço
  (`infrastructure/command_runner.py`); sanitização de env e cwd explícito
  chegam na WIRS-122 sem mudar a interface. O S603 do linter foi silenciado
  com `noqa` justificado — o único call site autorizado do repositório.
- **Versão via regex tolerante** (`WP-CLI x.y[.z]`): sem versão parseável,
  `available=True` com `version=None` — resposta parcial honesta em vez de
  falha inventada.

**Verificar:** `src/wirs/infrastructure/command_runner.py`,
`src/wirs/providers/wpcli.py`, `tests/unit/test_wpcli_doctor.py` ·
**Issue:** #32 (fechada).

---

## #33 — Checksums: perguntando ao WordPress.org sem acreditar cego (WIRS-064)

### O que é o provider e por que ele traduz em vez de repassar

O WP-CLI já sabe verificar o core contra os checksums oficiais — reinventar
isso seria vaidade. O trabalho do WIRS é outro: **executar com segurança,
normalizar a saída para o modelo interno e registrar provenance**. O
`verify_core_checksum` roda `verify-checksums --include-root --format=json
--path=<alvo>`, traduz a lista `[{file, message}]` para `FileIntegrity`
(MATCH/MISMATCH/MISSING/UNEXPECTED) e devolve um `CoreChecksumReport` com
provider, versão e sucesso. A aplicação nunca vê o formato do vendor — essa é
a anti-corruption layer funcionando: se o WP-CLI mudar o JSON amanhã, quebra
um parser isolado, não o motor.

### Decisões de desenho

- **Contrato lido da doc oficial, não da memória**: a página do comando
  confirmou hook `before_wp_load`, download de md5 por versão+locale e o
  formato da lista — e o contrato ficou registrado em
  `docs/providers/wp-cli.md` (exigência da DoD de provider). O que a doc não
  dizia (stdout vazio no sucesso), foi tratado defensivamente.
- **Exit != 0 é sinal, não erro**: o WP-CLI sai diferente de zero quando algo
  diverge — com JSON parseável, o report sai normal. Só vira
  `ProviderExecutionError` quando não há stdout aproveitável. Confundir
  "encontrou divergência" com "ferramenta quebrou" seria o erro clássico aqui.
- **Mensagem desconhecida = `ProviderInvalidOutput`, nunca chute**: classificar
  um aviso novo como benigno seria o falso negativo silencioso; recusar alto
  força atualização explícita do parser + coverage degradado. Segurança antes
  de conveniência.
- **Hierarquia de erros do spec virou código**: `ProviderUnavailable`,
  `ProviderTimeout`, `ProviderInvalidOutput`, `ProviderExecutionError` —
  cada falha tem nome, e cada nome vira Coverage em vez de abortar o scan.
- **Doctor injetável**: o provider recebe o doctor pronto (o teste injeta o
  fake), em vez de criá-lo escondido — sem isso, o fake do teste nunca seria
  consultado e o teste mentiria. O TDD pegou as duas armadilhas (lookup
  incondicional e chamada errada no fake).
- **Integração real quando existir**: o teste de integração pula sem `wp` ou
  fixture — skip explícito documentado, não cobertura fingida.

**Verificar:** `src/wirs/providers/wp_checksum.py`,
`src/wirs/domain/integrity.py`, `tests/unit/test_core_checksum.py`,
`tests/integration/test_wpcli_core.py`, `docs/providers/wp-cli.md` ·
**Issue:** #33 (fechada).

---

## #34 — Plugins: o mesmo molde, um problema novo (UNVERIFIED) (WIRS-065)

### O que é o provider de plugins e por que reaproveitar foi o teste real

Verificar plugins é "igual ao core, mas por componente e com `--strict`".
O valor desta slice não está no comando novo — está em **provar que a
arquitetura anti-corruption funciona duas vezes**: a aplicação continua sem
conhecer nenhum formato WP-CLI, porque o segundo provider reutiliza o mesmo
executor, a mesma hierarquia de erros e o mesmo mapa de mensagens do core. Se
a #33 tivesse vazado detalhe de vendor para a aplicação, a #34 doeria — não
doeu: o trabalho foi só o formato por plugin + o caso novo.

### Decisões de desenho

- **Contrato assumido às claras**: a doc oficial não mostra o JSON de plugins,
  então definimos `[{plugin, file?, message}]` (core + slug) e registramos
  como ASSUMIDO em `docs/providers/wp-cli.md`, com integração real pendente.
  Assunção documentada + parser estrito > adivinhação silenciosa.
- **Sem baseline = UNVERIFIED, nunca failure**: plugin fora do WordPress.org
  (premium/custom) cai em `unverified_plugins` via mensagens de skip
  tabeladas — visível no coverage, jamais confundido com erro de provider.
  É a invariante 7 ("sem baseline não é malicioso") atravessando a fronteira
  do vendor.
- **Shape do core é rejeitado aqui**: entrada sem `plugin` vira
  `ProviderInvalidOutput` — cada comando tem seu contrato, e misturá-los
  seria corrupção de camada.
- **Executor extraído, não duplicado**: `_execute_verify` + `_stdout_or_raise`
  servem core e plugins; a refatoração rodou com os testes da #33 verdes o
  tempo todo (Regra de Ouro: nada de refactor em RED).
- **Coverage por componente**: o report agrupa por slug (`PluginResult` com
  `success` próprio) — o orquestrador futuro monta uma entry por plugin sem
  precisar reparsear nada.

**Verificar:** `src/wirs/providers/wp_checksum.py`,
`tests/unit/test_plugin_checksum.py`,
`tests/integration/test_wpcli_plugins.py` · **Issue:** #34 (fechada).

---

## #35 — Uploads: onde PHP é notícia, não paisagem (WIRS-068)

### O que é a policy e por que ela separa "parece executável" de "é proibido aqui"

PHP dentro de `wp-content/plugins` é paisagem; o mesmo PHP dentro de
`wp-content/uploads` é notícia — a zona de uploads deveria conter mídia
inerte. A policy codifica exatamente essa distinção em duas metades
independentes (o Exercício 7 do spec): `looks_executable` responde "este
conteúdo parece executável?" (genérico, sem saber o que é WordPress) e
`check_uploads_executable` responde "e nesta zona, isso pode?" (só dispara em
`UPLOADS`). Separadas, as metades são reusáveis — o detector serve ao futuro
adapter Laravel, a policy serve a futuras zonas.

### Decisões de desenho

- **Conteúdo, não extensão**: `evil.php` acusa pelo `<?php`, mas `foto.jpg`
  com magic JPEG passa e — detalhe que salva SVGs legítimos — `<?xml` não é
  PHP. Extensão é alegação do invasor; conteúdo é evidência.
- **HIGH/HIGH, nunca "malware"**: severidade alta (forte violação de
  expectativa, spec Q17) com confiança HIGH — não DETERMINISTIC, porque zona
  é convenção, não baseline oficial. O finding informa prioridade de análise,
  não veredito.
- **Allowlist do operador com `fnmatch`**: exceções legítimas (plugin que
  grava PHP em uploads) entram como padrões de config — stdlib, sem DSL
  própria antes da hora.
- **Evidence exigida, não fabricada**: a função recebe `evidence_refs` como
  parâmetro obrigatório — a policy não inventa proveniência; o pipeline
  futuro fornece.
- **Fixtures inertes dos dois lados**: `evil.php` (positivo, sem backend
  funcional), `foto.jpg` binário real e plugin legítimo (negativos) vivem em
  `tests/fixtures/wordpress/uploads_php/` — positivo sem os dois negativos
  seria teste pela metade.

**Verificar:** `src/wirs/detectors/executable.py`,
`src/wirs/adapters/wordpress/policies.py`,
`tests/unit/test_upload_policy.py`,
`tests/fixtures/wordpress/uploads_php/` · **Issue:** #35 (fechada).

---

## #36 — IOC: o vocabulário dos sinais conhecidos (WIRS-050)

### O que é o IOC e por que tipo validado, não string solta

"Procurar `eval(` nos arquivos" parece trivial até o dia em que um IOC
malformado (SHA com 63 chars, domain com espaço) gera falso negativo
silencioso ou quebra o scanner no meio. O `IOC` amarra **tipo + valor
validados**: 5 kinds (literal, domain, URL fragment, path fragment, SHA-256),
cada um com sua regra — SHA exige 64 hex, domain exige charset válido e é
normalizado para minúsculo, literal não pode ser vazio. IOC inválido nem
nasce: `ValueError` na construção, nunca no meio do scan.

### Decisões de desenho

- **Normalizar em vez de só validar**: domain vai para minúsculo (DNS não
  distingue caixa), SHA maiúsculo desce — o mesmo indicador escrito de dois
  jeitos é o mesmo IOC, com o mesmo ID.
- **ID sem o `label`**: a nota humana ("webshell X") viaja junto mas não
  compõe a identidade — renomear a nota não duplica o indicador.
- **Round-trip total**: o schema é a ponte entre o arquivo `iocs.txt` do
  operador (futuro) e o scanner em streaming da #37.

**Verificar:** `src/wirs/domain/ioc.py`, `tests/unit/test_ioc.py` ·
**Issue:** #36 (fechada).

---

## #37 — Scanner literal: bytes, fronteira e a quarentena que ensinou (WIRS-051)

### O que é o scanner e por que bytes, nunca texto

Procurar um IOC num arquivo parece `grep`, mas `grep` lê texto — e alvo
hostil tem binário, UTF-8 inválido e IOC partido no meio do buffer de
leitura. O `scan_stream` opera **só em bytes**: recebe chunks (os mesmos do
reader), carrega overlap de `max_len - 1` entre eles e acha o IOC mesmo
cruzando a fronteira, com offset absoluto no stream. Cada match leva um
contexto limitado (64 bytes por lado) em bytes crus — sem decodificar, sem
inventar.

### Decisões de desenho

- **Regra do carry provada por contagem**: match com fim dentro do carry já
  foi reportado; com fim além, é novo (cruzou a fronteira). Os testes pinam
  offsets absolutos e o caso "um por chunk, nenhum cruzado" — fronteira sem
  duplicar nem perder.
- **Cap que preserva o count**: acima de 100 ocorrências por IOC, para de
  guardar mas continua contando (`total_counts` exato + `truncated=True`).
  Milhares de ocorrências não explodem o relatório (spec T042) e ninguém perde
  a magnitude.
- **SHA256 ignorado aqui, por desenho**: hash se compara via HashService no
  orquestrador, não por busca literal — o scanner pula a kind sem erro.
  Cada ferramenta no seu quadrado.
- **Domain casa-insensitivo, resto exato**: DNS não distingue caixa; literal
  de código, sim. A distinção mora no kind do IOC (#36), não em flag do
  scanner.
- **A quarentena do Defender**: o Windows Defender **apagou** a primeira
  versão do teste por conter assinatura viva contígua. Virou regra registrada
  no SECURITY.md: literais perigosos sempre fragmentados com `+` explícito
  (o `ruff format` juntaria concatenação implícita de volta!) e comentário
  `NOTA ANTI-AV`. Amostra que o AV come é teste que "passa" sem existir.

**Verificar:** `src/wirs/detectors/ioc_scanner.py`,
`tests/unit/test_ioc_scanner.py` · **Issue:** #37 (fechada).

---

## #39 — Heurísticas: sinal fraco sozinho, cadeia explícita combinada (WIRS-055)

### O que são as heurísticas e por que isolado nunca é critical

`eval(` sozinho aparece em código legítimo; `base64_decode(` sozinho também.
O erro clássico dos scanners é transformar coincidência em veredito. O
`analyze_php` trabalha em dois tempos: primeiro coleta **famílias de sinais**
(execução dinâmica, encoding, processo, arquivo/rede, função dinâmica,
literal encoded) sobre bytes crus; depois aplica uma **tabela de combinação
explícita** — e só ela decide. Isolado fraco: silêncio ou LOW. Encoding +
execução: HIGH. Três famílias: HIGH. E **nunca CRITICAL**: heurística não tem
patente de certeza; o teto é HIGH por desenho, com teste travando isso.

### Decisões de desenho

- **Um finding no máximo (o tier mais alto)**: sem duplicar por família. O
  relatório recebe a conclusão, e os sinais vão em `attributes` para auditoria.
- **Regex em bytes, case-insensitive, sem decode**: mesmo arquivo binário não
  quebra a análise — e minificação JS legítima passa ilesa (sem tokens PHP,
  sem finding).
- **Backticks contam**: o operador de shell do PHP (`` `...` ``) é execução
  disfarçada de pontuação — entra como função dinâmica.
- **Fixtures sem `eval`**: a cadeia positiva usa `assert(+base64+gzinflate` —
  exercita encoding+execução sem o token que provoca o antivírus. A regra
  anti-AV da #37 vale para fixtures também; os 4 arquivos foram verificados
  legíveis após escrita.
- **Negativos em maioria**: base64 isolado, plugin limpo e JS minificado —
  positivo sem negativos seria teste pela metade (padrão firmado na #35).

**Verificar:** `src/wirs/detectors/php_heuristics.py`,
`tests/unit/test_php_heuristics.py`,
`tests/fixtures/wordpress/heuristics/` · **Issue:** #39 (fechada).

---

## #41 — Redaction: o segredo morre na fronteira, não na vitrine (WIRS-092)

### O que é o redaction e por que fronteira, não renderer

Relatório de incidente vaza por dois caminhos: o operador cola o JSON num
ticket, e o ticket vaza — levando `DB_PASSWORD`, salts e API keys junto. A
resposta comum ("mascaramos na UI") é teatro: o dado cru continua no JSON, no
log, no debug. O redactor do WIRS roda **na fronteira de coleta**: o conteúdo
é limpo *antes* de virar Evidence, então o segredo simplesmente não existe
abaixo dali — nem no JSON, nem no terminal, nem no HTML futuro. `redact_text`
para strings, `redact_mapping` recursivo para estruturas (str, bytes, dicts,
listas), e `STORE_RAW_CONTENT = False` como default explícito que a config
futura vai ligar.

### Decisões de desenho

- **Padrões conservadores, com nome por perto**: DB_PASSWORD com moldura
  preservada, bloco PRIVATE KEY multilinha, atribuições
  password/secret/api_key/token, AKIA, Bearer. Todos exigem o *nome* da chave
  — por isso hash SHA, `art_abc` e `6.5.2` passam intactos (testado lado a
  lado com o segredo). Precisão antes de cobertura: redigir um hash legítimo
  destruiria evidência.
- **A chave do mapping também é sinal**: `{"pwd": "s3nha"}` — o valor sozinho
  não casa nenhum padrão de texto. O TDD pegou: `redact_mapping` redige o
  valor inteiro quando o *nome* do campo é de secret. Dado estruturado se lê
  pela chave, não pelo valor.
- **Bytes via decode/re-encode**: valores binários são decodificados
  (tolerante), redigidos e re-codificados — sem corromper, sem exceção.
- **Fake com `noqa` justificado**: o S105 acusou a senha fake do teste; `noqa`
  com motivo, como manda o manual do bandit para fixtures.
- **Teste adversário dedicado** (`tests/security/`): aspas/case variados,
  chave quebrada em linhas, segredo colado em legítimo — o segredo não
  sobrevive em nenhuma forma, e o legítimo sobrevive ao lado.

**Verificar:** `src/wirs/reporting/redaction.py`,
`tests/unit/test_redaction.py`, `tests/security/test_secret_leakage.py` ·
**Issue:** #41 (fechada).

---

## #40 — Terminal: a vitrine que não confia na mercadoria (WIRS-091)

### O que é o reporter e por que a view é o lugar mais atacado

JSON é para máquina; humano lê terminal — e terminal é código executando
strings do invasor. Nome de arquivo com escape ANSI reprograma o emulador,
`[bold]` no título vira formatação real no Rich, `\n` no path quebra a tabela
e esconde linha. O `render_report` trata **todo conteúdo do alvo como
hostil**: ANSI removido, markup escapado (aparece como texto), controles
trocados por `?`. A regra de ouro da UX de segurança aqui: a formatação é
nossa, os dados são deles, e os dois nunca se misturam.

### Decisões de desenho

- **Cor nunca sozinha**: cada severidade tem cor + nome em texto
  (`CRITICAL`, `HIGH`...) — daltônico, terminal sem cor ou log redirecionado
  perdem zero informação. Summary mostra os 5 níveis mesmo zerados: ausência
  visível também é dado.
- **Finding card com refs**: regra, título, categoria, confiança em texto,
  artifact e evidence refs — o cartão responde "o quê, onde, com que prova"
  sem precisar abrir o JSON.
- **Coverage tão visível quanto findings**: mesma hierarquia de tabela, no
  mesmo render. Cobertura escondida no rodapé seria repetir o pecado que o
  produto nasceu para matar.
- **`sanitize` exportado e testado**: a função é pública para os futuros
  renderers Markdown/HTML reutilizarem a mesma política — sanitizar uma vez,
  em um lugar.
- **CLI delega, não duplica**: o `_print_terminal` do scan virou inventory
  (específico) + `render_report` (geral). A refatoração rodou em GREEN com a
  suite intacta — e a prova E2E no fixture confirma as três tabelas.

**Verificar:** `src/wirs/reporting/terminal.py`,
`tests/unit/test_terminal.py` · **Issue:** #40 (fechada).

---

## #38 — Hints: um passo de leitura, N respostas (WIRS-054)

### O que são os hints e por que o passo único importa

Ler disco é a operação mais cara do scanner — cada byte lido duas vezes é
tempo e I/O jogados fora, crítico em hospedagem compartilhada. Os hints
resolvem isso na raiz: **um passo sobre os bytes serve N respostas**.
`extract_hints` recebe o head do arquivo uma vez e devolve `is_text` +
`executable` juntos. Quando o scheduler (futuro) plugar essa função no stream
compartilhado do reader, hash, IOC, heurísticas e hints beberão da mesma
leitura sem que nenhum detector precise saber dos outros.

### Decisões de desenho

- **Reuso por delegação, provado por contrato**: `executable` chama
  `looks_executable` da #35 — e o teste asserta acordo amostra a amostra, não
  a implementação. Se alguém duplicar a lógica, o contrato continua valendo;
  se mudarem o detector, os hints acompanham sem edição.
- **Texto = sem NUL e UTF-8 válido**: NUL denuncia binário mesmo quando o
  resto decodifica (UTF-8 aceita `\x00`); latin-1 e sequências inválidas caem
  para binário. Vazio conta como texto — nada há de binário nele.
- **Assinatura final antes do scheduler**: bytes entram, hints imutáveis
  saem. O orquestrador futuro só conecta; nada aqui será reassinado.
- **Sem dobra com mismatch extensão/conteúdo**: essa comparação (WIRS-015) é
  outra slice — hints expõem os fatos, regras julgam.

**Verificar:** `src/wirs/detectors/content.py`,
`tests/unit/test_content_hints.py` · **Issue:** #38 (fechada).

---

## #42 — Orquestrador: quem manda no scan sem conhecer ferramenta (WIRS-116)

### O que é o orquestrador e por que o scan era um script linear

Até aqui, o `wirs scan` fazia tudo inline: lia, contava, montava coverage.
Funcionava, mas cada capacidade nova (detector, provider) teria que ser
costurada no CLI — e o CLI passaria a conhecer filesystem, adapters e regras,
virando o acoplamento que a arquitetura proíbe. O `run_scan` inverte isso: o
**pipeline mora em `application/` e só conhece `domain` + `ports`**.
Implementações concretas (filesystem, adapters WordPress) entram por
parâmetro, montadas no CLI como composition root. O CLI voltou a ser magro:
valida, delega, renderiza.

### Decisões de desenho

- **Dependência só para dentro, verificada por teste**: o guarda de arquitetura
  ganhou um irmão que varre `application/` e só aceita `domain` + `ports`
  (+ stdlib). Se alguém importar infrastructure no orquestrador, o build quebra.
- **Fonte e adapters injetados, nunca importados**: `run_scan(target,
  profile, source, adapters)` — sem defaults concretos (default seria importar
  infra no módulo e furar o guarda). Fake source e adapter vazio nos testes
  provam a seam sem filesystem.
- **`classify` virou parte do protocolo**: `PlatformAdapter` ganhou o método
  de zona (string no vocabulário do adapter), e o `WordPressAdapter` o
  implementa delegando ao classifier da #31. Zones deixaram de ser função
  solta e viraram capability de plataforma — Laravel fará o mesmo sem tocar
  no orquestrador.
- **ScanResult congela a passada**: artifacts, gaps, discovery, zones por ID,
  coverage e findings (vazios até a #43). Entre CLI e relatório não trafega
  mais lógica, só esse objeto.
- **Corrigido de passagem**: o `classify` do adapter tinha entrado sem o
  import (sobra de um turno ambíguo) — o teste novo quebrou na hora, como deve
  ser, e a correção foi trivial porque a seam já existia.

**Verificar:** `src/wirs/application/orchestrator.py`,
`src/wirs/ports/source.py`, `tests/integration/test_orchestrator.py` ·
**Issue:** #42 (fechada).

---

## #43 — Ligando o produto: detectores e providers viram findings (WIRS-117)

### O que é a detecção orquestrada e por que ela é uma seam, não uma lista

Peças testadas não fazem produto: até aqui, IOC, policy, heurísticas e
checksums existiam isolados e o scan não usava nenhum. A #43 liga tudo através
de **duas seams em `ports/`** — `Detector` (internos: propõe findings sem
evidence, orquestrador cunha e anexa a ref) e `IntegrityProvider` (externos:
verifica por componente, orquestrador converte em findings + coverage). O
orquestrador continua sem importar nada além de `domain` + `ports`: leitores,
policies, heurísticas e WP-CLI entram por parâmetro, montados no CLI. E o
`--fail-on` fecha o contrato operacional: exit 1 quando há finding na
severidade pedida, 0 abaixo — CI consegue travar deploy em `HIGH+`.

### Decisões de desenho

- **Proposta sem ref, finding com ref**: o detector devolve `ProposedFinding`
  (sem `evidence_refs`); o orquestrador cunha a Evidence (com redaction nos
  contextos!) e anexa. Isso exigiu mudar `analyze_php` para devolver propostas
  — refactor guiado pela invariante 2, com os testes da #39 verdes o tempo
  todo. Invariante que quebra refactor revela onde o desenho estava devendo.
- **IOCs viajam dentro do detector**: `IocDetector([iocs])` em vez de parâmetro
  solto no `run_scan` — a lista de indicadores é configuração do detector,
  não do pipeline. CLI ainda sem flag `--ioc` (config file é WIRS-111).
- **Checksum degradando de verdade**: sem `wp` neste host, o scan real mostra
  `wp-cli-core-checksum: unavailable` e continua — ADR-010 exercido de ponta
  a ponta, não só em teste fake. Quando roda, MISMATCH→CRITICAL com
  provenance do provider (o escape explícito da invariante, feito para isso).
- **Redaction mora no domain agora**: `application` não podia importar de
  `reporting` (camada errada), então o primitivo mudou para
  `wirs.domain.redaction` com re-export compatível. Segurança como vocabulário
  do domínio, não detalhe de view.
- **Agregação por (artifact, IOC)**: um finding por indicador por arquivo, com
  count e offsets — 250 matches não viram 250 findings.
- **Generators no protocolo**: `iter_chunks` tipado como `Generator` (não
  `Iterator`) para fechar handle em leitura parcial sem `contextlib` — vazamento
  de FD em scan de 100 mil arquivos seria o bug silencioso do ano.

**Verificar:** `src/wirs/application/orchestrator.py`,
`src/wirs/ports/detection.py`, `src/wirs/ports/checksum.py`,
`src/wirs/ports/reader.py`, `src/wirs/domain/redaction.py`,
`tests/integration/test_orchestrator.py` · **Issue:** #43 (aberta).
