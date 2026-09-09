# Jornada do FT-1: do zero ao primeiro scan honesto

Este documento conta, slice por slice, como o núcleo seguro do WIRS foi
construído — e *por que* cada peça existe. É leitura para quem chega agora
(analista, curioso ou contribuidor) entender o sistema sem precisar ler o
código inteiro de uma vez. Cada seção termina com onde verificar: a Issue tem
o aceite formal, os arquivos têm a prova executável.

O FT-1 ("core seguro") é o primeiro fast-track do spec: inventory +
JSON + coverage. Ao final dele, o scanner ainda não detecta nada — mas já
sabe olhar para um diretório com segurança, modelar o que viu e dizer com
honestidade o que *não* viu. Detecção vem depois; fundação falsa não se
conserta depois.

> Este documento cresce junto com o projeto: toda slice nova ganha sua seção
> aqui antes de ser dada como concluída.

## #17 — Scaffold: o terreno antes da casa (WIRS-001)

Antes de qualquer detector, precisávamos de um repositório que compila, testa,
lint, tipa e publica no CI — Python `>=3.11` (roda em VPS moderno sem exigir o
bleeding edge), CLI com Typer, terminal com Rich, `pytest` + Hypothesis +
Ruff + `mypy strict`, CI na matrix 3.11–3.14. O `wirs scan` nasceu como
esqueleto honesto: valida o target (inválido → exit 2) e declara
"engine em construção" com coverage explícito (exit 3) em vez de fingir
resultado. Verificação: `uv run pytest`, `ruff check`, `mypy src/`, `wirs --help`.

## #18 — Fronteiras que o compilador não vê (WIRS-002)

Python não tem visibilidade de pacote como Java — nada impede `domain/`
importar `wordpress` ou um detector chamar `subprocess`. Como as invariantes
arquiteturais são o coração do produto, elas viraram **testes que varrem
imports via AST**: domain só-stdlib, detectors sem subprocess, subprocess só
via `CommandRunner`. E teste de guarda só vale se provado: cada um foi
verificado por mutação (violo de propósito → quebra → reverto). Verificação:
`tests/unit/test_architecture.py`.

## #19 — Target: onde é permitido olhar (WIRS-010)

Todo scan começa respondendo "o quê, exatamente, estou analisando?". O
`Target` congela essa resposta: root normalizado (resolve, sem trailing),
ID determinístico (`tgt_<sha256:16>` — dois scans do mesmo alvo geram o mesmo
ID, base para comparar relatórios no tempo), metadata imutável
(`MappingProxyType`, não dict). Raiz inexistente ou arquivo-como-root vira
`TargetError` — alvo inválido nunca produz "scan vazio válido", que seria o
falso negativo mais perigoso do produto. Verificação:
`tests/unit/test_target.py`.

## #20 — SafePath: o único lugar onde path sujo vira path confiável (WIRS-011)

Caminhos vêm do alvo hostil: `../../etc/cron.d/x` para escapar, `<script>` e
ANSI para atacar relatório, `C:\...` e `\\server\...` para explorar o Windows.
O `SafePath` confina lexicalmente (sem tocar o filesystem): `..` que escapa,
absoluto, drive e UNC viram `SecurityBoundaryError`; `\` sempre vira `/`
(código único Win/Linux); NUL é rejeitado em voz alta; Unicode vai para NFC.
O property test com Hypothesis caçou um bug real: no Windows,
`joinpath('::')` **descartava o root inteiro** — o `full` passou a ser
construído por concatenação em parse único e ancorado. Escape via symlink fica
para o inventory (nunca follow). Verificação:
`tests/unit/test_safepath.py`.

## #21 — Artifact: a unidade que atravessa o pipeline (WIRS-012)

Se Target diz *onde* e SafePath diz *como nomear*, Artifact diz *o quê* é
analisável. Um tipo congelado com 4 kinds (`FILE/DIR/SYMLINK/SPECIAL`, enum em
vez de subclasses para serialização trivial), ID estável que inclui o kind
(path que vira symlink é outro artifact), metadata honesta sobre ausência
(`None` em vez de zero inventado) e destino de symlink como *dado*, nunca
seguido. O `from_stat` é puro — recebe o `stat` já coletado e só mapeia —,
porque quem toca disco é o inventory; o modelo interpreta. Round-trip total
prepara o JSON canônico. Verificação: `tests/unit/test_artifact.py`.

## #22 — Inventory: a fronteira onde o scanner toca o disco (WIRS-013)

Primeiro código que lê o alvo — por isso concentra todas as decisões de
leitura segura num lugar só: gerador com pilha explícita (memória bounded,
ordem determinística por diretório), `scandir` + `lstat` sem follow (loops
impossíveis por construção), symlink registrado com destino de `readlink`,
special nunca aberto (o teste do FIFO *travaria para sempre* se tentássemos
abrir), erro por entrada vira `InventoryGap` (scan continua) e só root
ilegível vira `TargetError`. Gaps alimentam o Coverage; hidden files entram por
padrão. Symlink/FIFO pulam neste Windows sem privilégio e rodam no CI Linux —
skip explícito em vez de cobertura fingida. Verificação:
`tests/integration/test_inventory.py`.

## #23 — Evidence: a moeda da explicabilidade (WIRS-020)

Princípio P2, "evidência antes de interpretação": a `Evidence` é a observação
imutável que sustenta qualquer afirmação futura. ID determinístico
(`ev_<sha256:16>` de scan+kind+artifact+conteúdo, sem timestamp — a mesma
observação deduplica entre scans), `kind` aberto (vocabulário virá das regras),
`Provenance` obrigatória sem default (sem proveniência, nem instancia),
`content` restrito a JSON-serializável na construção (fundação do dado
canônico) e `RedactionState` explícito (`none`/`redacted`) para distinguir
"não havia secret" de "houve e foi redigido". Referência ao artifact por ID
string: sem import circular, serialização trivial, pronto para o evidence
graph. Verificação: `tests/unit/test_evidence.py`.

## #24 — Finding: a linha entre fato e chute (WIRS-021)

Evidências ninguém lê em volume; findings dizem o que elas *significam* — com
**severidade e confiança independentes** (um `CRITICAL+DETERMINISTIC` e um
`CRITICAL+LOW` coexistem no relatório sem se confundir). A invariante 2 virou
exceção: sem `evidence_refs` e sem `provenance` de provider, o construtor
recusa — finding órfão é impossível por construção. Confiança em duas partes
(classe honesta + score 0–1 validado, que complementa sem fingir precisão).
O ID deriva de regra+artifact+evidências+atributos — *não* de severidade:
reclassificar não muda a identidade, e a ordem das evidências também não
(refs ordenadas no hash). Verificação: `tests/unit/test_finding.py`.

## #25 — Coverage: o antídoto contra o "está limpo" (WIRS-023)

O falso negativo silencioso é o bug mais caro do produto — e o Coverage existe
para torná-lo visível e tipado: 6 estados + a contabilidade exata de cada
check aplicável. O invariante (`verified+failed+skipped+unavailable` iguala
`applicable_checks`) é exceção no construtor, e estado e contadores são
amarrados: `COMPLETE` exige tudo verificado, YARA com 10 indisponíveis **não
compila** como `COMPLETE` (só `PARTIAL`/`UNAVAILABLE`), `FAILED` descreve o
estrago sem inventar precisão. Só o tijolo validado — o relatório consolidado
pertence ao futuro `ReportService`. Verificação:
`tests/unit/test_coverage.py`.

## #26 — ArtifactReader: o gargalo obrigatório (WIRS-030)

Hash, IOC e heurísticas precisam ler arquivos — e se cada detector abrisse por
conta própria, teríamos N leituras, N políticas de limite e N chances de abrir
a coisa errada. O reader é o **único caminho para conteúdo**: sempre `rb`
(decoding é decisão do detector), streaming em chunks, `ReadBudget` validado,
`BudgetExceeded` com `bytes_read` (arquivo no-limite-exato não é erro),
cancelamento cooperativo sem threads, e recusa de não-`FILE` *antes* de tocar
o disco (abrir symlink seguiria o destino). Erros novos na família `WirsError`:
recuperáveis, feitos para virar Coverage. Verificação:
`tests/unit/test_reader.py`.

## #27 — HashService: ler uma vez, servir N detectores (WIRS-031)

Com o reader pronto, o hash centraliza a identidade de conteúdo: **uma
instância por scan, dona do cache** — o memo morre com o scan, então vazamento
entre scans (um falso `VERIFIED` catastrófico) é impossível por construção.
Chave `(artifact.id, algorithm)`: SHA-256 interno, MD5 só como compatibilidade
upstream (o linter acusou S324 e a resposta documenta `usedforsecurity=False`).
Prova de leitura única via spy que delega ao comportamento real — testa o
comportamento, não um mock. Erros do reader propagam intactos: a decisão do
que fazer com falha de leitura é do orquestrador, não do hasher. Verificação:
`tests/unit/test_hash.py`.

## #28 — JSON canônico: a fonte de verdade (WIRS-090)

Terminal, Markdown e HTML são *views*; o JSON é o contrato. O
`CanonicalReport` separa `schema_version` ("1.0", muda só com breaking change)
de `scanner_version` (0.0.1, muda a cada release), ordena findings por ID e
coverage por capability (ordem de chegada não altera a saída — o teste provou
com entradas embaralhadas), e nunca carrega conteúdo bruto (os modelos nem
têm onde guardar). O `generated_at` injetável existe porque o primeiro teste
pegou um vazamento de determinismo: `now()` por construção tornava duas
montagens diferentes. O golden
(`tests/golden/canonical_report_v1.json`) foi revisado manualmente: qualquer
mudança no output exige revisão explícita do diff, nunca overwrite cego.
Verificação: `tests/unit/test_canonical.py` +
`tests/golden/test_canonical_json.py`.
