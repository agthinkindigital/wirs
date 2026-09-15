# PROMPT ÚNICO — REALINHAMENTO DE PRODUTO, ARQUITETURA, ROADMAP, ISSUES E DOCUMENTAÇÃO DO WIRS

Você está trabalhando no repositório:

- `https://github.com/agthinkindigital/wirs`
- branch de análise e trabalho: `develop`

Esta tarefa é uma **auditoria e realinhamento estrutural do projeto WIRS**. Não é uma tarefa para implementar uma feature isolada, não é uma refatoração cosmética e não é autorização para transformar o produto em outra categoria de software.

O objetivo é identificar onde documentação, roadmap, Epics, Issues, prioridades, dependências e linguagem de produto começaram a se afastar da finalidade real do WIRS; corrigir essas derivações; criar mecanismos documentais que impeçam a repetição do problema; e deixar a DAG preparada para continuar o desenvolvimento no eixo correto.

---

## 1. Regra principal: entenda o produto antes de tocar no planejamento

A definição abaixo é a direção de produto aprovada pelo mantenedor e deve ser tratada como **North Star** desta auditoria.

### 1.1 O que o WIRS é

O WIRS é, primariamente, um:

> **scanner read-only de segurança, integridade e código suspeito para aplicações web, inicialmente especializado em WordPress, com core genérico para expansão posterior a PHP genérico e outros CMS/frameworks.**

Ele deve ajudar um profissional de segurança/infraestrutura a trocar uma inspeção manual de milhares de arquivos por uma lista pequena, auditável e priorizada de objetos que merecem análise humana.

O produto precisa:

1. inventariar os artifacts do target;
2. compreender o contexto/plataforma quando possível;
3. comparar arquivos contra baselines confiáveis quando eles existem;
4. identificar arquivos modificados, inesperados, ausentes ou sem baseline;
5. analisar conteúdo em busca de IOCs, assinaturas, padrões, ofuscação, comportamentos suspeitos e violações de expectativa;
6. combinar sinais independentes sem transformar heurística em fato;
7. gerar Evidence, Findings, Coverage e, quando houver base suficiente, Diagnoses;
8. produzir relatório canônico e views humanas seguras;
9. reduzir drasticamente a quantidade de arquivos que o analista precisa revisar manualmente;
10. manter tudo reproduzível, read-only, explicável e com falso negativo silencioso tratado como problema de Coverage.

### 1.2 Resultado operacional esperado

O resultado ideal não é:

```text
SITE INFECTADO
94% MALICIOSO
```

O resultado ideal é semelhante a:

```text
18.000 arquivos inventariados

11 artifacts requerem investigação:
- 3 críticos
- 4 altos
- 4 médios

2 arquivos do core divergem do baseline oficial
1 desses arquivos também corresponde a assinatura YARA de webshell

3 arquivos com conteúdo executável foram encontrados em zona de uploads

2 arquivos de plugin sem baseline confiável possuem cadeia de
ofuscação + execução dinâmica

4 arquivos foram modificados, mas não apresentam sinais maliciosos
adicionais no conjunto de checks executado

Coverage:
- filesystem: complete
- core integrity: complete
- plugin baseline: partial
- yara: complete
```

O analista deve conseguir ir direto aos poucos artifacts problemáticos, entender **por que** cada um foi destacado e decidir a correção.

---

## 2. O que o WIRS NÃO deve virar agora

Não redesenhe o projeto atual como:

- SIEM;
- XDR;
- EDR;
- daemon residente;
- plataforma de monitoramento contínuo;
- pipeline Kafka/Redis de eventos;
- conjunto de agentes Go/Rust instalados nos hosts;
- sistema de resposta automática;
- motor de quarentena automática;
- WAF;
- SOAR;
- plataforma centrada em cPanel;
- produto cujo principal objeto seja IP, sessão ou credencial;
- dashboard web obrigatório;
- serviço remoto obrigatório;
- scanner dependente de SSH;
- mecanismo cuja detecção primária seja feita por LLM.

Essas ideias podem existir como **visão futura, opt-in e desacoplada**, mas não podem dirigir a arquitetura, bloquear o scanner local ou ocupar a frente da DAG enquanto o scanner de arquivos/código ainda está evoluindo.

---

## 3. Princípio de arquitetura de evolução

A arquitetura lógica de produto deve continuar aproximadamente assim:

```text
Target
  ↓
Inventory
  ↓
Artifact classification
  ↓
Platform/CMS discovery
  ↓
Zones / context
  ↓
Baseline / integrity checks
  ↓
Content analysis
  ├── content hints
  ├── IOC
  ├── heuristics
  ├── signatures / YARA
  ├── policy rules
  └── future analyzers
  ↓
Evidence
  ↓
Findings
  ↓
Correlation
  ↓
Diagnoses
  ↓
Coverage
  ↓
Canonical Report
  ↓
CLI / TUI / JSON / Markdown / HTML
```

Fontes futuras devem entrar lateralmente:

```text
logs locais declarados ───────┐
threat intel opcional ────────┤
snapshot/archive ──────────────┤→ enriquecem o MESMO modelo
remote target futuro ─────────┤
AI AnalysisPacket futuro ─────┘
```

Nunca inverter a relação e fazer o scanner de arquivos depender dessas expansões.

---

## 4. Regra essencial: integridade e análise de conteúdo são caminhos complementares

Não reduza o WIRS a “analisa profundamente apenas arquivo modificado”.

O produto precisa manter dois caminhos independentes:

```text
INTEGRITY
artifact → baseline confiável → MATCH / MISMATCH / MISSING / UNEXPECTED / UNVERIFIED
```

e:

```text
SECURITY CONTENT ANALYSIS
artifact → IOC / heurística / YARA / policy / outros analyzers
```

Depois eles se correlacionam.

Isto é especialmente importante para plugins/themes/custom code.

Um plugin malicioso, nulled ou comprometido pode já ter sido distribuído com um backdoor. Nesse caso não existe necessariamente `HASH_MISMATCH` contra um “original” local. Portanto:

- plugin oficial com baseline confiável pode ser absolvido quando o conteúdo está comprovadamente igual ao upstream;
- plugin premium/custom sem baseline não é malicioso por definição;
- porém plugin premium/custom sem baseline **não pode ser pulado**;
- código sem baseline deve continuar sujeito a content analysis;
- artifact inesperado deve ser analisado;
- artifact divergente deve ser analisado;
- zonas sensíveis devem influenciar contexto e prioridade, nunca substituir evidência.

---

## 5. Detecção deve ser explicável

Preserve os princípios já corretos no código:

- `eval()` isolado não significa malware;
- `base64_decode()` isolado não significa malware;
- heurística não vira `CRITICAL` só porque existe uma função perigosa;
- severidade e confiança são eixos independentes;
- conteúdo executável em `uploads` é violação forte de expectativa, não prova isolada de malware;
- `UNVERIFIED` significa falta de baseline, não comprometimento;
- YARA/signature match tem provenance e não apaga a necessidade de contexto;
- zero findings sem Coverage suficiente não significa “limpo”.

Combinações são mais valiosas:

```text
baseline mismatch
+ YARA webshell
+ cadeia eval/base64/gzinflate
+ zona protegida
= hipótese muito mais forte
```

O primeiro motor de Diagnosis deve ser capaz de trabalhar somente com informações do próprio scan de arquivos, antes de depender de logs.

---

## 6. Ordem estratégica aprovada

Use esta ordem como referência durante a revisão. Você pode ajustar detalhes quando o código exigir, mas não pode inverter os horizontes sem registrar decisão explícita.

### Horizonte A — núcleo útil e confiável do scanner

Prioridade máxima:

1. artifact canônico de scan completo e referencialmente íntegro;
2. Evidence/Artifact/Finding/Coverage/provider status/Diagnoses serializáveis;
3. redaction defensiva na fronteira final;
4. integração YARA real no `wirs scan`;
5. análise de conteúdo bounded/streaming suficiente para não depender apenas do início do arquivo;
6. regras/heurísticas/IOCs úteis para localizar código suspeito;
7. WordPress completo como primeiro adapter forte:
   - core;
   - plugins;
   - themes;
   - MU-plugins;
   - uploads;
   - cache;
   - arquivos especiais/config;
   - official baselines;
   - operator baselines;
   - ausência de baseline explicitamente `UNVERIFIED`;
8. correlação file-centric:
   - integrity + YARA;
   - integrity + heurística;
   - YARA + heurística;
   - zone violation + assinatura/heurística;
   - IOC + outros sinais;
9. reporting claro:
   - JSON canônico;
   - terminal;
   - Markdown;
   - HTML self-contained;
   - PDF somente como extensão opcional;
10. CLI/TUI operacional para selecionar target, profile, formato/local de report e overrides quando necessários.

### Horizonte B — expansão natural do scanner

Depois do fluxo acima estar sólido:

1. PHP Generic local;
2. zones configuráveis de aplicação/webroot;
3. análise de `.htaccess`, `.user.ini`, config e código PHP sem WordPress;
4. outros CMS/adapters;
5. archive target local;
6. comparação entre scans/snapshots quando fizer sentido.

PHP Generic não deve depender de Incident Bundle ou SSH para funcionar sobre um diretório local.

### Horizonte C — enriquecimento forense opcional

Somente após o scanner de filesystem/código estar maduro:

1. ingestão de logs locais explicitamente fornecidos;
2. timeline;
3. eventos cPanel/Apache/Nginx/PHP;
4. relações temporais;
5. contexto offline de IP/CIDR/ASN/UA;
6. diagnoses que usem arquivos + logs;
7. relatórios forenses enriquecidos.

Esses recursos enriquecem o scan; não redefinem o produto.

### Horizonte D — aquisição remota e integrações avançadas

Longo prazo:

1. SSH/SFTP read-only;
2. snapshot remoto;
3. remote ArtifactSource;
4. APIs opcionais de threat intelligence;
5. scheduling/fleet;
6. qualquer automação operacional externa.

SSH deve ser tratado como **uma nova forma de adquirir o mesmo Target/Artifacts**, não como fundação arquitetural.

### Horizonte E — IA

Muito depois:

1. AnalysisPacket redigido;
2. resumo;
3. explicação;
4. priorização assistida;
5. sugestão de próximos checks;
6. sugestão de remediação.

A IA:

- é opt-in;
- trabalha sobre dados redigidos;
- nunca cria Evidence determinística;
- nunca modifica fato determinístico;
- nunca é requisito para o scan funcionar.

---

## 7. Estado atual conhecido que exige auditoria

Não aceite esta lista cegamente: valide tudo no checkout e no GitHub antes de editar. Ela serve como conjunto inicial de hipóteses de drift.

### 7.1 Pontos aparentemente corretos e que devem ser preservados

- domain genérico separado de WordPress;
- Artifact/SafePath/read-only;
- Evidence/Finding/Coverage;
- severidade × confiança;
- WordPress zones;
- premium/custom sem baseline = `UNVERIFIED` e continua sendo analisado;
- heurísticas PHP por combinação;
- policy de executável em uploads;
- IOC streaming;
- YARA como provider opcional;
- JSON canônico;
- redaction;
- CLI/wizard;
- providers opcionais degradando Coverage;
- IA fora do pipeline determinístico.

### 7.2 Pontos de drift que você deve confirmar e corrigir

Verifique especialmente:

1. `ORCHESTRATOR-ROADMAP.md` ainda descreve E12 como Snapshot/Remote/SSH antes de PHP Generic, apesar de a própria Epic E12 já ter sido redefinida para Incident Bundle/Archive local e declarar SSH pós-1.0.
2. O roadmap listado no checkout pode parar em E15 enquanto já existem E16/E17.
3. `ESTADO_ORQUESTRATOR.md` pode estar operacionalmente obsoleto e ainda apontar próximos passos de fases já superadas.
4. E06/WordPress pode estar adiando backlog do adapter para depois de “logs e correlação”, o que inverte a prioridade do produto.
5. E09/Diagnosis foi puxada para conta/CIDR/cPanel/logs antes de existir uma primeira correlação file-centric.
6. #70 / PHP Generic local pode estar bloqueada por Incident Bundle (#68). Esse acoplamento deve ser removido se não houver necessidade técnica real.
7. E16/E17 e seus slices podem estar classificados como P1/MVP apesar de serem enriquecimento opcional.
8. filhos de Epic P2 podem estar marcados P1 sem justificativa.
9. #80 / HTML forense pode estar bloqueado por log coverage e diagnoses de hospedagem. O HTML deve conseguir renderizar um scan file-centric completo mesmo sem timeline/logs.
10. #77/#78 podem ser diagnoses específicas de hospedagem classificadas cedo demais.
11. #79/IP context está corretamente mais distante se estiver P2; preserve essa direção.
12. README pode citar SSH/remote numa versão mais próxima do que a direção atual permite.
13. Issues podem citar ADRs que não existem no checkout (por exemplo, valide qualquer referência a `ADR-011`).
14. referências a testes/arquivos podem estar incorretas, como já ocorreu em #65.
15. a documentação pode usar “scanner de hospedagem” como destino principal. Isso deve ser corrigido.
16. os documentos de melhoria baseados em ANFAMOTO podem estar funcionando como roadmap de produto. Eles devem virar **future vision** e **case study**, respectivamente.
17. o código de análise pode depender excessivamente apenas de `head` para heurística. Avalie, sem implementar nesta auditoria, se o roadmap precisa de content analysis bounded/multi-window/stream completo para localizar backdoors fora do início do arquivo.
18. YARA deve participar do artifact canônico e produzir provider status/Coverage honestos, sem erros/timeout silenciosos.
19. toda referência `artifact_ref`/`evidence_ref` do JSON canônico deve resolver.
20. `MISSING` precisa de identidade lógica resolvível no artifact canônico.

---

# 8. Esta tarefa NÃO é para implementar as features do roadmap

Nesta execução:

- não implemente SSH;
- não implemente PHP Generic;
- não implemente collectors;
- não implemente YARA integration;
- não implemente HTML;
- não implemente Diagnosis;
- não faça “só porque já está aqui” código de produto fora do necessário para corrigir governança/documentação.

O trabalho é:

1. auditar;
2. classificar drift;
3. corrigir documentação;
4. corrigir roadmap;
5. corrigir Epics/Issues/labels/dependências;
6. criar os artefatos de governança que impedem nova deriva;
7. deixar a DAG coerente para as próximas implementações.

Se encontrar bug de código que invalida documentação, registre-o e abra/ajuste Issue apropriada. Não esconda o problema alterando docs para fingir que está implementado.

---

# 9. Skills obrigatórias/esperadas

Leia primeiro o `SKILL_MAP.md` atual e use o contrato real das skills, não apenas o nome.

Para esta tarefa, a sequência esperada é aproximadamente:

1. `zoom-out`
   - mapear repositório, documentos, código, Epics, Issues e dependências;

2. `grill-with-docs`
   - confrontar a direção de produto com `WIRS_MASTER_SPEC_PT-BR.md`, `CONTEXT.md`, ADRs e arquitetura;

3. `grill-feature-with-docs`
   - revisar E05, E06, E07, E08, E09, E12, E13, E16 e E17 sem perder contratos existentes;

4. `requirements-clarity`
   - para cada proposta perguntar:
     - Why?
     - Existe forma mais simples?
     - Isso melhora o scanner de arquivos ou cria outro produto?

5. `improve-codebase-architecture`
   - somente para avaliar boundaries e seams; não use como licença para refatorar tudo;

6. `roadmap`
   - reconstruir ordem de Epics/marcos;

7. `triage`
   - realinhar labels/status/prioridades de Issues existentes;

8. `to-issues`
   - somente se gaps reais não puderem ser representados nas Issues atuais;

9. `agent-md-refactor`
   - tornar `AGENTS.md` e matriz documental objetivos, sem inflar leitura obrigatória;

10. `crafting-effective-readmes` / `edit-article` / `writing-clearly-and-concisely`
    - atualizar README e documentos de leitura humana;

11. `qa-analyst`
    - portão final de consistência documental/DAG.

Não use `scaffold-mvp`: o projeto já existe.
Não use skills de frontend web para inventar dashboard.
Não use `game-changing-features` para promover ideias pós-1.0 ao MVP.

---

# 10. Crie um Product Charter curto e normativo

Crie:

```text
docs/PRODUCT-CHARTER.md
```

Esse documento deve ser curto o suficiente para o agente sempre ler.

Conteúdo mínimo:

## Identidade

- scanner read-only de segurança/integridade/código suspeito;
- WordPress-first;
- core genérico;
- foco em filesystem/código;
- produto para reduzir revisão manual.

## Promessa

- encontra e prioriza artifacts que merecem investigação;
- explica por Evidence/Findings/Coverage;
- não promete “site limpo”.

## Não objetivos atuais

- SIEM;
- daemon;
- agentes residentes;
- SOAR;
- SSH obrigatório;
- dashboard web obrigatório;
- IA como detector;
- resposta automática.

## Ordem de expansão

```text
filesystem/code
→ WordPress forte
→ signatures/correlation/report
→ PHP Generic
→ outros adapters
→ logs opcionais
→ IP/threat intel
→ remote
→ AI
```

## Invariantes de produto

Inclua explicitamente:

1. feature futura nunca bloqueia scanner local;
2. content analysis sem baseline é obrigatória quando aplicável;
3. integridade não substitui content analysis;
4. logs enriquecem, não fundam o scanner;
5. SSH é acquisition seam;
6. AI é analysis seam;
7. UI nunca contém regra de negócio;
8. Diagnosis file-centric existe antes de Diagnosis host-centric;
9. uma perícia/caso real informa regras, não redefine sozinho o produto;
10. toda nova Epic precisa declarar a qual horizonte do charter pertence.

---

# 11. Substitua o modelo de “ordem linear de autoridade” por autoridade por assunto

A regra atual de autoridade puramente linear é insuficiente.

Crie uma seção normativa em `AGENTS.md` e na matriz:

| Pergunta | Fonte de verdade |
|---|---|
| O que o WIRS é / não é? | `docs/PRODUCT-CHARTER.md` |
| Quais termos existem no domínio? | `CONTEXT.md` |
| Quais requisitos/contratos gerais? | `WIRS_MASTER_SPEC_PT-BR.md` |
| Como as peças se encaixam? | `docs/ARCHITECTURE.md` |
| Por que uma decisão arquitetural foi tomada? | ADR aceito aplicável |
| O que realmente está implementado? | código + testes reproduzíveis |
| O que vem depois e em qual ordem? | `ORCHESTRATOR-ROADMAP.md` |
| Qual escopo/aceite de uma entrega? | Epic/Issue correspondente |
| Qual é o estado operacional momentâneo? | `ESTADO_ORQUESTRATOR.md` |
| Como uma detecção funciona para o analista? | `docs/ENTENDENDO-O-WIRS.md` |
| Qual o contrato de ferramenta externa? | `docs/providers/*` |
| Quais ideias ainda não são compromisso? | `docs/future/*` |
| O que um incidente ensinou? | `docs/case-studies/*` |

Se duas fontes do mesmo domínio de autoridade divergem, registre o conflito e resolva explicitamente.

---

# 12. Crie e preencha a Matriz Documental

Crie:

```text
docs/DOCUMENTATION-MATRIX.md
```

Ela é obrigatória e deve ser atualizada nesta auditoria.

Use no mínimo as colunas:

| Artefato | Tipo | Fonte de verdade para | Autoridade | Horizonte | Estado | Pode definir prioridade? | Pode criar escopo de implementação? | Upstream obrigatório | Downstream que deve acompanhar | Gatilho de atualização | Drift encontrado | Ação tomada | Última revisão |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Preencha pelo menos:

- `docs/PRODUCT-CHARTER.md`
- `AGENTS.md`
- `CONTEXT.md`
- `WIRS_MASTER_SPEC_PT-BR.md`
- `docs/ARCHITECTURE.md`
- `docs/README.md`
- `docs/ENTENDENDO-O-WIRS.md`
- `docs/adr/*`
- `docs/providers/*`
- `ORCHESTRATOR-ROADMAP.md`
- `ESTADO_ORQUESTRATOR.md`
- `README.md`
- `CHANGELOG.md`
- `SKILL_MAP.md`
- GitHub Epics
- GitHub slice Issues
- `docs/future/*`
- `docs/case-studies/*`

### Regras da matriz

`docs/future/*`:

- pode propor;
- não pode priorizar;
- não pode bloquear P0/P1;
- não pode criar compromisso sem promoção via Charter/Spec/Roadmap.

`docs/case-studies/*`:

- pode registrar lições e gaps;
- não pode redefinir a tese de produto;
- não pode, sozinho, reordenar roadmap;
- cada gap deve declarar:
  - `core`;
  - `expansão natural`;
  - `enriquecimento opcional`;
  - `longo prazo`;
  - `fora do escopo`.

`ESTADO_ORQUESTRATOR.md`:

- é snapshot;
- nunca é fonte de produto;
- deve trazer data/commit/branch;
- conteúdo obsoleto deve ser substituído, não acumulado indefinidamente.

---

# 13. Reorganize os documentos de melhorias

Os dois documentos de melhoria existentes devem ser corrigidos e classificados.

## `WIRS-MELHORIAS.md`

Transforme em visão de evolução alinhada ao scanner.

Destino recomendado:

```text
docs/future/WIRS-MELHORIAS.md
```

ou mantenha o path atual se houver razão de compatibilidade, mas deixe explícito no cabeçalho:

```text
Tipo: FUTURE VISION
Autoridade: não normativa
Não redefine roadmap automaticamente
```

Ele deve:

- começar pelo scanner de filesystem/código;
- preservar aprendizados do ANFAMOTO;
- remover arquitetura SIEM como alvo imediato;
- mover Kafka, agents, Redis Streams, ML, bloqueio, SOAR etc. para “possibilidades de longo prazo”;
- priorizar content analysis, WordPress, YARA, Diagnosis file-centric, report e PHP Generic;
- manter logs/IP/AI como enriquecimento opcional futuro.

## `WIRS-MELHORIAS-EXECUCAO-ANFAMOTO-v2.md`

Transforme em case study.

Destino recomendado:

```text
docs/case-studies/ANFAMOTO-GAPS.md
```

Ele deve afirmar explicitamente:

> ANFAMOTO é um caso de validação e descoberta de gaps. Não é a definição do produto WIRS.

O critério de sucesso do caso não deve ser “reproduzir 100% da perícia automaticamente”.

O critério primário deve ser:

> Dado um snapshot/diretório/arquivo do site, o WIRS reduz a massa de artifacts para uma lista pequena de arquivos suspeitos, com Evidence, Findings, Severity, Confidence, Coverage e Diagnoses file-centric.

Logs, IPs e timeline podem compor uma camada posterior do mesmo case study.

---

# 14. Realinhe roadmap, Epics e Issues

Faça isso somente após o Product Charter e a matriz estarem preenchidos.

## 14.1 Preserve IDs

- não reutilize IDs E##;
- não delete Issues para “limpar” histórico;
- prefira atualizar título/body/labels/dependências;
- se uma Issue ficou semanticamente incompatível, marque/reclassifique e crie substituta somente quando necessário;
- registre nota de realinhamento quando o significado mudar.

## 14.2 Ajustes que precisam ser avaliados

### E02 / #65

Continua central/P0.

Finalize as decisões HITL do artifact canônico antes de features que dependem do JSON.

### E07 / #66

Integração YARA ao scan é core do objetivo e deve permanecer próxima.

### E05

Reavalie backlog ainda não fatiado para garantir que exista caminho para:

- content analysis bounded além do `head`;
- padrões maliciosos em qualquer região relevante do arquivo;
- obfuscation/entropy quando justificável;
- extension/content mismatch;
- regras sobre config/scripts suspeitos;
- rule metadata e falsos positivos.

Não crie tudo sem grill/TDD; apenas garanta roadmap coerente.

### E06 WordPress

Não adie conclusão do adapter WordPress por depender de logs de hospedagem.

Reavalie backlog de:

- MU-plugins;
- config;
- themes;
- plugins;
- cache;
- root specials;
- policies úteis ao scanner de arquivos.

### E09 Diagnosis

Separe:

#### E09-A — correlação file-centric

Primeiro.

Exemplos:

- trusted baseline mismatch + YARA no mesmo Artifact;
- unexpected file + YARA;
- `UNVERIFIED` + high heuristic + IOC;
- executable em zona inerte + signature/heuristic;
- mismatch + cadeia PHP suspeita.

#### E09-B — correlação temporal/host

Depois, usando E16/E17.

As Issues host-centric atuais não devem bloquear a existência de Diagnosis file-centric.

### E12

Mantenha Incident Bundle/archive local se for útil, mas não como pré-condição do scanner PHP local.

SSH/SFTP deve continuar pós-1.0/longo prazo.

### E13 / #70

PHP Generic local deve conseguir:

```text
wirs scan ./legacy-php
```

sem Incident Bundle obrigatório.

Remova dependência de #68 se ela não for realmente necessária.

Promova E13 na ordem estratégica, sem necessariamente rotular tudo P0.

### E16/E17

Preserve a arquitetura local/read-only/bounded, mas reclassifique como enriquecimento opcional pós-core.

Não devem competir como P1 com conclusão do scanner.

### #76/#77/#78

Reavalie prioridade e bloqueios porque são majoritariamente temporal/host-centric.

Não use essas Issues para representar o primeiro Diagnosis do produto.

### #79

Contexto offline de IP pode permanecer pós-MVP.

### #80

HTML self-contained é útil, mas deve ser capaz de renderizar:

- scan sem logs;
- `diagnoses: []`;
- ausência de timeline;
- apenas filesystem/content findings.

Remova blockers de host/logs quando não forem necessários.

Timeline deve ser seção opcional.

### #81

PDF continua opcional/pós-MVP.

### E14

Runtime HTTP ativo é pós-1.0/P3.

Não deve bloquear logs locais nem scanner.

### E15

IA pós-1.0/P3, opt-in.

---

# 15. Corrija inconsistências documentais concretas

Audite todos os links e referências.

Verifique:

- Epic existente mas ausente do roadmap;
- Epic renomeada na Issue mas com nome antigo no roadmap;
- Issue com teste inexistente;
- referência a ADR inexistente;
- milestone/fase descrita com nome diferente em documentos;
- labels parent/child conflitantes;
- checkboxes de slices já concluídas;
- README descrevendo versão antiga;
- `ESTADO_ORQUESTRATOR.md` com data/branch incorreta;
- docs dizendo que algo está “planejado” quando já está implementado;
- docs dizendo que algo existe quando ainda é apenas Issue;
- versão do produto versus schema version versus scanner version.

Não invente estado para fechar inconsistência. O checkout testado é a prova do que existe.

---

# 16. Regras para novas Epics a partir deste ponto

Toda Epic nova deve conter no corpo:

```markdown
## Product Charter

- Horizonte: A | B | C | D | E
- Capacidade principal: filesystem | content-analysis | platform-adapter | reporting | enrichment | acquisition | AI
- Por que pertence ao WIRS:
- Por que agora:
- O que não depende desta Epic:
- Não-objetivos:

## Upstream documental

- Product Charter:
- Master Spec:
- ADRs:
- Architecture:
- Case study/future vision, se houver:

## Exit condition

- comportamento verificável;
- Coverage;
- Evidence/provenance;
- segurança;
- documentação afetada.
```

Toda slice deve declarar qual capability concreta entrega ao usuário.

---

# 17. Gate anti-deriva para novas features

Inclua em `AGENTS.md` um gate curto.

Antes de criar Epic/Issue de feature, responder:

1. Isso ajuda o WIRS a encontrar/priorizar arquivos/código suspeito?
2. Isso melhora integridade, Evidence, Finding, Coverage, Diagnosis ou report?
3. É requisito para scanner local funcionar?
4. Pode ser um provider/adapter opcional em vez de entrar no core?
5. Está bloqueando uma capacidade central sem necessidade?
6. É derivado de um único incidente real? Se sim, foi generalizado?
7. Existe forma de entregar valor sem rede/daemon/infra adicional?
8. Qual horizonte do Product Charter?
9. O que acontece quando esta feature não está disponível?
10. Coverage representa honestamente essa ausência?

Se as respostas indicarem produto lateral, mover para Future Vision ou horizonte posterior.

---

# 18. Verificação técnica da arquitetura atual

Sem implementar novas features, revise o código para confirmar:

- `domain/` continua sem imports de plataforma;
- adapters carregam semântica de WordPress/PHP;
- detectors recebem bytes/Artifacts e não fazem I/O arbitrário;
- providers são opcionais;
- `ArtifactReader` continua centralizando leitura/budget;
- YARA não acessa `filepath=` do target diretamente;
- findings/evidence usam identidade canônica;
- report não reinventa dados;
- CLI é composition root;
- read-only é preservado;
- baseline confiável pode reduzir falso positivo;
- arquivo não verificado não é absolvido;
- content analysis continua funcionando em custom/premium;
- o design permite PHP Generic sem bifurcar todo o engine.

Registre qualquer divergência como issue, não a esconda.

---

# 19. Saídas obrigatórias desta auditoria

Ao terminar, entregue no repositório:

1. `docs/PRODUCT-CHARTER.md`
2. `docs/DOCUMENTATION-MATRIX.md`
3. `docs/README.md` atualizado
4. `AGENTS.md` atualizado
5. `ORCHESTRATOR-ROADMAP.md` corrigido
6. `ESTADO_ORQUESTRATOR.md` atualizado
7. `README.md` corrigido onde necessário
8. `WIRS_MASTER_SPEC_PT-BR.md` corrigido somente onde conflitar com a direção aprovada
9. `docs/ARCHITECTURE.md` alinhado
10. `CONTEXT.md` somente se o vocabulário precisar mudar
11. `docs/ENTENDENDO-O-WIRS.md` preservando caráter didático e refletindo apenas features reais
12. `docs/future/WIRS-MELHORIAS.md` ou equivalente
13. `docs/case-studies/ANFAMOTO-GAPS.md` ou equivalente
14. Epics/Issues/labels/dependências realinhados
15. relatório de auditoria, por exemplo:

```text
docs/audits/PRODUCT-REALIGNMENT-2026-09.md
```

---

# 20. Estrutura obrigatória do relatório de auditoria

Use:

```markdown
# Product Realignment Audit

## Baseline
- branch:
- commit:
- data:
- issues analisadas:
- documentos analisados:
- módulos de código analisados:

## North Star validada

## O que já estava correto

## Drifts encontrados

| ID | Local | Tipo | Evidência | Impacto | Ação |
|---|---|---|---|---|---|

Tipos:
- PRODUCT_DRIFT
- PRIORITY_DRIFT
- DEPENDENCY_DRIFT
- DOC_DRIFT
- ISSUE_DRIFT
- IMPLEMENTATION_DRIFT
- DEAD_REFERENCE
- FUTURE_PROMOTED_TOO_EARLY

## Mudanças feitas

## Issues repriorizadas

| Issue | Antes | Depois | Motivo | Dependências corrigidas |
|---|---|---|---|---|

## Documentos atualizados

## Itens preservados deliberadamente

## Dívidas não corrigidas nesta auditoria

## Próxima DAG recomendada

## Verification
```

---

# 21. Próxima DAG: não escolha antes da auditoria

Não conclua previamente que “logs” ou “Incident Bundle” são a próxima fase.

Após o realinhamento, calcule a próxima DAG a partir de:

1. dependências reais;
2. Product Charter;
3. valor direto do scanner;
4. maturidade do código;
5. risco técnico.

A expectativa atual é que #65 e #66 permaneçam na frente, seguidos por capacidades file-centric, mas confirme contra o checkout.

---

# 22. Critérios de aceite do realinhamento

A tarefa só está pronta quando:

- [ ] existe uma North Star curta que todo agente lê;
- [ ] documentação tem responsabilidades sem sobreposição desnecessária;
- [ ] Future Vision não funciona como roadmap;
- [ ] Case Study não funciona como Product Spec;
- [ ] roadmap contém todas as Epics atuais;
- [ ] nomes/estados de Epic no roadmap batem com GitHub;
- [ ] nenhuma referência obrigatória aponta para arquivo/ADR/teste inexistente;
- [ ] PHP Generic local não depende de logs/SSH/Incident Bundle sem razão técnica;
- [ ] HTML/reporting básico não depende de logs host-centric;
- [ ] existe caminho de Diagnosis file-centric;
- [ ] E16/E17 estão posicionadas como enriquecimento opcional, não fundação;
- [ ] SSH está explicitamente longo prazo;
- [ ] IA está explicitamente fora do pipeline determinístico;
- [ ] WordPress continua primeiro adapter e prioridade;
- [ ] plugins premium/custom continuam analisados mesmo sem baseline;
- [ ] content analysis é tratado como capability central;
- [ ] issues P0/P1 refletem o scanner que queremos construir;
- [ ] prioridades parent/child são coerentes ou justificadas;
- [ ] `ESTADO_ORQUESTRATOR.md` reflete o momento atual;
- [ ] matrix documental foi preenchida;
- [ ] documentação e Issues não prometem feature inexistente;
- [ ] QA documental final aprovou o conjunto.

---

# 23. Restrições de execução

- Não apague histórico útil.
- Não feche Epic pai sem autorização explícita.
- Não altere comportamento do scanner só para fazer documentação “bater”.
- Não adicione dependência externa desnecessária.
- Não exponha dados reais de incidentes em fixtures.
- Não copie IPs, paths ou secrets identificáveis para testes públicos.
- Não crie dezenas de novas Issues antes de reutilizar/reclassificar as atuais.
- Não invente ADR para justificar decisão que ainda não foi tomada.
- Não transforme hipótese desta mensagem em fato: valide no repositório.
- Não conclua a tarefa com “documentação atualizada” sem mostrar matriz antes/depois.

---

# 24. Forma de trabalhar

Faça a auditoria em etapas e registre progresso.

Primeiro leia e inventarie.

Depois apresente internamente a matriz de drift.

Só então edite documentos/Issues.

Depois rode QA de consistência.

Se uma mudança de semântica for irreversível ou realmente ambígua, use HITL. Para correções evidentes de drift documental, prioridade incoerente, referência impossível ou dependência desnecessária, corrija diretamente e documente.

A meta não é reduzir ambição do WIRS. É impedir que a ambição futura destrua a clareza do produto atual.

O WIRS pode futuramente ler logs, enriquecer IPs, acessar hosts remotos e usar IA.

Mas primeiro ele precisa ser excelente em uma tarefa:

> **apontar uma aplicação web para o scanner e receber de volta uma investigação reproduzível, priorizada e explicável dos arquivos e códigos que realmente merecem atenção.**
