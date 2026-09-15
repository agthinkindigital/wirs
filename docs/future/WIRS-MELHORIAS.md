# Melhorias no WIRS — Evolução do Scanner de Segurança de Aplicações Web

> **Tipo documental:** Future Vision / evolução de produto
> **Autoridade:** não normativa; não substitui Product Charter, Master Spec, ADRs, Roadmap ou Issues.
> **Regra:** não redefine o Roadmap automaticamente.
> **Objetivo:** registrar melhorias que aumentem a capacidade do WIRS de localizar, priorizar, explicar e correlacionar artifacts suspeitos sem transformar o projeto prematuramente em SIEM/XDR/SOAR.
>
> Este documento incorpora aprendizados de incidentes reais, inclusive ANFAMOTO, mas nenhum incidente isolado redefine a tese de produto.

---

## 0. Tese de produto

O WIRS deve evoluir como um:

> **scanner read-only de segurança, integridade e código suspeito para aplicações web, WordPress-first, com core genérico para PHP e outros CMS/frameworks.**

A função principal é reduzir uma análise manual de milhares de arquivos para um conjunto pequeno de artifacts que merecem investigação humana.

O scanner deve responder:

- o que existe no target;
- o que deveria existir;
- o que mudou;
- o que apareceu sem baseline;
- onde existe conteúdo executável inesperado;
- onde existem IOCs, assinaturas ou cadeias suspeitas;
- quais sinais se reforçam;
- qual a confiança e a severidade;
- o que não pôde ser analisado;
- quais artifacts o profissional deve revisar primeiro.

### O WIRS não promete

- “site 100% limpo”;
- remoção automática de malware;
- autoria de ataque;
- atribuição de pessoa por IP;
- certeza probabilística fabricada;
- cobertura que não executou.

---

## 1. O que o incidente ANFAMOTO ensinou sem redefinir o produto

O caso ANFAMOTO expôs duas classes diferentes de melhoria.

### 1.1 Lições centrais para o scanner de arquivos

Estas pertencem diretamente ao produto:

| Lição | Generalização para o WIRS |
|---|---|
| PHP malicioso pode existir fora de WordPress | PHP Generic precisa compartilhar o mesmo core de Artifact/Evidence/Finding |
| Código malicioso pode existir em plugin/custom code sem baseline oficial | Content analysis nunca pode depender apenas de `HASH_MISMATCH` |
| PHP em diretórios estáticos é contexto forte | Zones/policies precisam existir fora do WordPress |
| `.htaccess`, `.user.ini`, `index.php` e configs podem carregar persistência/cloaking | Arquivos especiais/config devem receber regras próprias |
| Webshell pode estar escondida longe do início do arquivo | Content analysis precisa de estratégia bounded que não dependa somente do `head` |
| Arquivo “igual ao pacote recebido” ainda pode ser malicioso | Baseline prova integridade contra uma referência, não benignidade absoluta |
| Vários sinais no mesmo artifact aumentam valor investigativo | Diagnosis file-centric deve preceder correlação de logs |
| Backups/archives podem carregar versões comprometidas | Archive target local é útil, mas é uma forma de target, não o centro do produto |

### 1.2 Lições de enriquecimento forense

Estas são úteis, porém posteriores:

| Lição | Evolução futura |
|---|---|
| Logs revelaram sequência de autenticação/upload | ingestão opcional de logs locais |
| IP/ASN ajudaram a contextualizar eventos | enrichment offline opcional |
| Timeline melhorou a hipótese de ataque | Evidence temporal + Diagnosis temporal |
| A coleta exigiu SSH no caso real | remote target futuro, sem bloquear scanner local |
| Relatório manual consumiu tempo | HTML/PDF como views do artifact canônico |

A distinção é obrigatória: **arquivos/código são o núcleo; logs e rede enriquecem.**

---

## 2. Arquitetura-alvo coerente

```text
┌────────────────────────────────────────────────────────────────────┐
│                        WIRS CORE                                   │
│ Target → Inventory → Artifact → Evidence → Finding → Coverage      │
│                    ↓                                               │
│           Correlation / Diagnosis                                  │
└────────────────────────────────────────────────────────────────────┘
             ▲                     ▲
             │                     │
     ┌───────┴────────┐    ┌──────┴───────────┐
     │ Platform       │    │ Providers        │
     │ Adapters       │    │ opcionais        │
     ├────────────────┤    ├──────────────────┤
     │ WordPress      │    │ YARA             │
     │ PHP Generic    │    │ Wordfence futuro │
     │ Joomla futuro  │    │ Semgrep futuro   │
     │ outros CMS     │    │ threat intel     │
     └────────────────┘    └──────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────┐
│ REPORTING                                                          │
│ JSON canônico → Terminal / TUI / Markdown / HTML / PDF opcional   │
└────────────────────────────────────────────────────────────────────┘

Expansões laterais, não fundação:

logs locais → Evidence temporal ─────┐
archive/snapshot local ──────────────┤
SSH/SFTP futuro ─────────────────────┤→ mesmo modelo canônico
IP/ASN futuro ───────────────────────┤
AI AnalysisPacket futuro ────────────┘
```

---

## 3. Capacidade central nº 1 — Integridade

Integridade responde:

> “Este artifact corresponde a uma referência confiável?”

Estados úteis:

- `MATCH`;
- `MISMATCH`;
- `MISSING`;
- `UNEXPECTED`;
- `UNVERIFIED`;
- provider unavailable/failed refletido em Coverage.

### 3.1 WordPress Core

Quando versão/locale e provider confiável estiverem disponíveis:

```text
core atual
→ checksum upstream
→ arquivos verificados são absolvidos de heurística redundante
→ divergentes continuam no pipeline de content analysis
```

Isso reduz falsos positivos sem esconder alteração real.

### 3.2 Plugins e themes oficiais

O mesmo princípio deve valer por componente.

A integridade precisa distinguir:

- plugin oficial verificável;
- premium/custom com baseline do operador;
- premium/custom sem baseline;
- arquivo inesperado;
- arquivo ausente.

### 3.3 Premium/custom

Regra:

```text
SEM BASELINE ≠ MALICIOSO
SEM BASELINE ≠ PULAR
```

Sem baseline:

```text
UNVERIFIED
→ content analysis
→ YARA
→ IOC
→ heurísticas
→ policies
```

---

## 4. Capacidade central nº 2 — Content analysis

Este é um dos diferenciais que precisa amadurecer.

### 4.1 Não analisar apenas arquivos modificados

Existem dois caminhos independentes:

```text
integrity path
```

e:

```text
content-security path
```

O segundo continua necessário quando:

- não há baseline;
- artifact é custom;
- plugin é premium;
- artifact é unexpected;
- referência é apenas `UNVERIFIED_REFERENCE`;
- a plataforma não oferece checksums.

### 4.2 Heurísticas combinadas

Sinais que podem ser observados:

#### Execução dinâmica

- `eval`;
- `assert`;
- `create_function`;
- dynamic function calls;
- backticks.

#### Encoding/ofuscação

- `base64_decode`;
- `gzinflate`;
- `str_rot13`;
- `hex2bin`;
- `urldecode`;
- literais codificados extensos;
- entropia anormal, se medida com regra auditável.

#### Process execution

- `shell_exec`;
- `exec`;
- `system`;
- `passthru`;
- `popen`;
- `proc_open`;
- `pcntl_exec`.

#### Arquivo/rede

- escrita de arquivo;
- upload;
- `curl`;
- sockets;
- download remoto;
- criação/movimentação de payload.

Um sinal isolado deve ter pouco peso.

Uma cadeia possui outro significado:

```text
encoding
+ dynamic execution
+ process/file/network
```

### 4.3 Profundidade de leitura

O MVP atual pode usar `head` para checks baratos, mas a evolução precisa impedir o falso negativo óbvio:

> backdoor localizado depois da janela inicial do arquivo.

A estratégia futura deve ser bounded e compatível com profile:

- streaming;
- multi-window;
- full scan para tipos/tamanhos elegíveis;
- budgets explícitos;
- Coverage `PARTIAL` quando truncado;
- sem carregar arbitrariamente arquivos gigantes em memória.

### 4.4 MIME/conteúdo/extensão

Melhorias úteis:

- PHP com extensão de imagem;
- conteúdo executável em zonas não executáveis;
- extensão inocente com shebang/PHP/script;
- arquivo binário disfarçado;
- archive em local sensível.

---

## 5. Capacidade central nº 3 — YARA e signatures

YARA deve ser um provider opcional, mas de primeira classe no scan.

Contrato:

- ausência → `UNAVAILABLE`;
- erro → Coverage honesto;
- timeout → Coverage honesto;
- match → Evidence + Finding;
- rule/tags/namespace/provenance preservados;
- nenhuma execução do target;
- bytes fornecidos pelo reader/budget do WIRS;
- ruleset versionado;
- sem include externo em pack builtin.

### 5.1 Correlação desejada

```text
YARA match sozinho
→ finding de assinatura

YARA + mismatch oficial
→ hipótese muito forte

YARA + executable em uploads
→ hipótese muito forte

YARA + cadeia PHP suspeita
→ evidências independentes concordantes
```

---

## 6. WordPress como primeiro adapter forte

WordPress continua sendo o primeiro ecossistema a receber tratamento profundo.

### 6.1 Zonas

- core protected;
- root special;
- plugins;
- themes;
- MU-plugins;
- uploads;
- cache;
- upgrade;
- other.

### 6.2 Regras que fazem sentido

#### Core

- mismatch;
- missing;
- unexpected;
- config/root special suspeito.

#### Plugins/themes

- official baseline;
- operator baseline;
- `UNVERIFIED`;
- content analysis em custom/premium;
- arquivo inesperado;
- scripts ofuscados;
- payloads fora de expectativa.

#### MU-plugins

Merecem atenção contextual porque auto-carregam.

Posição não prova malware, mas aumenta relevância de finding de conteúdo.

#### Uploads

Executável/PHP é forte violação de expectativa.

#### Cache

Cache precisa:

- política própria;
- não gerar tempestade de falso positivo;
- poder ser escaneado como etapa adicional;
- nunca servir como desculpa para esconder artifact suspeito.

#### Configuração

Arquivos relevantes:

- `wp-config.php`;
- `.htaccess`;
- `.user.ini`;
- `php.ini`;
- outros arquivos sensíveis de raiz.

---

## 7. Diagnosis: primeiro sobre files, depois sobre atores/logs

O primeiro correlator deve operar sem depender de logs.

### DX-FILE-001 — alteração + assinatura

```yaml
requires:
  - integrity mismatch/unexpected
  - yara/signature no mesmo artifact
confidence: high
```

### DX-FILE-002 — zona incompatível + conteúdo suspeito

```yaml
requires:
  - executable em zona não executável
  - heuristic chain ou signature
confidence: high
```

### DX-FILE-003 — custom/unverified + múltiplos sinais

```yaml
requires:
  - artifact UNVERIFIED
  - heuristic high
  - IOC ou YARA
confidence: high
```

Diagnosis deve conter:

- basis;
- hipótese;
- alternativas;
- unknowns;
- próximos checks;
- confidence;
- referências resolvíveis.

Sem “score mágico 87%”.

---

## 8. Reporting

O JSON canônico é a fonte de verdade.

Dele derivam:

- terminal;
- TUI/Rich;
- Markdown;
- HTML;
- PDF opcional;
- SARIF futuro.

### 8.1 Um relatório útil precisa mostrar

- target;
- plataforma;
- profile;
- versão do scanner/schema;
- artifacts relevantes;
- findings;
- severidade;
- confiança;
- evidence;
- coverage;
- provider health;
- diagnoses;
- limitações;
- próximos checks.

### 8.2 HTML

HTML deve funcionar mesmo quando:

- não existem logs;
- `diagnoses` está vazio;
- não existe timeline;
- somente filesystem foi analisado.

Timeline e IPs são seções opcionais, nunca blockers do renderer.

---

## 9. PHP Generic — expansão natural

Depois do WordPress-first estar sólido:

```text
wirs scan ./legacy-php
```

deve funcionar sem Incident Bundle, SSH ou logs.

### 9.1 Discovery

Pode usar:

- presença de PHP real por conteúdo;
- `composer.json`;
- estrutura de webroot;
- sinais configurados;
- ausência de WordPress.

### 9.2 Zones genéricas

Exemplos:

```text
webroot-executable
static-assets
uploads
cache
vendor
config
unknown
```

A configuração pode declarar:

```text
img/
uploads/
assets/
```

como não executáveis.

### 9.3 Reuso

PHP Generic deve reutilizar:

- Artifact;
- Reader;
- IOC;
- heurísticas;
- YARA;
- Evidence;
- Finding;
- Coverage;
- Diagnosis;
- reporting.

Se exigir um segundo engine, a arquitetura está errada.

---

## 10. Outros CMS

A evolução posterior pode adicionar adapters:

- Joomla;
- Drupal;
- Laravel;
- PHP frameworks;
- outros.

Cada adapter acrescenta:

- discovery;
- zones;
- baselines disponíveis;
- policies;
- collectors específicos quando realmente necessários.

O core não aprende nomes de diretórios específicos da plataforma.

---

## 11. Archive e Snapshot locais

Archive é útil para:

- backups;
- perícia offline;
- comparação de versões;
- pacotes de plugin/theme;
- snapshots de incidente.

Requisitos:

- read-only;
- sem extração insegura;
- zip-slip protegido;
- symlink protegido;
- bomb limits;
- provenance;
- Coverage quando limites impedirem análise.

Não deve bloquear:

- WordPress local;
- PHP Generic local;
- reporting.

---

## 12. Logs locais — enriquecimento posterior

Quando arquivos de log forem fornecidos explicitamente:

```text
filesystem findings
       +
observed log events
       ↓
enriched Diagnosis
```

Exemplos:

- artifact suspeito foi solicitado via HTTP;
- upload observado para path depois detectado como webshell;
- mudança de credencial próxima a escrita de arquivo;
- erro PHP demonstra execução do artifact.

### 12.1 Princípios

- local/offline por padrão;
- streaming/bounded;
- `occurred_at` separado de `collected_at`;
- source/provenance;
- gaps de retenção → Coverage;
- evento observado não prova intenção;
- ausência de log não quebra scan de arquivos.

---

## 13. IP, ASN e User-Agent

Também são enriquecimento.

Podem ajudar a responder:

- origem de request;
- ASN;
- mesma rede;
- UA family;
- VPN/hosting/proxy context.

Nunca devem concluir:

```text
mesmo CIDR = mesma pessoa
```

ou:

```text
IP mal reputado = arquivo é malware
```

A função é contexto.

---

## 14. SSH/SFTP

SSH é longo prazo.

O design correto:

```text
LocalArtifactSource
RemoteArtifactSource
ArchiveArtifactSource
```

Todos alimentam o mesmo scanner.

SSH não deve criar:

- novo domínio;
- novo modelo de Finding;
- nova arquitetura de report;
- dependência obrigatória.

É acquisition seam.

---

## 15. IA

IA é análise auxiliar.

Fluxo:

```text
Canonical Report
→ redaction gate
→ bounded AnalysisPacket
→ LLM provider
→ summary / recommendations
```

Pode:

- explicar findings;
- resumir;
- sugerir próximos checks;
- sugerir remediação;
- comparar reports.

Não pode:

- inventar Evidence;
- alterar hash;
- transformar LOW em CRITICAL sem regra;
- modificar fatos determinísticos;
- receber secrets crus;
- ser requisito do scan.

---

## 16. O que não construir agora

Não priorizar:

- Kafka;
- Redis Streams como requisito;
- agents Go/Rust;
- inotify residente;
- mTLS agent fleet;
- dashboard Grafana obrigatório;
- bloqueio automático;
- WAF integration;
- playbooks de resposta automáticos;
- ML anomaly;
- RAG;
- vector database;
- SOAR.

Essas ideias podem ser revisitadas se o WIRS um dia ganhar produto de monitoramento separado.

---

## 17. Roadmap de evolução por horizonte

| Horizonte | Objetivo |
|---|---|
| A | Canonical artifact, YARA, content analysis, WordPress completo, Diagnosis file-centric, reporting |
| B | PHP Generic, outros adapters, archive/snapshot local |
| C | logs locais, timeline, Diagnosis temporal, IP/ASN offline |
| D | SSH/SFTP, remote targets, threat intel APIs, scheduling/fleet |
| E | AI AnalysisPacket e assistência |

### Regra

Nenhuma capability C/D/E deve bloquear A/B sem uma necessidade técnica demonstrável.

---

## 18. KPIs coerentes com o produto

Métricas centrais:

| Métrica | Objetivo |
|---|---|
| Redução de massa manual | transformar milhares de artifacts em shortlist investigável |
| Recall em fixtures maliciosas conhecidas | minimizar falso negativo silencioso |
| Falso positivo em trees limpas | baixo e explicável |
| Coverage | sempre explícito |
| Reprodutibilidade | mesmo input/config → resultado semanticamente estável |
| Performance | profiles seguros para hosting compartilhado/VPS |
| Provenance | todo finding explicável |
| Referencialidade | refs canônicas resolvem |
| Segurança | scanner não executa nem modifica target |

Métricas como MTTD/MTTR contínuo, eventos/s e cobertura de SOC pertencem a um produto de monitoramento, não ao scanner CLI atual.

---

## 19. Critério para aceitar uma nova melhoria

Antes de promover uma ideia ao roadmap:

1. melhora detecção/priorização de artifacts?
2. melhora Evidence/Finding/Coverage/Diagnosis?
3. é necessária ao scanner local?
4. cabe em provider/adapter opcional?
5. está generalizada além de um incidente?
6. qual o falso positivo esperado?
7. qual Coverage existe quando não roda?
8. qual horizonte?
9. bloqueia feature mais central?
10. exige nova infraestrutura sem necessidade?

Se a resposta indicar produto lateral, registrar em Future Vision e não promover.

---

## 20. Aplicação ao ANFAMOTO

O caso continua valioso.

O objetivo correto não é:

> “automatizar 100% da perícia ANFAMOTO agora”.

O objetivo é:

> “usar o caso para provar que o WIRS encontra e prioriza artifacts que obrigariam inspeção manual, e guardar logs/IP/timeline como enriquecimentos progressivos.”

Primeiro:

```text
snapshot/site
→ inventory
→ PHP Generic/WordPress
→ integrity quando houver baseline
→ content analysis
→ YARA
→ findings
→ file-centric diagnosis
→ report
```

Depois, se logs estiverem disponíveis:

```text
logs locais
→ Evidence temporal
→ relações
→ Diagnosis enriquecido
```

---

## 21. Resultado estratégico

O diferencial do WIRS deve ser:

> **combinar integridade confiável, análise de conteúdo, contexto de plataforma, signatures, Coverage e correlação explicável para indicar exatamente onde o profissional deve investigar.**

Esse foco permite crescer para PHP genérico, outros CMS, logs, remote targets e IA sem reconstruir o produto em cada fase.

---

*Documento vivo — versão 2.0 de direcionamento — realinhado ao objetivo do scanner de arquivos/código.*
