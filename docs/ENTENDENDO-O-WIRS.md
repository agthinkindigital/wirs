# Entendendo o WIRS: o que procurar num site comprometido (e por quê)

Este documento ensina **segurança na prática**: que problemas moram nos
arquivos de um site, como reconhecê-los e por que o scanner foi desenhado do
jeito que foi para encontrá-los. Cada seção nasce de uma entrega real do
projeto (o número `#NN` é a Issue que a implementou), e explica três coisas:
**o que** o scan busca, **como** ele busca e **por que** foi desenhado assim.

Não é manual de código nem de arquitetura — para isso, veja
[`ARCHITECTURE.md`](ARCHITECTURE.md). Aqui o assunto é o **seu site**:
onde o invasor se esconde, o que é evidência de verdade e como ler um
relatório sem cair em falso positivo nem em falso "está limpo".

> Novas entregas de detecção ganham sua seção aqui. Mecânica interna
> (tooling, plumbing de CLI, detalhes de implementação) mora no código e nos
> ADRs, não neste documento.

---

## #19 — Alvo: delimitar antes de acusar

### O que o scan busca

Antes de procurar qualquer ameaça, o scanner congela a pergunta "o quê,
exatamente, estou analisando?" — um diretório, um snapshot, um archive. Parece
burocracia, mas é a primeira lição de incident response: **relatório limpo
sobre o alvo errado (ou sobre nada) é o falso negativo mais perigoso que
existe**. Alvo inexistente não gera "scan vazio válido" — gera erro explícito.

### Por que foi desenhado assim

O alvo tem identidade determinística (mesmo diretório, mesmo ID em scans
diferentes), o que permite comparar relatórios no tempo e dizer "isso mudou
desde ontem". Metadata Travada impede que o próprio scanner altere a cena do
crime no meio da análise.

**Verificar:** teste de target inválido × `TargetError` · **Issue:** #19.

---

## #20 — Caminhos: como invasores (e acidentes) quebram scanners

### O que o scan busca

Nomes de arquivo são a primeira arma contra a ferramenta que os lê:
`../../etc/cron.d/x` para escapar do diretório analisado, `<script>` e
sequências ANSI para atacar o relatório, `C:\...` para explorar peculiaridades
do Windows, byte NUL para truncar strings em C, Unicode com duas formas para
o "mesmo" nome. O scanner só aceita caminhos relativos canônicos confinados à
raiz — todo o resto é rejeitado em voz alta, nunca "ajeitado" em silêncio.

### Por que foi desenhado assim

Porque "ajeitar" caminho hostil é adivinhar intenção do invasor — e adivinhação
erra para o lado perigoso. Exceção didática que o próprio desenvolvimento
revelou: `a/..` resolve para o próprio root (benigno), não é ataque; no
Windows, até `Path.joinpath('::')` descartava a raiz inteira, e um teste
automático com milhares de entradas hostis aleatórias caçou o bug. Lição para
o analista: **desconfie de relatório que mostra paths estranhos sem marcar
como estranhos** — path bizarro é evidência, não sujeira.

**Verificar:** property test de confinamento · **Issue:** #20.

---

## #21 — Artefatos: tudo que o invasor pode tocar

### O que o scan busca

Incidente não mora só em "arquivos": mora em symlink apontando para fora,
em FIFO/socket esquecido, em registro de banco, em evento de cron, em entrada
de configuração. O scanner modela tudo isso como **artefatos** de 4 tipos
(arquivo, diretório, symlink, especial) — porque cada tipo pede um cuidado:
symlink se registra e nunca se segue (seguir é cair na armadilha), especial
nunca se abre como comum (abrir um FIFO trava; abrir device explode).

### Por que foi desenhado assim

Para que nenhum esconderijo fique fora do modelo: se não é arquivo nem
diretório, é `especial` — visível no inventário em vez de invisível na análise.
E cada artefato tem ID estável, então dá para apontar "este objeto" em
qualquer discussão, ticket ou re-scan.

**Verificar:** symlink com destino registrado e nunca atravessado · **Issue:** #21.

---

## #22 — Inventário: mapear antes de julgar

### O que o scan busca

A varredura completa e ordenada de tudo que existe — incluindo arquivos
ocultos (`.`), que muito "scanner" amador ignora e onde backdoor adora morar.
Symlinks entram como links (com destino anotado), nunca atravessados: loops e
fugas são impossíveis por construção, não por verificação posterior. Erro de
permissão num arquivo não aborta nada — vira lacuna explícita de cobertura.

### Por que foi desenhado assim

Porque julgar antes de mapear é como diagnosticar sem anamnese: o relatório
precisa dizer "olhei N objetos", não só "achei M problemas". E ordem
determinística garante que dois scans do mesmo alvo sejam comparáveis —
sem isso, `diff` entre relatórios seria ruído.

**Verificar:** fixture com hidden + symlink + FIFO · **Issue:** #22.

---

## #23 — Evidência: sem prova, é opinião

### O que o scan busca

Cada observação carrega **quem a produziu e em que versão** (provenance),
quando, sobre qual objeto e em que estado de redação. Sem proveniência, o
scanner nem instancia a observação — e sem observação, nenhum finding existe.
É o hábito que separa analista de alarmista: toda afirmação do relatório
aponta para algo que outro humano consegue re-verificar.

### Por que foi desenhado assim

Porque "94% malicioso" sem mostrar o porquê não serve em incident response:
você precisa decidir se apaga, restaura ou reinstala — e decisão cara exige
prova auditável. IDs determinísticos ainda permitem deduplicar a mesma
observação entre scans.

**Verificar:** finding órfão é impossível por construção (ver #24) · **Issue:** #23.

---

## #24 — Severidade × confiança: grave não é o mesmo que certo

### O que o scan busca

Toda afirmação carrega dois eixos **independentes**: severidade (quão grave,
*se* verdade) e confiança (quão certo estamos). Um checksum oficial divergente
é `CRITICAL + DETERMINÍSTICO`; uma heurística isolada num nome suspeito pode
ser `CRITICAL + LOW`. No mesmo relatório, sem se confundir. É isso que impede
o produto de colapsar tudo num "INFECTED" opaco — e é a lente com que você
deve ler qualquer ferramenta de segurança, inclusive esta.

### Por que foi desenhado assim

Porque o erro mais comum em resposta a incidente é tratar chute confiante
como fato (e fato incerto como "deve ser nada"). Reclassificar a gravidade
não muda a identidade da afirmação — quando uma regra amadurece, o histórico
continua íntegro.

**Verificar:** matriz severidade × confiança nos finding cards · **Issue:** #24.

---

## #25 — Cobertura: o antídoto contra o "está limpo"

### O que o scan busca

O bug mais caro do ramo não é o falso positivo — é o **falso negativo
silencioso**: scanner roda, não acha nada, e alguém conclui "limpo" sem saber
que o motor de assinaturas estava ausente e 300 arquivos eram ilegíveis. Cada
capacidade declara seu estado (completo, parcial, pulado, indisponível,
falhou, não-aplicável) com a contabilidade exata. YARA ausente nunca vira
"completo".

### Por que foi desenhado assim

Porque "zero findings" sem cobertura completa **não significa limpo** — e o
relatório diz isso com todas as letras. Ao contratar ou operar qualquer
scanner, pergunte sempre: "o que ele *não* olhou?" Se a ferramenta não responde,
ela está te vendendo tranquilidade, não segurança.

**Verificar:** seção Coverage em todo relatório · **Issue:** #25.

---

## #30 — Reconhecer WordPress sem acreditar em nome

### O que o scan busca

"Tem `wp-content`, logo é WordPress" seria o falso positivo inaugural: backup,
tema solto ou diretório com nome famoso enganaria tudo. O scanner exige
**combinação de sinais com o tipo certo** (arquivo `version.php`, diretórios
`wp-admin/` e `wp-content/`, arquivo `wp-config.php`) — no mínimo 2 de 4 — sem
banco e sem ler conteúdo nenhum.

### Por que foi desenhado assim

Porque detecção de plataforma errada contamina todo o resto (zonas erradas,
regras erradas). Nome sem tipo é fantasia: symlink com nome famoso não conta,
e versão fica em branco até ser extraída com segurança em outra etapa — ausência
honesta em vez de chute.

**Verificar:** diretório só com `wp-content` não é detectado · **Issue:** #30.

---

## #31 — Zonas: o mesmo arquivo significa coisas diferentes por lugar

### O que o scan busca

Um `loader.php` em `mu-plugins/` (carregado automaticamente) e o mesmo nome
em `uploads/` (que deveria ser conteúdo inerte) são situações opostas — mas
sem contexto, parecem iguais. O WordPress é dividido em 9 zonas, cada uma com
sua **expectativa**: core protegido espera igualdade com o oficial; uploads
espera não-executável; cache espera churn e não merece alarme. Regras não
perguntam "o que é este arquivo?" no vazio — perguntam "o que significa este
arquivo *nesta zona*?".

### Por que foi desenhado assim

Porque contexto decide gravidade, não nome. Arquivo oficial da raiz
(`index.php`, `wp-login.php`...) é comparável com o upstream; config visível
(`wp-config.php`, `.htaccess`) merece análise de política, nunca igualdade
silenciosa; desconhecido na raiz vai para área sensível (atenção, não
silêncio); MU-plugin é *posição no mapa*, nunca veredito — dizer se é
malicioso exige evidência, não localização.

**Verificar:** tabela de 16 casos cobrindo as 9 zonas · **Issue:** #31.

---

## #33 — Integridade: perguntando ao WordPress.org sem acreditar cego

### O que o scan busca

 O teste mais forte que existe contra adulteração: comparar cada arquivo do
core com os **checksums oficiais por versão**. Arquivo que diverge do oficial
é fato determinístico (`MISMATCH`); esperado ausente (`MISSING`) sugere
remoção; extra em área protegida (`UNEXPECTED_FILE`) sugere plantação. Tudo
sem executar nada do alvo e sem exigir banco.

### Por que foi desenhado assim

Porque integridade oficial é o único "limpo parcial" honesto que existe — e
mesmo ele vem com provenance (qual provider, qual versão, quando). Lição de
método que vale para qualquer ferramenta: o contrato do provider foi validado
contra o binário real (a doc sugeria um formato que o binário rejeita!),
e mensagem desconhecida vira erro explícito, nunca classificação silenciosa —
errar para o lado do silêncio seria o falso negativo institucionalizado.

**Verificar:** #45 (supressão) mostra o outro lado: o que o oficial absolve ·
**Issue:** #33.

---

## #34 — Plugins: oficial verifica, premium declara

### O que o scan busca

O mesmo teste de integridade, por componente: cada plugin oficial é comparado
com seus checksums (`--strict`, que pega até mudança "soft"). E o ponto que
mais confunde donos de site: **plugin premium/sem baseline não é "malicioso"
— é `UNVERIFIED`**. Sem origem confiável para comparar, o scanner declara
ignorância honesta em vez de acusar (ou, pior, de silenciar).

### Por que foi desenhado assim

Porque "não sei" é resposta legítima e valiosa: ela diz exatamente onde
investigar manualmente ou fornecer o pacote limpo do fornecedor (Fase C
aceitará baselines do operador). Plugin fora do WordPress.org nunca aparece
nos resultados do provider — só nos avisos — então o scanner extrai os slugs
dali: visível no coverage, jamais confundido com erro.

E atenção ao ponto que mais importa na prática: `UNVERIFIED` não é pulado.
O código premium é varrido por heurísticas e IOC como qualquer outro — só o
que o baseline confiável *verificou* é absolvido (ver #45). Sem baseline, sem
absolvição: o relatório entrega os achados e **você decide** (remover,
atualizar, isolar, aceitar o risco). Ferramenta que pula premium em silêncio
esconde justamente onde webshell gosta de morar.

**Verificar:** premium em `unverified_plugins`, nunca em findings · **Issue:** #34.

---

## #35 — PHP em uploads: onde código é notícia, não paisagem

### O que o scan busca

PHP dentro de `wp-content/plugins` é paisagem; o mesmo PHP dentro de
`wp-content/uploads` é notícia — uploads deveriam ser mídia inerte, e código
lá é o padrão clássico de webshell plantada via upload vulnerável. A regra
olha **conteúdo, não extensão** (magic JPEG passa, `<?xml` de SVG legítimo não
é PHP), e dispara como *violação de expectativa* (HIGH), nunca como veredito
de "malware".

### Por que foi desenhado assim

Porque extensão é alegação do invasor (renomear `shell.php` para `foto.jpg`
não muda o `<?php` dentro) e porque contexto decide: o mesmo conteúdo em
plugin legítimo não acusa. Exceções reais (plugin que grava PHP em uploads)
entram numa allowlist do operador — regra com válvula de escape documentada
em vez de regra que você desliga por completo no primeiro falso positivo.

**Verificar:** fixture `uploads_php` (positivo + jpg + plugin legítimo) · **Issue:** #35.

---

## #36 — IOCs: o vocabulário dos sinais conhecidos

### O que o scan busca

Indicadores que você já conhece de incidentes passados ou threat intel:
trecho de código (`eval(` de dropper conhecido), domínio de C2, fragmento de
URL, hash de arquivo. Cada tipo tem validação própria (SHA exige 64 hex,
domain normaliza caixa) — indicador malformado nem nasce, em vez de gerar
falso negativo silencioso no meio do scan.

### Por que foi desenhado assim

Porque IOC é memória institucional: o que um incidente te ensinou vira
`kind:value` num arquivo e passa a vigiar todos os próximos scans. E porque
tipo validado evita a armadilha clássica — procurar hash com 63 caracteres e
concluir "limpo".

**Verificar:** `sessao-iocs.txt` da sessão real · **Issue:** #36.

---

## #37 — Busca literal: bytes, fronteira e evasão

### O que o scan busca

O IOC em qualquer lugar do conteúdo — inclusive **partido no meio do buffer
de leitura** (técnica boba de evasão seria escapar por fronteira de chunk, e
o scanner carrega overlap exatamente para isso), com offset absoluto e
contexto limitado em bytes crus, sem decodificar binário como texto. Milhares
de ocorrências não explodem o relatório: acima do cap, para de guardar mas
continua contando.

### Por que foi desenhado assim

Porque atacante conta com preguiça de implementação: string dividida, binário
com bytes inválidos, 50 mil matches para estourar memória. Cada uma dessas
tem resposta explícita — e hash SHA não se busca como texto (se compara via
hash do arquivo, cada ferramenta no seu quadrado).

**Verificar:** teste de IOC cruzando chunk sem duplicar nem perder · **Issue:** #37.

---

## #39 — Heurísticas: sinal fraco sozinho, cadeia combinada

### O que o scan busca

Os padrões clássicos de código malicioso PHP: execução dinâmica (`eval`,
`assert`, `create_function`), cadeias de encoding (`base64_decode`,
`gzinflate`...), APIs de processo/arquivo/rede, funções variáveis (`$x(`),
backticks de shell, literais encoded gigantes. Sozinhos, quase todos aparecem
em código legítimo — por isso existe a **tabela de combinação explícita**:
encoding + execução vira HIGH; três famílias, HIGH; isolado fraco, silêncio
ou LOW. E **nunca CRITICAL**: heurística não tem patente de certeza.

### Por que foi desenhado assim

Porque o erro clássico dos scanners é transformar coincidência em veredito
(`base64_decode` existe no core legítimo!). A tabela é pública e auditável —
quando ela errar, você sabe exatamente qual linha ajustar, em vez de brigar
com "pontuação de risco 94%" sem explicação. E todo positivo vem com os
sinais listados, para você conferir em segundos se faz sentido.

**Verificar:** fixtures `heuristics/` (cadeia + 3 negativos) · **Issue:** #39.

---

## #40 — Lendo o relatório sem ser atacado por ele

### O que o scan busca (em você)

Terminal é código executando strings do invasor: nome de arquivo com escape
ANSI reprograma o emulador, `[bold]` vira formatação real, `\n` no path quebra
a tabela e esconde linha. Todo conteúdo do alvo é neutralizado antes de
aparecer (ANSI removido, markup escapado como texto, controles visíveis), e
severidade sempre tem nome em texto — cor nunca é o único indicador
(daltônico, terminal sem cor e log redirecionado perdem zero informação).

### Por que foi desenhado assim

Porque o relatório é superfície de ataque: analista que abre HTML/terminal
contaminado sem sanitização vira vítima do incidente que investiga. Regra para
sua vida: **formatação é nossa, dados são deles, e os dois nunca se misturam**
— em qualquer ferramenta que você usar.

**Verificar:** título hostil com ANSI + markup + newline no teste · **Issue:** #40.

---

## #41 — Segredos: o relatório também vaza

### O que o scan busca (para esconder)

Relatório de incidente vaza por dois caminhos: você cola o JSON num ticket, e
o ticket vaza — levando `DB_PASSWORD`, salts e API keys junto. O scanner limpa
secrets **antes** de virar evidência (não só na tela): senha de banco com a
moldura preservada, bloco de chave privada inteiro, atribuições
password/secret/api_key/token, chaves AWS, tokens Bearer. E os padrões exigem
o *nome* da chave por perto — hash SHA, IDs e versões passam intactos, porque
redigir evidência legítima destruiria a investigação.

### Por que foi desenhado assim

Porque "mascaramos na UI" é teatro: o dado cru continua no JSON, no log, no
debug. Segredo precisa *não existir* abaixo da fronteira de coleta. Para sua
operação: nunca anexe `wp-config.php` bruto, dump de banco ou `.env` em
ticket — e desconfie de ferramenta que mostra secret no relatório "para
conveniência".

**Verificar:** testes adversários em `tests/security/` · **Issue:** #41.

---

## #45 — Absolvidos pelo oficial: por que o core limpo não gera findings

### O que o scan busca (e deixa de buscar de propósito)

Num WordPress íntegro, milhares de arquivos oficiais contêm `copy(`, `$var(`
e outros padrões que as heurísticas acusariam — ~200 findings falsos num core
limpo, como a sessão real provou. A resposta: **arquivo verificado contra
baseline confiável não recebe heurística**. O provider declara o escopo
verificado, e o orquestrador suprime detecção ali — menos nos arquivos que o
próprio provider apontou como divergentes (a correlação "mismatch + sinal no
mesmo arquivo" é justamente a hipótese mais forte que existe).

### Por que foi desenhado assim

Porque acusar código oficial é provar que a ferramenta não entende confiança:
se o upstream absolveu, heurística não recorre. E porque a supressão é
contada e visível (`3338 suprimidos por baseline confiável`) — absolvição
silenciosa seria outro falso negativo em potencial. Para você: findings
zerados *com* baseline verificado valem ouro; sem baseline, valem uma
investigação.

**Verificar:** sessão real (cru → 0 findings; adulterado → 2) · **Issue:** #45.

---

## #48 — Manifest: a origem confiável por escrito

### O que o scan busca

Comparar com "o original" exige ter o original descrito em algum lugar
confiável: o manifest lista cada arquivo esperado com seu SHA-256, quem
garante aquilo (upstream oficial, operador, release assinada — ou referência
não-confiável, declarada como tal) e a provenance do pacote. Sem isso,
"diverge do quê?" não tem resposta — e é por isso que premium sem manifest é
`UNVERIFIED`, não "suspeito".

### Por que foi desenhado assim

- **Confiança em 4 níveis, não binária**: oficial, operador, assinada e
  referência não-confiável (que serve para diff, nunca para acusar violação).
  A linguagem do relatório muda com o nível — nem "limpo" falso, nem acusação
  sem base.
- **Manifest hostil não atravessa**: `../../`, absoluto, duplicata e hash
  inválido morrem na construção — porque manifest vem de fora (operador,
  download, ZIP) e tudo de fora é input até prova em contrário.
- **Uma forma canônica por arquivo**: `a/../a.php` e `a.php` são o mesmo; o
  manifest guarda uma forma só, para a comparação nunca divergir por sintaxe.

**Verificar:** `src/wirs/domain/baseline.py`,
`tests/unit/test_baseline_manifest.py` · **Issue:** #48.

---

## #49 — Comparar: quatro respostas, não duas (WIRS-041)

### O que o scan busca

Dado o manifest (#48) e os hashes reais da árvore, cada arquivo recebe um de
quatro vereditos: `match` (idêntico), `mismatch` (mudou — com esperado e real
lado a lado), `missing` (o manifest promete, o disco não entrega) e
`unexpected` (o disco tem, o manifest não conhece). Todo extra em escopo
protegido entra como `unexpected`, não como curiosidade.

### Por que foi desenhado assim

- **Quatro estados em vez de "igual/diferente"**: ausente e extra são perguntas
  diferentes ("removeram?" vs "plantaram?") e merecem severidades e próximos
  checks diferentes. Colapsar tudo em "diverge" joga fora a investigação.
- **Mismatch carrega os dois hashes**: a evidência comparável é o que permite
  ao analista (ou à correlação futura) decidir se foi 1 byte ou reescrita
  total — sem reler o disco.
- **Puro e reutilizável**: a função compara manifest contra mapa de hashes,
  sem saber de filesystem, WP-CLI ou CLI — o mesmo código servirá ao ZIP (#51)
  e ao mapping premium (#52).

**Verificar:** `compare_baseline` em `src/wirs/domain/baseline.py`,
`tests/unit/test_baseline_compare.py` · **Issue:** #49.

---

## #50 — Fotografar o limpo: `baseline create` (WIRS-042)

### O que o scan busca

Transformar "o plugin premium íntegro que você tem" num manifest verificável:
`wirs baseline create ./componente-limpo --name X` percorre o diretório,
calcula SHA-256 de cada arquivo regular e grava manifest com provenance
(origem, data, hash do pacote). O manifest gerado verifica o próprio diretório
— tudo `match` — provando que a fotografia é fiel antes de ser usada.

### Por que foi desenhado assim

- **Só lê, nunca executa**: o builder usa o mesmo inventory sem-follow e o
  mesmo reader `rb` do scan — gerar baseline de um pacote nunca roda nada
  dele. Symlinks (inclusive para fora) e arquivos especiais ficam de fora:
  não são conteúdo verificável por hash.
- **Provenance junto do hash**: `source` guarda o diretório de origem,
  `created_at` a data, `package_hash` o resumo do pacote inteiro — porque um
  manifest sem "quando e de onde" vira verdade sem dono.
- **Trust de operador, declarado**: o manifest nasce `TRUSTED_OPERATOR` — vale
  o quanto vale a sua certeza de que aquele diretório estava limpo. A
  ferramenta não finge que sabe mais do que você disse a ela.

**Verificar:** `wirs baseline create --help`,
`src/wirs/infrastructure/baseline.py`,
`tests/integration/test_baseline_create.py` · **Issue:** #50.

---

## #51 — ZIP confiável sem cair em armadilha (WIRS-043)

### O que o scan busca

Gerar o mesmo manifest a partir do ZIP que o fornecedor (ou você) guardou:
extrai isolado, calcula SHA-256 por arquivo e identifica o pacote pelo hash do
próprio ZIP. Manifest do ZIP ≡ manifest do diretório extraído — a embalagem
não muda a fotografia.

### Por que foi desenhado assim

- **ZIP é input hostil clássico**: `../../evil.php` (zip-slip), symlink que
  aponta para fora e bomba de expansão são os três ataques testados — travessia
  vira erro de fronteira, symlink nunca é materializado, expansão tem teto.
  Baseline que deixa o ZIP escrever fora do destino não é baseline, é
  vulnerabilidade.
- **Hash do ZIP como identidade do pacote**: o `package_hash` aqui é o SHA-256
  do arquivo ZIP — amarra "este manifest fala *deste* pacote", permitindo
  re-verificar a embalagem antes de confiar no conteúdo.
- **Extração nunca executa**: copiar bytes não roda lifecycle script; não há
  caminho de código entre "abrir o ZIP" e "rodar algo dele".

**Verificar:** `src/wirs/infrastructure/archive.py`,
`tests/unit/test_baseline_archive.py`,
`tests/security/test_baseline_archive_attack.py` · **Issue:** #51.

---

## #52 — Premium com dono: mapping path→manifest (WIRS-066)

### O que o scan busca

Fechar a promessa "premium nunca é skip": `wirs scan --baseline mapping.json`
associa cada diretório de plugin/theme ao seu manifest. Mapeado e íntegro vira
`covers` (absolvido como baseline confiável, sem heurística redundante);
mapeado e adulterado gera `WP.PLUGIN.HASH_MISMATCH` + `UNEXPECTED_FILE`;
**não-mapeado continua `UNVERIFIED`** — com a lacuna nomeada no coverage
(`baseline:plugin:premium`, parcial), nunca uma acusação.

### Por que foi desenhado assim

- **O mapping é explícito, não adivinhado**: o scanner não tenta descobrir
  sozinho qual manifest vale para qual pasta — confiança delegada sem
  declaração seria chute. O JSON `{dir: manifest}` é a sua assinatura dizendo
  "este pacote eu garanto".
- **Reuso total**: o provider monta `BaselineBuilder` (#50) + `compare_baseline`
  (#49) sobre o seam `IntegrityProvider` — o orquestrador nem percebe que não
  é WP-CLI: findings, covers e coverage saem no mesmo idioma.
- **UNVERIFIED nomeado é acionável**: a entrada de coverage diz *qual*
  componente está sem baseline — o próximo passo (gerar manifest, #50) é
  óbvio. Lacuna anônima vira "algo não verificado em algum lugar", que ninguém
  resolve.
- **E2E prova os três destinos**: limpo (exit 0, zero findings), adulterado
  (exit 1, mismatch + unexpected) e sem mapping (exit 0, parcial nomeado).

**Verificar:** `wirs scan --help`,
`src/wirs/providers/operator_baseline.py`,
`tests/integration/test_premium_baseline.py` · **Issue:** #52.

---

## #56 — Violação ou diferença? O trust decide a frase (WIRS-044)

### O que o scan busca

Nem todo "diferente do manifest" é acusação: contra baseline confiável
(`TRUSTED_OPERATOR`, `TRUSTED_UPSTREAM`), divergência é `HASH_MISMATCH`
determinístico; contra referência não-confiável (`UNVERIFIED_REFERENCE`), o
mesmo byte diferente é `REFERENCE_DIFF` com confiança `HIGH` — um diff para
investigar, nunca uma "violação de integridade".

### Por que foi desenhado assim

- **A frase é parte da evidência**: "violação" autoriza ação (reinstalar,
  bloquear); "diferença" pede investigação. Chamar diff de violação é como
  testemunha que exagera — contamina a decisão do analista.
- **Confiança rebaixada junto**: `DETERMINISTIC`→`HIGH` comunica que o fato
  (bytes diferem) é certo, mas a conclusão (adulteração) não tem fiador. O
  atributo `trust` no finding mostra o fiador — ou a ausência dele.
- **Vale para os três estados**: mismatch, missing e unexpected ganham o
  prefixo `REFERENCE_` — porque "arquivo sumiu da referência fraca" também
  não é "arquivo removido por invasor".

**Verificar:** `_REFERENCE_SUFFIX` em `src/wirs/application/orchestrator.py`,
`tests/integration/test_reference_trust.py` · **Issue:** #56.

---

## #57 — Cache com dono e idade: baseline guardado, não esquecido (WIRS-045)

### O que o scan busca

Reutilizar manifests sem rebaixar a confiança: `baseline cache-store`
guarda o manifest em `~/.wirs/cache` com origem e data, e o mapping aceita
`cache:premium:1.0` no lugar do arquivo. Quando o scan usa o cache, cada
divergência carrega a idade e a origem ("cache de 12d, origem
zip-do-fornecedor") — e referência fraca continua `REFERENCE_DIFF`, nunca
vira "violação" por estar guardada.

### Por que foi desenhado assim

- **Cache com provenance ou não é cache**: sem origem e data, um manifest
  guardado vira "verdade sem dono" — daqui a um ano ninguém sabe se ainda
  vale. O envelope registra os três; a idade viaja até o finding.
- **Staleness é dado, não expiração**: o scanner não decide sozinho quando
  um baseline "venceu" (isso seria chute com data) — ele declara a idade e
  deixa a decisão com você. Expiração silenciosa seria outro falso negativo.
- **Ausente/corrompido = erro acionável**: cache sem a entrada falha
  explicitamente ("rode `baseline cache-store`") em vez de verificar contra
  vazio ou, pior, contra outro componente.

**Verificar:** `src/wirs/infrastructure/baseline_cache.py`,
`tests/integration/test_baseline_cache.py` · **Issue:** #57.

---

## #58 — Assinado por quem? HMAC com chave em arquivo (WIRS-046)

### O que o scan busca

Amarrar "este manifest saiu do nosso CI": `baseline sign` grava um `.sig`
destacado (HMAC-SHA256 sobre os bytes do manifest) e o scan confere quando
há `--sign-key`. Manifest adulterado pós-assinatura não passa — nem no
`verify-sig`, nem no scan. Sem chave, componente com `.sig` vira `UNVERIFIED`
com o motivo nomeado — nunca erro silencioso.

### Por que foi desenhado assim

- **HMAC stdlib, sem dep nova**: para release interna/CI, segredo
  compartilhado basta; assimétrico (chave pública distribuível) seria
  gestão de chaves maior para um ganho que o caso de uso não pede.
- **Chave em arquivo, nunca em arg**: `--key-file`, não `--key` — segredo
  em linha de comando vaza para histórico e lista de processos (§19.8).
- **Destacado, não embutido**: o `.sig` viaja ao lado do manifest sem
  alterar o schema — manifests antigos continuam válidos e o cache (#57)
  nem percebe a diferença.
- **Sem chave = UNVERIFIED nomeado**: "assinatura presente mas sem chave"
  no coverage — o operador sabe exatamente o que falta, em vez de receber
  um "verificado" que ninguém verificou.

**Verificar:** `src/wirs/infrastructure/baseline_sign.py`,
`tests/integration/test_signed_manifest.py` · **Issue:** #58.

---

## #61 — Assinaturas alugadas: YARA como provider opcional (WIRS-081)

### O que o scan busca

O que as heurísticas não sabem nomear: assinaturas YARA descrevem malware
conhecido por padrão de bytes ("webshell que decodifica e executa"), e o
match diz *qual regra* pegou, com tags e namespace. É o vocabulário pronto
da comunidade, em vez de reinventar um corpus concorrente.

### Por que foi desenhado assim

- **Opcional de verdade**: sem `yara-python`, o scan continua e o coverage
  marca `UNAVAILABLE` — assinatura é reforço, nunca pré-requisito. Ferramenta
  que aborta sem o plugin opcional está blefando sobre "opcional".
- **Bytes do reader, nunca path direto**: o YARA recebe o conteúdo já lido
  sob budget — o analyzer não abre arquivo por conta própria, então limite
  de tamanho e recusa de especiais continuam valendo.
- **Timeout por arquivo, não por scan**: regra lenta trava aquele arquivo,
  não a investigação inteira. Degradar parcial é o comportamento padrão do
  WIRS para tudo que é externo.
- **Regra sem severidade declarada vira `medium`**: YARA não promete
  gravidade, só casamento de padrão — a severidade honesta de "casou, sem
  contexto" é média, e a regra original viaja junto para você julgar.

**Verificar:** `src/wirs/providers/yara_provider.py`,
`tests/unit/test_yara_provider.py`, `docs/providers/yara-python.md` ·
**Issue:** #61.

---

## #62 — Assinaturas da casa: pack YARA builtin (WIRS-082)

### O que o scan busca

Padrões de técnicas conhecidas em PHP: `eval` combinado com cadeia de
decoding (webshell-like) e `include` com variável de input. Regras com
nome, descrição, severidade e condição de tamanho — para o match dizer
*o quê* casou, não só "casou algo".

### Por que foi desenhado assim

- **Técnicas, não malware**: as regras descrevem padrões de bytes; os
  fixtures que as disparam são sintéticos sem backend real. Assinatura
  boa nomeia a técnica para o analista reconhecer, não para o scanner
  "provar infecção" sozinho.
- **`experimental/` fora por default**: regra com falso-positivo conhecido
  não entra no pack padrão — promoção segue maturidade (experimental →
  beta → stable), nunca pressa.
- **Severidade na regra, não no achismo**: cada regra declara a sua (high
  para eval+decode, medium para include dinâmico) — o provider só usa
  `medium` quando a regra não declara nada.

**Verificar:** `rules/yara/builtin/php_webshell.yar`,
`rules/yara/experimental/php_obfuscation.yar`,
`tests/integration/test_yara_rules.py` · **Issue:** #62.
