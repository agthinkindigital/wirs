# WIRS — Caso ANFAMOTO como validação do scanner e fonte de gaps

> **Tipo documental:** Case Study / gap analysis
> **Autoridade:** não normativa; este caso não redefine Product Charter nem reordena Roadmap sozinho.
> **Objetivo:** registrar o que o incidente ANFAMOTO ensinou ao WIRS, separar gaps centrais do scanner de enriquecimentos forenses futuros e fornecer um caso de validação realista.
>
> Regra de leitura: **ANFAMOTO é um laboratório de requisitos; não é a definição do produto WIRS.**

---

## 0. Veredito

O incidente mostrou que o WIRS precisa ficar melhor em sua tarefa principal:

> **examinar filesystem/código de uma aplicação e reduzir milhares de artifacts a uma shortlist explicável de arquivos que merecem investigação.**

O caso também mostrou que logs, IPs e timeline aumentam a confiança de uma investigação, mas isso pertence a uma camada posterior de enriquecimento.

Portanto, o resultado do caso não deve ser:

> “WIRS precisa virar scanner de hospedagem.”

A conclusão correta é:

> “WIRS precisa amadurecer como scanner de aplicações web e permitir, futuramente, que telemetria local enriqueça os mesmos Evidence/Findings/Diagnoses.”

---

## 1. O que o WIRS já faria bem no caso

| Capacidade | Valor no caso |
|---|---|
| SafePath + inventory | mapear a árvore sem seguir symlink perigoso |
| ArtifactReader + budgets | analisar com controle de I/O |
| Baseline/operator manifest | comparar árvore/pacote limpo com árvore suspeita |
| WordPress integrity | identificar alteração/extra em core/plugins quando aplicável |
| WordPress zones | dar contexto para uploads/cache/root |
| IOC streaming | procurar indicadores conhecidos |
| PHP heuristics | localizar cadeias de execução/ofuscação |
| YARA provider | identificar webshell/dropper por assinatura quando integrado ao scan |
| Evidence/Finding/Coverage | explicar o que foi encontrado e o que ficou sem cobertura |
| JSON canônico | permitir report reproduzível |
| profiles | limitar impacto em ambiente compartilhado |

A principal lacuna atual não é “não existe SSH”.

A principal lacuna é consolidar tudo isso num scan canônico completo, aprofundar content analysis e expandir o mesmo engine para PHP genérico.

---

## 2. O que a perícia manual revelou

As tarefas manuais do caso podem ser classificadas.

### 2.1 Diretamente ligadas ao scanner

| Trabalho manual | Gap generalizável |
|---|---|
| comparar árvores/backups | archive/snapshot local + baseline |
| localizar PHP suspeito fora de WordPress | PHP Generic |
| revisar `eval/base64/...` | heurística/content analysis |
| verificar webshells | YARA/signatures |
| revisar `.htaccess`/`index.php` | regras de config/cloaking |
| procurar executável em diretório estático | generic zones/policies |
| decidir quais arquivos olhar primeiro | correlation/Diagnosis file-centric |
| montar lista priorizada | reporting |

### 2.2 Enriquecimento forense

| Trabalho manual | Gap posterior |
|---|---|
| parse cPanel | collector local opcional |
| parse Apache/Nginx | log Evidence temporal |
| cruzar horários | correlation temporal |
| analisar IP/ASN/UA | enrichment offline |
| montar timeline | report enriquecido |

### 2.3 Aquisição/operação

| Trabalho manual | Classificação |
|---|---|
| entrar via SSH para coletar material | acquisition seam futuro |
| mover/quarentenar arquivos | remediação; fora do `scan` |
| bloquear IP | resposta; fora do `scan` |
| revogar sessão | resposta; fora do `scan` |

---

## 3. Gaps prioritários — eixo correto

### GAP-A01 — Artifact canônico completo

Antes de avançar em novas fontes, o scan precisa preservar:

- Scan Manifest;
- Target;
- Artifacts;
- Evidence;
- Findings;
- Coverage;
- provider status/runs;
- `diagnoses: []`;
- referências canônicas resolvíveis;
- redaction final.

Isto é base para qualquer relatório ou correlação posterior.

### GAP-A02 — YARA integrado ao scan

O provider existe, mas o valor de produto aparece quando participa do pipeline real.

Requisitos:

- builtin pack;
- status do provider;
- Coverage em ausência/falha/timeout;
- Evidence;
- Finding;
- artifact ref canônica;
- rule/tags/namespace/provenance;
- sem execução do target.

### GAP-A03 — Content analysis que encontra backdoor fora do início do arquivo

Heurística baseada apenas em uma janela inicial é útil como fast path, mas não pode ser a estratégia final.

Planejar uma política bounded:

- arquivos elegíveis → streaming/full content;
- arquivos grandes → janelas/budget;
- profile define limites;
- truncation → Coverage `PARTIAL`;
- nunca carregar arbitrariamente arquivo gigante.

Objetivo:

> um backdoor escondido no final de plugin/custom PHP ainda deve poder ser encontrado.

### GAP-A04 — WordPress completo

O caso reforça a necessidade de terminar primeiro adapter antes de desviar para host telemetry.

Prioridades:

- core;
- plugins oficiais;
- plugins premium/custom;
- themes;
- MU-plugins;
- uploads;
- cache;
- root special/config;
- baselines;
- content analysis sempre que não houver absolvição confiável.

### GAP-A05 — Detectores/config de aplicação

Melhorias úteis para arquivos:

- `.htaccess` com rewrite/cloaking suspeito;
- `.user.ini`/`php.ini` com auto prepend/append suspeito;
- PHP em zona estática;
- extensão × conteúdo incompatíveis;
- chains de download + write + execute;
- criação/alteração de usuário/admin quando detectável estaticamente;
- payloads externos;
- scripts altamente ofuscados.

Cada regra deve declarar falsos positivos e não transformar palavra-chave isolada em veredito.

### GAP-A06 — Diagnosis file-centric

Antes de SessionActor:

```yaml
diagnosis: DX-FILE-001
requires:
  - trusted integrity mismatch
  - yara match no mesmo artifact
confidence: high
```

Outro exemplo:

```yaml
diagnosis: DX-FILE-002
requires:
  - executable em static/uploads
  - php heuristic chain
confidence: high
```

Isso já reduz trabalho do analista sem nenhum log.

### GAP-A07 — Reporting útil sem telemetria

HTML deve conseguir representar:

- scope;
- findings;
- evidence;
- severity/confidence;
- coverage;
- diagnoses;
- limitations;
- próximos checks.

Timeline é opcional.

PDF é posterior e deriva do HTML.

---

## 4. PHP Generic — gap central revelado pelo caso

O incidente tinha PHP legado fora do WordPress.

Logo:

```text
wirs scan ./site-php-legado
```

precisa ser um objetivo natural.

### 4.1 Não depender de Incident Bundle

Para uma pasta local:

- não exigir manifest de bundle;
- não exigir logs;
- não exigir SSH.

O adapter deve descobrir e classificar o target usando conteúdo/configuração.

### 4.2 Zones

Exemplo:

```text
webroot-executable
static
uploads
cache
vendor
config
unknown
```

O operador pode declarar:

```text
img/
uploads/
assets/
```

como áreas onde execução não é esperada.

### 4.3 Reusar o engine

Nada de criar scanner paralelo.

Reusar:

- inventory;
- reader;
- IOC;
- heuristics;
- YARA;
- Evidence;
- Finding;
- Coverage;
- Diagnosis;
- report.

---

## 5. Archive local — útil, mas independente

No caso real havia backups ZIP.

Isso justifica:

```text
wirs scan ./backup.zip
```

ou uso como fonte local.

Mas archive não deve virar pré-condição para PHP Generic.

Requisitos:

- traversal protegido;
- symlink protegido;
- bomb limits;
- nested archive policy;
- provenance;
- Coverage;
- read-only.

---

## 6. Logs locais — camada opcional posterior

Depois do scanner file-centric:

```text
wirs scan ./site \
  --access-log ./logs/access.log \
  --php-error-log ./logs/error.log
```

ou modelo equivalente pode enriquecer a mesma execução/bundle.

### 6.1 Evidence temporal

Um registro deve distinguir:

```text
occurred_at
collected_at
source
source_locator
artifact/path relacionado quando resolvível
```

### 6.2 Coverage temporal

Informar:

- primeiro/último evento;
- rotações presentes;
- intervalo ausente;
- linhas inválidas;
- parser loss;
- timezone.

Gap de log é Coverage, não malware.

---

## 7. Collectors de hospedagem

cPanel/Apache/Nginx/PHP log continuam válidos como adapters/collectors opcionais.

Eles não são prioridade do núcleo.

Exemplos futuros:

- File Manager upload/edit/download;
- auth/session;
- Apache/Nginx request;
- PHP error/runtime observation.

Regra:

> collector registra fato observado; regra/Diagnosis interpreta.

Nunca:

```text
upload = ataque
```

automaticamente.

---

## 8. Relações temporais e ator

Futuro:

```text
same account
same path
same artifact
same session
same cidr
same ua family
time window
```

Mas:

```text
same CIDR != same actor
same UA != same actor
```

Correlation deve declarar a chave usada.

---

## 9. Contexto offline de IP

GeoIP/ASN/UA pode ajudar depois.

Saída:

- IP normalizado;
- CIDR;
- ASN;
- country;
- UA family;
- limitations/provenance.

Não produzir autoria.

Base ausente:

```text
UNAVAILABLE
```

e o scan segue.

---

## 10. SSH não é requisito do caso de scanner

A perícia manual usou SSH porque os dados estavam no servidor.

Isto não significa que o WIRS precise de SSH para ser útil.

Sequência correta:

```text
primeiro:
material local → scanner

depois:
SSH/SFTP → forma opcional de adquirir material → mesmo scanner
```

Remote target deve ser longo prazo.

---

## 11. IA não é detector

Depois do canonical report:

```text
report
→ redaction
→ AnalysisPacket
→ LLM
```

Uso:

- resumo;
- próximos checks;
- explicação;
- recomendação.

Não usar como Evidence.

---

## 12. Ordem de implementação recomendada após o realinhamento

Não tratar esta tabela como substituta do Roadmap; ela é a leitura do case study.

| Ordem | Capacidade | Relação com ANFAMOTO |
|---:|---|---|
| 1 | canonical artifact | preserva cadeia de prova |
| 2 | YARA no scan | webshell/signatures |
| 3 | content analysis profundo/bounded | código escondido em plugins/files |
| 4 | WordPress completo | primeiro adapter forte |
| 5 | Diagnosis file-centric | shortlist mais confiável |
| 6 | reporting HTML | investigação e entrega |
| 7 | PHP Generic | cobre legado do caso |
| 8 | archive local | cobre backups |
| 9 | logs locais | enriquece sequência do incidente |
| 10 | Diagnosis temporal | cruza filesystem + logs |
| 11 | IP/ASN offline | contexto |
| 12 | remote/SSH | aquisição futura |
| 13 | AI | assistência futura |

---

## 13. Realinhamento sugerido das Epics/Issues atuais

Validar sempre contra o GitHub antes de editar.

### #65

Manter na frente.

É a base do modelo canônico.

### #66

Manter logo após #65.

YARA é parte central de content/signature analysis.

### E06

Não esperar logs/host correlation para completar melhorias file-centric de WordPress.

### E09

Criar ou reposicionar uma primeira slice de Diagnosis sobre o mesmo Artifact.

As slices de credencial/cPanel/phishing com logs passam para etapa posterior da própria Epic ou subfase.

### E12

Incident Bundle/archive local pode permanecer, mas:

- não bloquear PHP Generic;
- SSH permanece adiado.

### #70 / E13

Remover dependência de Incident Bundle se o primeiro scan é sobre diretório local.

### E16/E17

Preservar, porém classificar como enriquecimento posterior.

Não tratar como requisito para MVP do scanner.

### #76/#77/#78

São úteis para fase temporal/host, mas não devem representar o primeiro correlator.

### #79

Pós-MVP é coerente.

### #80

HTML deve depender do canonical model e, opcionalmente, de Diagnosis file-centric.

Não deve exigir logs para renderizar.

### #81

PDF opcional e posterior.

---

## 14. Critério de sucesso do caso ANFAMOTO — versão correta

Não exigir que o WIRS reproduza toda a investigação automaticamente.

### Etapa 1 — scanner

Dado material local do site:

```bash
wirs scan ./snapshot-ou-site --profile soft --report ./scan.json
```

Sucesso se o report conseguir:

- inventariar corretamente;
- identificar divergências quando houver baseline;
- identificar artifacts inesperados;
- encontrar cadeias PHP suspeitas;
- encontrar YARA/signatures quando provider disponível;
- destacar executável em zonas incompatíveis;
- produzir shortlist;
- mostrar Coverage;
- explicar refs;
- gerar Diagnosis file-centric quando sinais se reforçarem.

### Etapa 2 — expansão PHP

O mesmo cenário deve funcionar sem WordPress.

### Etapa 3 — archive

Opcionalmente ler backup local.

### Etapa 4 — logs

Quando logs forem fornecidos:

- criar Evidence temporal;
- relacionar request/upload/path;
- enriquecer Diagnosis;
- registrar gaps de retenção.

### Etapa 5 — IP

Contexto offline opcional.

---

## 15. O que NÃO faz parte do critério primário

Não exigir agora:

- classificar dezenas de milhares de IPs;
- provar credential takeover;
- acessar servidor por SSH;
- rodar agente residente;
- bloquear IP;
- quarentenar arquivo;
- revogar sessão;
- gerar playbook automático;
- operar Kafka/Redis;
- dashboard Grafana;
- reproduzir toda timeline histórica;
- inferir patient zero.

Essas capacidades pertencem a outros horizontes.

---

## 16. Valor do case study

ANFAMOTO continua sendo um excelente teste porque contém:

- WordPress;
- PHP legado;
- arquivos adulterados;
- webshell;
- ofuscação;
- config/rewrite;
- archives;
- logs;
- sequência temporal.

Ele deve inspirar fixtures **sintéticas**, nunca copiar material real.

O case study serve para perguntar:

> “Se eu tivesse o WIRS naquele dia, quais horas de inspeção arquivo por arquivo ele teria eliminado?”

Essa é a métrica principal.

---

## 17. Resultado esperado no longo prazo

Quando todas as camadas existirem:

```text
files
+ integrity
+ content analysis
+ signatures
+ platform context
+ logs opcionais
+ IP context opcional
         ↓
Evidence
         ↓
Findings
         ↓
Diagnoses
         ↓
report forense
```

Mas a base continua sendo o scanner.

---

*Documento vivo — versão 3.0 de realinhamento — ANFAMOTO como case study, não como Product Charter.*
