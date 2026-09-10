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
