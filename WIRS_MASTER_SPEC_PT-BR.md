# WIRS — WordPress Incident Response Scanner

## Especificação Mestra de Produto, Segurança, Arquitetura, TDD, QA e Entrega

**Nome de trabalho:** WIRS — WordPress Incident Response Scanner  
**Direção arquitetural:** core genérico de Incident Response Scanner + adapter WordPress  
**Status do documento:** baseline de engenharia / especificação viva  
**Linguagem principal do MVP:** Python 3.11+  
**Modelo de execução principal:** read-only, evidence-first, deterministic-first  
**Alvos iniciais:** hosts Linux, hospedagem compartilhada com SSH quando possível, VPS/KVM, snapshots locais e filesystems montados  
**Direção de longo prazo:** aplicações PHP, CMSs, frameworks, web roots Linux, containers e outros runtimes sem acoplamento do engine ao WordPress.

---

# 0. Resumo Executivo

O WIRS não deve ser tratado como “mais um antivírus para WordPress”. O produto deve nascer como um **motor de scanning para resposta a incidentes, integridade e orquestração de evidências**, capaz de responder de forma reproduzível a perguntas como:

- Quais arquivos diferem de uma origem confiável?
- Quais arquivos existem em locais onde não deveriam existir?
- Quais componentes não puderam ser verificados porque não existe baseline confiável?
- Quais arquivos apresentam indicadores conhecidos, estruturas suspeitas ou padrões perigosos de execução?
- Quais regiões do alvo foram efetivamente analisadas e quais ficaram sem cobertura?
- Quais mecanismos de persistência existem na aplicação, runtime ou host?
- Quais registros de banco de dados merecem investigação por conter código, referências externas ou IOCs?
- Quais conclusões são fatos determinísticos e quais são apenas heurísticas?
- Quais findings, quando correlacionados, sustentam uma hipótese de diagnóstico?
- Um segundo analista consegue reproduzir a conclusão sem confiar em uma decisão opaca de modelo de IA?

O primeiro adapter será WordPress porque o ecossistema fornece primitives fortes para análise determinística: checksums oficiais de core, checksums de plugins do repositório oficial, WP-CLI, estrutura de diretórios previsível e amplo histórico de técnicas de comprometimento. Porém, o **core do scanner não deve conhecer `wp-admin`, `wp-content`, Elementor, WooCommerce ou qualquer conceito específico de WordPress**.

Esses conceitos pertencem a adapters e rule packs.

A forma arquitetural pretendida é:

```text
Core genérico do scanner
    + descoberta de alvo
    + inventário de artefatos
    + coleta de evidências
    + baseline providers
    + regras determinísticas
    + detectores heurísticos
    + analyzers externos opcionais
    + correlação / diagnóstico
    + reporting
        └── platform adapters
              ├── WordPress
              ├── PHP Generic
              ├── Laravel
              ├── Joomla
              ├── Linux Web Host
              └── futuros adapters
```

O MVP deve ser útil antes de ser sofisticado. A primeira versão funcional precisa conseguir apontar para uma instalação ou snapshot WordPress, inventariar os arquivos, verificar integridade oficial quando possível, encontrar arquivos inesperados, aplicar políticas de diretório, procurar IOCs, executar um pequeno pacote heurístico/YARA e produzir findings estruturados com cobertura explícita.

A evolução posterior deve ampliar capacidades sem quebrar os contratos centrais do MVP.

---

# 1. Tese de Produto

## 1.1 Problema que o produto resolve

Uma investigação de comprometimento em aplicações web normalmente é uma coleção de comandos e ferramentas desconectadas:

- ferramenta de integridade identifica divergência de arquivo;
- engine de assinatura procura malware conhecido;
- SAST entende sintaxe e fluxo de código;
- CLI do CMS expõe estado da aplicação;
- banco de dados contém configuração e payload persistido;
- scanner HTTP observa comportamento de runtime;
- analista tenta correlacionar manualmente tudo isso.

O diferencial do WIRS não deve ser inventar mais um detector isolado. O valor está em **normalizar, preservar proveniência, medir cobertura, classificar confiança e correlacionar evidências heterogêneas**.

## 1.2 Resultado esperado de um scan

Um scan deve produzir três categorias distintas:

### 1. Fatos

Observações determinísticas e reproduzíveis.

Exemplos:

- SHA-256 calculado;
- checksum oficial divergente;
- arquivo esperado ausente;
- arquivo extra em uma zona protegida;
- IOC literal encontrado;
- permissão/owner de arquivo;
- versão de componente;
- provider disponível ou indisponível.

### 2. Suspeitas

Findings heurísticos, com possibilidade real de falso positivo.

Exemplos:

- código altamente ofuscado;
- execução dinâmica combinada com decoding;
- PHP em diretório destinado a mídia;
- string com alta entropia;
- configuração de persistência anômala;
- arquivo executável disfarçado por extensão.

### 3. Diagnósticos

Hipóteses derivadas da correlação entre fatos e suspeitas.

Exemplo:

```text
Arquivo pertencente ao core diverge do baseline oficial
+ mesmo arquivo corresponde a assinatura de malware
+ mesma modificação ocorreu junto a outro artefato suspeito
= hipótese forte de adulteração maliciosa do componente
```

O produto nunca deve colapsar essas três categorias em um simples:

```text
INFECTADO
```

sem explicar o porquê.

## 1.3 Não objetivos do MVP

O MVP não deve ser:

- removedor automático de malware;
- EDR;
- daemon residente;
- WAF;
- framework de exploração de vulnerabilidades;
- substituto integral de Wordfence, WPScan, YARA, Semgrep ou WP-CLI;
- agente autônomo baseado em LLM;
- suíte completa de forense de sistema operacional;
- plataforma de engenharia reversa binária;
- ferramenta que “garante que o site está limpo”.

A restrição é estratégica. Esses limites tornam o MVP terminável, testável e seguro.

---

# 2. Princípios Centrais

## P1 — Read-only por padrão

Um scan não altera o alvo.

O fluxo normal não pode:

- apagar arquivo;
- renomear arquivo;
- colocar em quarentena;
- modificar permissão;
- desativar plugin;
- alterar banco;
- regenerar cache;
- reinstalar core;
- remediar finding.

Se remediation existir no futuro, deve ser outro subsistema, outra namespace de comandos e outro modelo de autorização.

## P2 — Evidência antes de interpretação

Um finding deve apontar para evidência verificável.

Ruim:

```text
Malware detectado: 94%.
```

Bom:

```text
Rule ID: WP.CORE.HASH_MISMATCH
Path: wp-includes/example.php
Baseline: WordPress 6.x pt_BR / upstream
Expected hash: ...
Actual hash: ...
Confidence: DETERMINISTIC
Evidence: ev_01...
```

## P3 — Determinístico antes de heurístico

Os checks mais baratos e confiáveis executam primeiro.

Ordem conceitual:

```text
inventory
→ metadata
→ hash/baseline
→ policies
→ IOCs
→ heurísticas
→ YARA/external analyzers
→ correlação
→ análise opcional por LLM
```

## P4 — Cobertura é um resultado de primeira classe

“Zero findings” não significa “limpo”.

O relatório precisa dizer:

- o que foi analisado;
- o que foi pulado;
- o que ficou ilegível;
- o que não possuía baseline;
- qual provider falhou;
- qual análise não foi executada;
- qual limite de tamanho impediu análise completa.

## P5 — Platform adapters, não contaminação do core

O domínio central conhece conceitos genéricos:

- Target;
- Artifact;
- Evidence;
- Finding;
- Diagnosis;
- Baseline;
- Provider;
- Rule;
- Coverage.

`wp-content`, `artisan`, `composer.lock`, Joomla e demais especificidades pertencem aos adapters.

## P6 — Resource budget obrigatório

O scanner deve ser utilizável em produção e hospedagem compartilhada.

CPU, I/O, workers, número de arquivos abertos, tamanho máximo de arquivo, tempo de provider e profundidade de parsing devem possuir limites configuráveis.

## P7 — Conteúdo do alvo é input hostil

Durante uma resposta a incidente, devemos assumir que o atacante controla:

- conteúdo dos arquivos;
- nomes dos arquivos;
- symlinks;
- conteúdo do banco;
- HTML;
- JSON;
- YAML;
- arquivos compactados;
- saída indireta de código comprometido;
- strings que podem terminar em relatório.

## P8 — O scanner não executa código do alvo para analisá-lo

Não utilizar `include`, `require`, import dinâmico ou qualquer mecanismo semelhante sobre arquivos do alvo.

Quando uma ferramenta externa inevitavelmente inicializa a aplicação, isso deve ser explicitamente classificado como modo de maior risco.

## P9 — Explainability é requisito de qualidade

Um finding crítico sem evidência útil é um finding ruim.

## P10 — Ferramentas externas são providers, não fundação arquitetural

WP-CLI, YARA, Wordfence CLI e Semgrep podem ser integrados, porém o schema interno deve continuar funcional mesmo quando um deles não existir.

---

# 3. Modelo de Domínio

## 3.1 Target

Representa o que está sendo analisado.

```python
Target(
    id: str,
    kind: TargetKind,
    root: Path | RemotePath | SnapshotRef,
    metadata: dict,
)
```

Tipos iniciais:

- `LOCAL_DIRECTORY`
- `SNAPSHOT_DIRECTORY`
- `ARCHIVE`

Futuros:

- `SSH_REMOTE`
- `SFTP_REMOTE`
- `CONTAINER`
- `KUBERNETES_POD`
- `OBJECT_STORAGE_SNAPSHOT`

## 3.2 Artifact

Objeto lógico analisável.

Não precisa ser arquivo.

Tipos previstos:

- arquivo;
- diretório;
- symlink;
- registro de banco;
- entrada de configuração;
- evento de cron;
- usuário/conta;
- resposta HTTP;
- componente/package;
- saída de analyzer;
- baseline manifest.

## 3.3 Evidence

Observação imutável criada por collector ou detector.

Exemplo:

```yaml
evidence_id: ev_01J...
scan_id: scan_01J...
kind: file_hash
source: filesystem
artifact_ref: art_01J...
collected_at: 2026-09-08T...
content:
  algorithm: sha256
  hash: ...
redaction_state: none
provenance:
  collector: internal.hash
  version: 0.1.0
```

## 3.4 Finding

Afirmação normalizada de segurança/integridade sustentada por evidência.

```yaml
finding_id: fnd_01J...
rule_id: WP.CORE.HASH_MISMATCH
title: Arquivo do core diverge do baseline confiável
category: integrity
severity: critical
confidence:
  type: deterministic
  score: 1.0
artifact_ref: art_01J...
evidence_refs:
  - ev_01J...
status: open
attributes:
  expected_hash: ...
  actual_hash: ...
```

## 3.5 Diagnosis

Hipótese correlacionada.

```yaml
diagnosis_id: dx_01J...
title: Possível adulteração persistente de código
confidence: high
basis:
  - fnd_...
  - fnd_...
hypothesis: ...
alternative_hypotheses:
  - ...
recommended_next_checks:
  - ...
```

Diagnosis nunca pode transformar heurística em fato determinístico.

## 3.6 Baseline

Expectativa de conteúdo utilizada para comparação.

Tipos:

- checksum oficial upstream;
- package confiável fornecido pelo operador;
- manifest assinado por CI/CD;
- snapshot golden;
- release artifact de repositório.

Estados de confiança:

- `TRUSTED_UPSTREAM`
- `TRUSTED_OPERATOR`
- `TRUSTED_SIGNED_INTERNAL`
- `UNVERIFIED_REFERENCE`

Uma referência não confiável pode ajudar a calcular diff, porém não deve gerar linguagem de “violação de baseline confiável”.

---

# 4. Modelo de Severidade e Confiança

Severidade e confiança são independentes.

## 4.1 Severidade

- **INFO** — inventário ou observação.
- **LOW** — sinal fraco/higiene.
- **MEDIUM** — anomalia relevante.
- **HIGH** — condição fortemente suspeita ou violação importante.
- **CRITICAL** — evidência de alto impacto, especialmente integridade confiável violada, assinatura forte de malware ou persistência perigosa.

## 4.2 Confiança

- `DETERMINISTIC`
- `HIGH`
- `MEDIUM`
- `LOW`
- `UNKNOWN`

Pode existir score `0.0–1.0`, mas ele complementa a classe e não deve fingir ser probabilidade científica.

## 4.3 Contrato das regras

Toda regra deve declarar:

- Rule ID;
- título;
- categoria;
- severidade padrão;
- confiança;
- evidências necessárias;
- plataformas aplicáveis;
- falsos positivos conhecidos;
- maturidade;
- referências técnicas.

---

# 5. Pipeline de Execução

```text
1. Validar configuração e argumentos
2. Resolver Target
3. Criar Scan Manifest
4. Descobrir plataforma(s)
5. Inventariar Artifacts
6. Coletar metadata
7. Resolver Baselines
8. Executar verificações determinísticas
9. Executar políticas de path/zone
10. Executar IOCs exatos
11. Executar heurísticas leves
12. Executar analyzers externos opcionais
13. Executar collectors específicos da plataforma
14. Normalizar saídas
15. Correlacionar Findings
16. Calcular Coverage
17. Produzir Diagnoses
18. Gerar relatórios
19. Encerrar com exit code documentado
```

## 5.1 Falha parcial

O padrão é degradar cobertura, não abortar tudo.

Exemplos:

```text
YARA indisponível
→ scan continua
→ Coverage.YARA = UNAVAILABLE

WP-CLI inexistente
→ inventory/heuristics continuam
→ checksum provider fica UNAVAILABLE

arquivo sem permissão
→ demais arquivos continuam
→ Artifact coverage = PARTIAL
```

Abortar scan somente quando a própria validade do alvo ou uma invariável interna não puder ser mantida.

---

# 6. Adapter WordPress — Primeira Implementação

## 6.1 Discovery

O adapter deve detectar WordPress sem exigir banco.

Sinais possíveis:

- `wp-includes/version.php`;
- `wp-admin/`;
- `wp-content/`;
- `wp-config.php` na raiz ou localização suportada;
- WP-CLI opcional em modo controlado.

A detecção deve utilizar combinação de evidências para evitar falso positivo por um único nome de diretório.

## 6.2 Zones de filesystem

### `wp-core-protected`

- `wp-admin/**`
- `wp-includes/**`
- arquivos oficiais da raiz

Esperado: comparação com baseline oficial.

### `wp-root-special`

- `wp-config.php`
- `.htaccess`
- `.user.ini`
- `php.ini`
- arquivos de configuração visíveis

Esperado: análise de política/heurística, não igualdade com upstream.

### `wp-content-plugins`

Plugins oficiais, premium e custom.

### `wp-content-themes`

Themes oficiais/customizados.

### `wp-content-mu-plugins`

Superfície importante porque código ali pode ser carregado automaticamente.

Existência de MU-plugin não é finding por si só.

### `wp-content-uploads`

Conteúdo majoritariamente não executável. Código executável é sinal de alta relevância, mas ainda precisa ser contextualizado.

### `wp-content-cache`

Zona de alto churn. Regras precisam evitar classificar cache gerado como malware automaticamente.

### `wp-content-upgrade`

Artefatos temporários de atualização.

### `wp-content-other`

Demais diretórios customizados.

## 6.3 Integridade do core

Provider preferencial no MVP:

```bash
wp core verify-checksums --include-root --format=json
```

WIRS não deve simplesmente exibir stdout. Deve transformar o resultado em Evidence/Findings próprios e registrar:

- versão do provider;
- comando lógico utilizado;
- status;
- tempo;
- erros;
- cobertura.

Um provider nativo consumindo manifests oficiais pode ser implementado depois como fallback/offline.

## 6.4 Plugins

Provider preferencial:

```bash
wp plugin verify-checksums --all --strict --format=json
```

Estados possíveis para componentes:

```text
VERIFIED
MISMATCH
MISSING_EXPECTED_FILE
UNEXPECTED_FILE
UNVERIFIED_NO_BASELINE
PROVIDER_FAILED
NOT_APPLICABLE
```

Plugin premium sem baseline deve virar `UNVERIFIED_NO_BASELINE`, nunca “malicioso”.

## 6.5 Themes e componentes customizados

Suporte a:

- ZIP limpo fornecido pelo operador;
- manifest de release;
- manifest gerado por CI;
- snapshot golden conhecido.

WIRS gera SHA-256 próprio para identidade e comparação.

## 6.6 Banco de dados WordPress

No MVP completo, a inspeção de banco deve existir.

Superfícies prioritárias:

- `options`;
- `site options` em multisite;
- posts;
- postmeta;
- usermeta quando justificado;
- tabelas próprias de plugins;
- WP-Cron;
- usuários privilegiados;
- application passwords/session metadata sem expor secrets.

IOC search pode começar usando `wp db search`.

O relatório não deve carregar dumps completos.

## 6.7 Segurança no uso de WP-CLI

Os comandos devem ser classificados.

### Safe/pre-load

Comandos documentados para operar antes do bootstrap completo possuem risco menor.

### Application-bootstrap

Comandos que carregam WordPress/plugins/themes podem executar código comprometido.

Configuração:

```yaml
platforms:
  wordpress:
    wp_cli_mode: safe_only
```

Valores:

- `safe_only`
- `allow_application_bootstrap`
- `disabled`

Default: `safe_only`.

---

# 7. Estratégia de Expansão Além de WordPress

## 7.1 PHP Generic Adapter

Capacidades futuras:

- descoberta de `.php`, `.phtml`, `.phar`;
- identificação por conteúdo, não só extensão;
- Composer inventory;
- análise de document root;
- zonas graváveis com execução;
- `.htaccess`, `.user.ini`, PHP ini;
- YARA/Semgrep;
- baseline fornecido pelo operador;
- ownership/permissions.

## 7.2 Laravel Adapter

Conhecimento específico futuro:

- `artisan`;
- `bootstrap/cache`;
- `storage`;
- `public`;
- Composer;
- `.env` sem exposição de secrets;
- scheduled tasks;
- arquivos/cache de rota/config;
- manifests de deploy.

## 7.3 Host Adapter

Post-MVP:

- crontab do usuário;
- vhosts;
- PHP-FPM pools;
- systemd timers/services quando autorizado;
- processos;
- portas;
- owner/group;
- arquivos executáveis modificados recentemente.

O host adapter deve permanecer opcional para que o produto funcione sem root.

# 8. /grill-me — Framework de Decisões

Esta seção existe para impedir que o projeto seja guiado por empolgação técnica em vez de restrições reais. Antes de implementar qualquer feature importante, ela deve sobreviver a estas perguntas.

## 8.1 Identidade do produto

### Q1. Estamos construindo scanner, assistente de resposta a incidente ou plataforma de remediação?

**Decisão:** scanner + orquestrador de evidências primeiro. Diagnóstico é uma camada derivada. Remediação fica fora do MVP.

**Motivo:** auto-remediation altera completamente o perfil de segurança, teste, responsabilidade operacional e risco de dano.

### Q2. Qual é a menor promessa realmente útil?

**Decisão:**

> Dado um target acessível, produzir um relatório reproduzível de integridade e segurança, com evidências e cobertura explícita.

Se isso não estiver sólido, qualquer dashboard, IA ou automação adicional é prematuro.

### Q3. O produto precisa declarar “o alvo está limpo”?

**Decisão:** não.

A formulação correta é:

```text
Nenhum finding acima do threshold foi encontrado nas verificações que concluíram.
Coverage: ...
```

### Q4. WordPress é o limite do produto?

**Decisão:** não. WordPress é o adapter #1.

---

## 8.2 Execução e deploy

### Q5. WIRS precisa ser instalado no host investigado?

**Decisão:** não como requisito arquitetural.

Modos desejados:

1. diretório local;
2. snapshot copiado;
3. filesystem montado;
4. archive controlado;
5. coleta SSH/SFTP futura;
6. container/pod futuro.

### Q6. Deve exigir root?

**Decisão:** não.

Collectors root-level podem existir depois como módulos opcionais.

### Q7. Como operar em hospedagem compartilhada?

**Decisão:** profile `soft` conservador.

Características:

- 1 worker padrão;
- fila limitada;
- baixa simultaneidade de open files;
- streaming;
- timeout;
- large-file policy;
- external analyzers limitados;
- nenhuma extração recursiva de archives;
- nenhuma escrita.

### Q8. SSH remoto deve instalar Python no host?

**Decisão:** não inicialmente.

Preferência futura:

- SFTP/SSH para leitura;
- comandos mínimos allowlisted;
- snapshot/stream para uma máquina limpa;
- remote helper apenas se trouxer benefício comprovado.

### Q9. Seguir symlink?

**Decisão:** não por padrão.

Registrar:

- caminho;
- destino;
- se escapa do root;
- se forma loop.

### Q10. Network filesystem pode ser analisado?

**Decisão:** sim, porém com profile conservador e sem assumir semântica de inode/ctime idêntica a ext4.

---

## 8.3 Confiança e baseline

### Q11. O que é baseline confiável?

**Decisão:**

- manifest oficial upstream;
- package limpo explicitamente confiado pelo operador;
- release manifest assinado;
- artifact de CI/CD conhecido;
- golden snapshot independente.

### Q12. Podemos transformar produção atual em baseline automaticamente?

**Decisão:** não para investigar o próprio estado atual.

Isso apenas congela potencial comprometimento.

Pode ser feito depois, quando o estado já tiver sido validado, para monitoramento de drift.

### Q13. O que fazer sem baseline?

**Decisão:** classificar como `UNVERIFIED`, continuar heurísticas.

### Q14. MD5 ou SHA-256?

**Decisão:** respeitar algoritmo upstream quando necessário para verificação oficial, mas usar SHA-256 internamente para identidade/manifests próprios.

### Q15. Pode usar cache de manifest remoto?

**Decisão:** sim, registrando origem, versão, timestamp e estado de confiança. Falha de rede não pode transformar cache não confiável em verdade automática.

---

## 8.4 Detecção

### Q16. `eval` significa malware?

**Decisão:** não.

### Q17. PHP dentro de uploads significa malware?

**Decisão:** não automaticamente. Significa forte violação de expectativa/política em grande parte das instalações e merece alta prioridade de análise.

### Q18. Entropia é útil?

**Decisão:** sim, como sinal auxiliar.

Alta entropia isolada não gera finding crítico.

### Q19. Regex própria ou YARA?

**Decisão:** ambos, em papéis diferentes.

- match literal e heurística barata: interno;
- assinatura mais rica: YARA;
- syntax-aware: Semgrep/Tree-sitter posteriormente.

### Q20. Semgrep entra no MVP?

**Decisão:** não como dependência obrigatória. Provider posterior.

### Q21. Devemos reimplementar o corpus do Wordfence?

**Decisão:** não.

Integrar Wordfence CLI como provider opcional é mais racional.

### Q22. Finding de ferramenta externa vira verdade do WIRS?

**Decisão:** vira Finding normalizado, mantendo:

- provider;
- versão;
- rule/signature ID original;
- confidence source;
- evidência disponível.

---

## 8.5 Banco

### Q23. Dump completo do banco?

**Decisão:** não por padrão.

### Q24. Procurar código arbitrário no banco inteiro?

**Decisão:** por etapas.

MVP:

- IOCs exatos;
- superfícies textuais prioritárias;
- padrões altamente específicos.

Depois:

- heurística em campos selecionados;
- parsers de JSON/serialized data seguros.

### Q25. Usar `unserialize()` do PHP?

**Decisão:** jamais sobre conteúdo hostil dentro do scanner.

Utilizar parser seguro e limitado, se necessário.

### Q26. Como tratar credentials?

**Decisão:** redaction na fronteira de coleta, não apenas na UI.

---

## 8.6 IA/LLM

### Q27. LLM é detector primário?

**Decisão:** não.

### Q28. LLM pode aumentar severidade automaticamente?

**Decisão:** pode sugerir classificação. Não pode modificar fato determinístico sem nova evidência/regra ou confirmação humana.

### Q29. O que pode ser enviado ao modelo?

**Decisão:** somente `AnalysisPacket` explicitamente habilitado e redigido.

Nunca por padrão:

- `.env` completo;
- private keys;
- `wp-config.php` bruto;
- dump de banco;
- tokens;
- credenciais;
- árvore inteira sem filtro.

### Q30. Scan depende de IA?

**Decisão:** nunca.

---

## 8.7 Reporting

### Q31. JSON ou relatório humano?

**Decisão:** ambos.

JSON é canônico. Terminal/Markdown/HTML são views.

### Q32. O que é o artifact de scan?

**Decisão:** bundle lógico contendo:

- Scan Manifest;
- Findings;
- Evidence metadata;
- Coverage;
- Diagnoses;
- Provider statuses.

Raw evidence sensível fica ausente por padrão.

### Q33. Incluir snippet de código?

**Decisão:** somente snippet limitado, escapado e redigido.

### Q34. Nome de arquivo pode atacar terminal/HTML?

**Decisão:** sim. Renderers devem tratar tudo como untrusted.

---

## 8.8 Arquitetura

### Q35. Microservices?

**Decisão:** não. Modular monolith/CLI.

### Q36. Message broker?

**Decisão:** não.

### Q37. Plugin system dinâmico agora?

**Decisão:** contratos internos de provider sim. Marketplace/dynamic loading depois.

### Q38. Banco de dados interno do produto?

**Decisão:** não no MVP. JSON primeiro; SQLite quando history/cache justificar.

### Q39. Async ou multiprocessing?

**Decisão:** scheduler central escolhe estratégia conforme workload. Detectors não criam pools ilimitados.

### Q40. Detector abre arquivo diretamente?

**Decisão:** preferencialmente não. Deve utilizar `ArtifactReader` para compartilhar hash/read, budget, telemetry e segurança.

---

# 9. /tdd — Especificação Test-Driven Development

Para uma ferramenta de segurança, testes definem semântica. WIRS deve nascer com fixture-driven development.

## 9.1 Pirâmide de testes

### Unit tests

Cobrem:

- path normalization;
- Artifact IDs;
- hashing;
- baseline comparison;
- severity/confidence;
- rule predicates;
- redaction;
- provider parsers;
- coverage;
- serialização.

### Integration tests

Cobrem:

- filesystem real;
- subprocess provider fake/real;
- WP-CLI;
- YARA;
- banco descartável;
- reports.

### Golden tests

Um fixture conhecido gera JSON canônico esperado. Alteração de golden exige revisão explícita.

### E2E

Instância isolada WordPress limpa/adulterada → execução do CLI real → comparação de findings/coverage/exit code.

### Security/Fuzz tests

- nomes hostis;
- Unicode;
- invalid UTF-8;
- symlink loops;
- special files;
- oversized content;
- malformed JSON/YAML;
- regex stress;
- archive traversal;
- terminal injection;
- HTML injection;
- output malicioso de provider.

## 9.2 Filosofia dos fixtures

Não colocar malware executável real no repositório normal.

Preferir amostras sintéticas e inertes que representem técnicas sem risco de execução.

Estrutura:

```text
tests/
  fixtures/
    generic/
      clean_tree/
      symlink_escape/
      hostile_names/
      large_files/
      high_entropy/
    wordpress/
      clean_core/
      modified_core/
      unexpected_core/
      clean_plugin/
      modified_plugin/
      premium_unverified/
      uploads_php/
      mu_plugin/
      config_persistence/
      database/
  golden/
  unit/
  integration/
  e2e/
  security/
```

## 9.3 Catálogo mínimo obrigatório

### Filesystem

**T001 — target vazio**  
Scan conclui, nenhuma plataforma detectada, coverage coerente.

**T002 — root ilegível**  
Falha de target. Nunca retornar “sem findings” como se scan tivesse sido válido.

**T003 — child file ilegível**  
Scan continua e coverage fica parcial.

**T004 — symlink interno**  
Inventariado, não seguido.

**T005 — symlink externo**  
Escape detectado, não atravessado.

**T006 — symlink loop**  
Sem recursão infinita.

**T007 — filename hostil**  
Nome com newline, ANSI, `<script>`, tab ou bytes inválidos não corrompe report.

**T008 — arquivo gigante**  
Budget respeitado.

### Baseline/hash

**T010 — baseline idêntico**  
`VERIFIED`.

**T011 — 1 byte modificado**  
Mismatch determinístico.

**T012 — arquivo esperado ausente**  
`FILE_MISSING`.

**T013 — arquivo extra em escopo protegido**  
`UNEXPECTED_FILE`.

**T014 — duplicate path no manifest**  
Manifest inválido.

**T015 — `../../` no manifest**  
Rejeitado.

### WordPress

**T020 — core limpo**  
Sem integrity finding.

**T021 — core alterado**  
`WP.CORE.HASH_MISMATCH`.

**T022 — PHP extra no core**  
Unexpected + sensitive executable.

**T023 — plugin oficial limpo**  
Verified.

**T024 — plugin oficial modificado**  
Mismatch.

**T025 — premium sem baseline**  
Unverified, não malicious.

**T026 — premium com package confiável**  
Verified.

**T027 — premium adulterado**  
Mismatch.

**T028 — PHP em uploads**  
Policy finding.

**T029 — PHP disfarçado de imagem**  
Content/type mismatch signal.

**T030 — MU-plugin legítimo**  
Inventariado e analisado sem finding automático.

### IOC

**T040 — literal exato**  
Location + bounded context.

**T041 — IOC em binary**  
Sem decode inseguro.

**T042 — milhares de ocorrências**  
Cap de ocorrências evita report explosivo e preserva count.

**T043 — regex problemática**  
Budget impede travamento.

### Heurística

**T050 — `base64_decode` isolado**  
Não crítico.

**T051 — `eval` isolado**  
Sinal contextual.

**T052 — cadeia de obfuscation**  
Score/confidence maior por regra explícita.

**T053 — string longa de alta entropia**  
Sinal somente após thresholds.

**T054 — JS minificado legítimo**  
Minificação sozinha não gera high severity.

### YARA

**T060 — YARA ausente**  
Scan continua, coverage indica indisponibilidade.

**T061 — erro de compilação de rule pack**  
Provider falha sem derrubar scan.

**T062 — synthetic match**  
Rule/tags/namespace preservados.

### WP-CLI

**T070 — WP-CLI ausente**  
Fallback correto.

**T071 — timeout**  
Processo encerrado/controlado.

**T072 — JSON inválido**  
Provider error.

**T073 — stderr hostil**  
Escapado/redigido.

**T074 — `safe_only` bloqueia collector que faz bootstrap**  
Coverage registra skip explícito.

### Banco

**T080 — IOC em option**  
Table/column/PK + contexto redigido.

**T081 — IOC em postmeta**  
Mesmo contrato.

**T082 — serialized value enorme**  
Budget.

**T083 — serialized data malformado**  
Sem crash/unserialize inseguro.

**T084 — DB indisponível**  
Filesystem continua; DB = UNAVAILABLE.

### Redaction

**T090 — senha DB fake**  
Nunca aparece no report.

**T091 — private key fake**  
Bloco redigido.

**T092 — token fake**  
Redação sem remover IDs/hash legítimos indiscriminadamente.

### Reporting

**T100 — JSON estável**  
Schema e ordering definidos.

**T101 — ANSI injection**  
Neutralizada.

**T102 — HTML injection**  
Escapada.

**T103 — interrupção na escrita**  
Arquivo incompleto não é apresentado como report final.

### Performance

**T110 — 100 mil arquivos sintéticos**  
Memória bounded.

**T111 — worker=1**  
Profile soft funcional.

**T112 — workers=N**  
Sem duplicação/loss por race.

**T113 — SIGINT**  
Shutdown seguro + scan marcado incomplete.

## 9.4 Ordem TDD sugerida

1. SafePath / Artifact.
2. Inventory.
3. ArtifactReader.
4. Hash service.
5. Evidence/Finding.
6. Coverage.
7. Baseline manifest/comparator.
8. Generic policy engine.
9. WordPress discovery/zones.
10. WP checksum provider.
11. IOC scanner.
12. Reports.
13. YARA.
14. Premium baseline.
15. DB.
16. Diagnoses.
17. Remote.

## 9.5 Property-based tests

Utilizar Hypothesis ou equivalente para:

- caminhos aleatórios;
- Unicode estranho;
- tamanho de arquivo;
- manifests;
- serialização round-trip;
- thresholds;
- coverage invariants.

Invariantes:

```text
verified + failed + skipped + unavailable = applicable_checks
```

```text
SafePath nunca resolve para fora do TargetRoot.
```

```text
Report redigido não contém nenhum secret conhecido pelo fixture.
```

```text
Scan determinístico + input imutável + providers equivalentes
=> findings semanticamente equivalentes.
```

---

# 10. /qa-analysis — Estratégia de Quality Assurance

## 10.1 O que qualidade significa no WIRS

Não basta “não crashar”. QA precisa avaliar:

- falso positivo;
- falso negativo mensurável;
- reprodutibilidade;
- qualidade da evidência;
- isolamento de provider failure;
- consumo de recursos;
- segurança de output;
- compatibilidade;
- estabilidade de schema.

## 10.2 Quality gates

### Pull Request

Obrigatório:

- unit tests;
- integration tests afetados;
- lint/format;
- type check;
- nenhuma regressão de segurança conhecida;
- nova regra com fixture positivo e negativo;
- schema change documentado.

### Main

Além do PR:

- suite integrada completa;
- golden tests;
- security tests;
- package build;
- dependency audit.

### Release Candidate

Além disso:

- E2E WordPress limpo;
- E2E adulterado;
- benchmark soft/balanced;
- clean install;
- provider absent/offline;
- redaction verification;
- compatibility report.

## 10.3 Processo de promoção de regras

### Experimental

- disabled by default;
- pouco corpus benigno;
- rule author deve deixar falso positivo explícito.

### Beta

- opt-in;
- corpus razoável;
- confidence ainda pode mudar.

### Stable

- enabled default quando apropriado;
- positivo/negativo consistente;
- evidência clara;
- documentação.

## 10.4 Corpus benigno

Criar testes com:

- versões WordPress representativas;
- plugins populares;
- themes populares;
- JS minificado pesado;
- MU-plugins customizados;
- WordPress Composer/Bedrock-like futuramente;
- aplicações PHP genéricas.

Não redistribuir código proprietário sem licença.

## 10.5 Corpus malicioso/sintético

Preferir artefatos inertes representando:

- encoding/decoding chain;
- execução dinâmica;
- dropper-like sem sink real;
- webshell-like sem backend funcional;
- iframe/script injection;
- config persistence;
- cron suspeito.

Malware real deve ficar em corpus privado/controlado, se um dia necessário.

## 10.6 Compatibility matrix

MVP:

| Dimensão | Cobertura mínima |
|---|---|
| Linux | Ubuntu/Debian atuais |
| Python | 3.11–3.13 conforme deps |
| Filesystem | local + smoke network mount |
| WordPress | versões atuais + branch antiga representativa |
| WP-CLI | versão atual + ausência graciosa |
| YARA | versão suportada + ausência graciosa |
| DB | MariaDB + MySQL representativos |

Futuro:

- macOS client;
- Windows client;
- ARM64;
- Alpine;
- containers.

## 10.7 Performance QA

Métricas:

- arquivos/s;
- MB/s hashing;
- peak RSS;
- CPU;
- provider duration;
- wall time;
- bytes skipped;
- queue depth;
- open FDs.

Profiles:

### `soft`

```yaml
workers: 1
max_open_files: 16
external_workers: 1
large_file_policy: hash_stream
```

### `balanced`

Padrão VPS.

### `fast`

Usuário aceita maior uso de recurso.

Os profiles mudam scheduling, não semântica do finding.

## 10.8 Exit codes

Proposta:

```text
0   scan completo, nenhum finding no fail threshold
1   scan completo, finding atingiu fail threshold
2   target/argument/config inválido
3   scan incompleto por falha crítica de coleta
4   erro interno do scanner
5   rule pack/configuração inválida
130 interrompido pelo operador
```

Opção:

```bash
wirs scan ... --fail-on high
```

---

# 11. /grill-features-with-docs — Revisão de Features Contra Ferramentas Existentes

Esta seção serve para evitar reinventar capacidades maduras.

## 11.1 Checksum do WordPress Core

### O que já existe

WP-CLI fornece:

```bash
wp core verify-checksums
```

A documentação oficial informa que o comando compara arquivos com checksums do WordPress.org, aceita version/locale, possui `--include-root`, JSON e opera em `before_wp_load`.

### Decisão WIRS

**Integrar primeiro; reimplementar apenas fallback necessário.**

Responsabilidades do WIRS:

- detectar WP-CLI;
- executar por `CommandRunner` seguro;
- aplicar timeout;
- parsear output;
- normalizar Findings;
- registrar provider/version;
- calcular Coverage;
- continuar sem provider.

Fallback nativo será útil para:

- snapshot offline;
- host sem WP-CLI;
- cache de manifests;
- remote scans.

## 11.2 Checksum de plugins oficiais

### Existente

```bash
wp plugin verify-checksums --all --strict
```

### Decisão

Provider WP-CLI para plugins WordPress.org.

WIRS adiciona:

- baselines premium/custom;
- estado `UNVERIFIED`;
- normalização;
- correlação;
- reporting.

## 11.3 Arquivos inesperados

WP-CLI já identifica situações em áreas de core, mas WIRS precisa de **path policy engine genérico** para expressar:

- arquivo executável em uploads;
- script em storage;
- world-writable executable;
- arquivo extra em component manifest;
- extension/content mismatch.

## 11.4 Malware signatures

### Existente

Wordfence CLI é open source, multiprocessado e possui malware/vulnerability scanning.

### Decisão

Não construir corpus concorrente no MVP.

Criar provider:

```python
class ExternalAnalyzer(Protocol):
    id: str
    capabilities: set[Capability]
    def available(self) -> Availability: ...
    def scan(self, artifacts, ctx) -> AnalyzerResult: ...
```

Wordfence entra como analyzer opcional.

Remediation dele não deve ser chamada por `wirs scan`.

## 11.5 YARA

### Existente

Engine consolidado para rules/signatures, com bindings Python.

### Decisão

Primeiro signature provider extensível.

Estrutura:

```text
rules/
  yara/
    builtin/
    wordpress/
    php/
    experimental/
```

## 11.6 Semgrep

### Existente

Rules syntax-aware, search e taint.

### Decisão

Provider opcional fase 2.

Casos úteis:

- dangerous APIs;
- request → execution flows;
- patterns PHP difíceis de expressar com regex;
- adapters Laravel/Joomla.

Core não depende de recursos cloud.

## 11.7 Tree-sitter

### Decisão

Não MVP. Reservar `SyntaxAnalyzer` port para análise futura interna de AST/syntax tree.

## 11.8 Database search

### Existente

`wp db search` pesquisa colunas textuais e retorna table/column/match/PK.

### Decisão

Provider WordPress inicial, porém manter `DatabaseReader` genérico.

WIRS precisa controlar:

- queries read-only;
- redaction;
- limite de rows/context;
- timeout;
- coverage.

## 11.9 WP-Cron

### Existente

`wp cron event list`.

### Decisão

Collector de persistência WordPress, não detector automático de malware.

## 11.10 Configuração WordPress

### Existente

`wp config list`.

### Decisão

Coletar apenas fatos seguros/necessários.

Exemplos:

- `DISALLOW_FILE_EDIT`;
- `DISALLOW_FILE_MODS`;
- MULTISITE;
- custom content path;
- suspicious includes;
- debug state.

Nunca serializar DB password ou salts no report.

## 11.11 Permissions/ownership

### Decisão

Analisar metadata e policy, sem auto-chmod.

Findings úteis:

- world-writable executable;
- config excessivamente permissiva;
- mudança de owner versus baseline;
- executable writable em zona que deveria ser protegida.

Não assumir uma única permissão universal correta para todos os hosts.

## 11.12 Vulnerability intelligence

### Decisão

Provider opcional posterior.

Vulnerabilidade conhecida é contexto, não prova de comprometimento.

## 11.13 Runtime HTTP

### Decisão

Fase 2.

Collector bounded deve conseguir:

- GET/HEAD;
- redirects;
- headers;
- response hash;
- origins externos;
- scripts/iframes;
- cookie jar;
- user-agent/referer profiles.

Não virar browser automation completo no MVP.

## 11.14 LLM analysis

### Decisão

`AnalysisProvider` opcional.

Entrada:

- Findings;
- diffs;
- bounded snippets;
- metadata;
- rule explanations.

Saída:

- classificação sugerida;
- rationale;
- alternativas;
- próximos checks determinísticos.

Nenhuma mutação do alvo.

---

# 12. /diagnoses — Engine de Correlação e Diagnóstico

## 12.1 Por que separar diagnosis de finding

Finding é observação normalizada.

Diagnosis responde:

> O que a combinação desses findings possivelmente significa?

Misturar os dois cria certeza falsa.

## 12.2 Chaves de correlação

- mesmo artifact;
- mesmo diretório;
- mesmo component;
- mesmo IOC;
- mesmo domínio/IP/hash;
- mesmo owner;
- mesma janela de alteração;
- mesma persistence surface;
- DB record apontando para artifact;
- runtime origin apontando para IOC existente;
- baseline mismatch + code heuristic no mesmo arquivo.

## 12.3 Regras iniciais

### DX001 — Trusted mismatch + malware signature

Requisitos:

- baseline confiável diverge;
- mesmo artifact tem signature high-confidence.

Resultado:

```text
Alta probabilidade de adulteração de artifact confiável.
```

### DX002 — Executável inesperado em zona de conteúdo

Requisitos:

- executable content;
- zone esperada non-executable;
- sinais adicionais suspeitos.

### DX003 — Persistence config → suspicious artifact

Configuração de persistência referencia artifact que possui findings relevantes.

### DX004 — DB + filesystem correlation

Registro suspeito no DB referencia component/path/domain que possui outros findings.

## 12.4 Confidence de diagnosis

No MVP, receitas categóricas explícitas são melhores que números sofisticados falsamente precisos.

Exemplo:

```yaml
rule: DX001
requires:
  integrity_mismatch: deterministic
  malware_signature: high
confidence: high
severity: critical
```

## 12.5 Output obrigatório

Todo diagnosis deve trazer:

- título;
- resumo;
- confidence;
- findings base;
- motivo da correlação;
- o que ainda não sabemos;
- hipóteses alternativas;
- próximos checks;
- necessidade de confirmação humana.

## 12.6 Sem raciocínio circular

Finding → Diagnosis.

Diagnosis não pode criar Evidence para justificar Finding no mesmo scan.

## 12.7 Evidence graph futuro

Estrutura desejável:

```text
Artifact -> belongs_to -> Component
Artifact -> mismatches -> Baseline
Artifact -> contains -> IOC
Artifact -> referenced_by -> Persistence
DBRecord -> references -> Domain
HTTPResponse -> loads -> Domain
```

Graph DB não é necessário no MVP. IDs/relações estáveis deixam a migração possível.

---

# 13. /scaffold-mvp — Scaffold Técnico do MVP

## 13.1 Objetivo

Entregar CLI capaz de analisar diretório/snapshot WordPress de forma segura e gerar findings úteis sem precisar executar a aplicação.

## 13.2 Definition of Done do MVP

MVP completo quando:

1. `wirs scan <target>` funciona.
2. Inventory é seguro e bounded.
3. WordPress discovery funciona.
4. Zones funcionam.
5. Core official checksum funciona via provider.
6. Plugin official checksum funciona via provider.
7. Operator baseline funciona para componentes custom.
8. IOC scanner funciona.
9. Sensitive zone policy funciona.
10. Heuristic pack PHP v0 funciona.
11. YARA opcional funciona ou degrada corretamente.
12. Coverage é explícito.
13. JSON + terminal funcionam.
14. Redaction funciona.
15. TDD clean/tampered fixture passa.
16. Profile soft funciona.
17. Exit codes documentados.
18. Nenhuma escrita no target.

DB pode entrar no `0.2/0.3`, porém deve existir antes de considerar a solução madura para incident response WordPress.

## 13.3 Estrutura de repositório

```text
wirs/
├── pyproject.toml
├── README.md
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── docs/
│   ├── architecture.md
│   ├── threat-model.md
│   ├── rule-authoring.md
│   ├── providers.md
│   ├── reports.md
│   ├── wordpress-adapter.md
│   └── adr/
├── src/wirs/
│   ├── cli/
│   ├── domain/
│   ├── application/
│   ├── ports/
│   ├── infrastructure/
│   ├── detectors/
│   ├── providers/
│   ├── adapters/wordpress/
│   ├── reporting/
│   └── config/
├── rules/
│   ├── builtin/
│   ├── wordpress/
│   ├── php/
│   └── experimental/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── security/
│   ├── fixtures/
│   └── golden/
└── scripts/
```

## 13.4 Dependências

Poucas e isoladas.

Possíveis:

- Typer/Click — CLI;
- Pydantic ou dataclasses validadas — config/models;
- Rich — terminal;
- pytest;
- Hypothesis;
- Ruff;
- mypy/pyright;
- yara-python como extra;
- MySQL connector como extra.

Providers externos devem ser opcionais.

## 13.5 CLI

```text
wirs scan <target>
wirs scan <target> --profile soft
wirs scan <target> --platform wordpress
wirs scan <target> --ioc iocs.txt
wirs scan <target> --baseline baselines.yaml
wirs scan <target> --format terminal
wirs scan <target> --report scan.json

wirs baseline create <clean-dir> --name component
wirs baseline inspect <manifest>
wirs baseline verify <target> --manifest <manifest>

wirs rules validate
wirs rules list
wirs doctor
wirs version
```

Futuro:

```text
wirs collect ssh://host/path --output snapshot.tar.zst
wirs scan snapshot.tar.zst
wirs compare old.json new.json
wirs explain <finding-id>
```

## 13.6 Configuração mínima

```yaml
version: 1

scan:
  profile: soft
  workers: 1
  max_file_bytes: 268435456
  follow_symlinks: false
  include_hidden: true

platforms:
  auto_detect: true
  wordpress:
    enabled: true
    wp_cli_mode: safe_only

providers:
  wp_cli:
    enabled: auto
    timeout_seconds: 60
  yara:
    enabled: auto
  wordfence_cli:
    enabled: false

rules:
  builtin: true
  experimental: false

evidence:
  snippet_bytes: 512
  store_raw_content: false

report:
  redact_secrets: true
  include_info: true
```

## 13.7 Primeiro vertical slice

```text
wirs scan ./wordpress --ioc iocs.txt
    ↓
validate target
    ↓
inventory
    ↓
WordPress discovery
    ↓
zone classification
    ↓
shared file stream/hash/features
    ↓
WP-CLI core/plugin checksum
    ↓
IOC scanner
    ↓
executable-zone policy
    ↓
PHP heuristics v0
    ↓
Coverage
    ↓
Terminal + JSON
```

Sem DB, browser, LLM ou remote no primeiro slice.

## 13.8 Performance implementation

- streaming;
- hash uma vez;
- features compartilhadas;
- sem subprocess por arquivo;
- external analyzer em batch;
- bounded queues;
- scheduler central;
- cache apenas no scan inicialmente.

## 13.9 Packaging

MVP:

- `pipx`/`pip`;
- optional extras;
- Docker image para scan de snapshot/mount.

Depois:

- standalone binary;
- signed release;
- SBOM;
- package repos.

# 14. /query-docs — Mapa de Documentação e Fontes de Verdade

Toda integração externa deve ter documentação oficial registrada no repositório. O objetivo é evitar que comportamento de provider fique baseado em memória, suposição ou parsing acidental de output.

## 14.1 Política de documentação de providers

Para cada provider registrar:

- nome;
- versão testada;
- documentação oficial;
- comandos/APIs utilizados;
- formatos de output;
- exit codes;
- se inicializa código do target;
- se acessa rede;
- se pode modificar target;
- credenciais necessárias;
- limites de timeout/concurrency;
- licença;
- fallback;
- última data de validação.

Arquivo sugerido:

```text
docs/providers/<provider>.md
```

## 14.2 WP-CLI — Core checksum

Documentação:

https://developer.wordpress.org/cli/commands/core/verify-checksums/

Contrato relevante:

- compara arquivos WordPress com checksums do WordPress.org;
- suporta versão/locale;
- `--include-root` amplia verificação de itens inesperados;
- possui formato JSON;
- é documentado no hook `before_wp_load`.

Dependência WIRS:

```text
WpCliCoreChecksumProvider
```

Teste de compatibilidade:

- fixture WordPress conhecido;
- modificar um arquivo;
- executar provider real;
- validar normalização.

## 14.3 WP-CLI — Plugin checksum

Documentação:

https://developer.wordpress.org/cli/commands/plugin/verify-checksums/

Contrato:

- verifica plugins contra checksums do WordPress.org;
- `--all`;
- `--strict`;
- output estruturado.

Provider:

```text
WpCliPluginChecksumProvider
```

## 14.4 WP-CLI — Database search

Documentação:

https://developer.wordpress.org/cli/commands/db/search/

Contrato:

- busca em colunas textuais;
- aceita `--all-tables-with-prefix`;
- retorna table/column/match/primary key;
- regex/context opcionais.

Risco:

Pode expor secrets/conteúdo sensível. WIRS deve normalizar somente metadata necessária + contexto limitado/redigido.

## 14.5 WP-CLI — Cron

Documentação:

https://developer.wordpress.org/cli/commands/cron/event/list/

Provider/collector:

```text
WpCronCollector
```

Não considerar cron desconhecido como malware automaticamente.

## 14.6 WP-CLI — Config

Documentação:

https://developer.wordpress.org/cli/commands/config/list/

Uso:

- fatos selecionados;
- nenhuma coleta indiscriminada de secrets.

## 14.7 WordPress hardening

Documentação:

https://developer.wordpress.org/advanced-administration/security/hardening/

https://developer.wordpress.org/advanced-administration/server/file-permissions/

Uso no WIRS:

- rationale das regras;
- contextual help;
- não auto-remediation.

## 14.8 Wordfence CLI

Repository:

https://github.com/wordfence/wordfence-cli

Produto/docs:

https://www.wordfence.com/products/wordfence-cli/

Examples:

https://github.com/wordfence/wordfence-cli/blob/main/docs/malware-scan/Examples.md

Verificar antes da integração:

- formato de output;
- workers;
- exit codes;
- timeout;
- pipe;
- licença/feed;
- comportamento quando assinatura não pode ser baixada;
- não executar remediation.

## 14.9 YARA

Documentação:

https://yara.readthedocs.io/

Verificar:

- compile;
- warnings;
- match file/data;
- namespaces;
- tags;
- timeout.

## 14.10 Semgrep

Documentação:

https://semgrep.dev/docs/writing-rules/

https://semgrep.dev/docs/writing-rules/rule-syntax/

Uso futuro:

- search rules;
- taint rules;
- language-aware matching.

## 14.11 Tree-sitter

Documentação:

https://tree-sitter.github.io/tree-sitter/using-parsers/

Uso futuro:

- parser interno syntax-aware.

## 14.12 Checklist `/query-docs` por provider

Antes de implementar qualquer provider responder:

1. Ele executa código do target?
2. Pode modificar o target?
3. Acessa rede?
4. Requer API key/secret?
5. Quais exit codes?
6. Output é machine-readable?
7. Output contém texto controlado pelo target?
8. Possui timeout/cancellation?
9. Concurrency é configurável?
10. Falha parcial é distinguível de sucesso?
11. A licença permite integração/distribuição?
12. Funciona offline?
13. Envia dados para terceiros?
14. Qual compatibilidade entre versões?
15. Existe fallback?

## 14.13 ADRs iniciais

```text
ADR-001 Python no MVP
ADR-002 Read-only por padrão
ADR-003 Platform adapter boundary
ADR-004 Canonical JSON schema
ADR-005 WP-CLI como provider preferencial de checksum WordPress
ADR-006 YARA como signature provider opcional
ADR-007 LLM fora do pipeline determinístico
ADR-008 Symlink não seguido por padrão
ADR-009 Safe WP-CLI mode sem bootstrap por padrão
ADR-010 Provider failure degrada coverage
```

---

# 15. /design-system — Design System de CLI, Relatórios e UI Futura

Em uma ferramenta de segurança, design system inclui linguagem, hierarquia de informação, semântica e consistência operacional.

## 15.1 Objetivos

- analista entende estado crítico rapidamente;
- uncertainty visível;
- Coverage tão importante quanto Findings;
- cor nunca é o único indicador;
- output pode ser anexado a ticket sem expor secrets;
- JSON, CLI e UI usam os mesmos conceitos.

## 15.2 Vocabulário oficial

- **Scan** — uma execução.
- **Target** — alvo analisado.
- **Artifact** — objeto analisável.
- **Evidence** — observação/fato.
- **Finding** — afirmação de segurança/integridade.
- **Diagnosis** — hipótese correlacionada.
- **Baseline** — expectativa confiável/referencial.
- **Provider** — implementação de capability.
- **Rule** — lógica que gera finding.
- **Coverage** — abrangência real da análise.
- **Unverified** — sem baseline suficiente.
- **Skipped** — pulado deliberadamente.
- **Unavailable** — capability/provider não disponível.

Evitar como status global:

- clean;
- safe;
- hacked;
- infected.

## 15.3 Terminal UX

Exemplo:

```text
WIRS 0.1.0
Target: /var/www/site
Platform: WordPress
Profile: soft
Mode: read-only

[1/6] Inventory             18,204 artifacts
[2/6] Trusted integrity     core verified; plugins 12 verified / 2 unverified
[3/6] Policy checks         4 findings
[4/6] IOC scan              0 findings
[5/6] External analyzers    YARA complete / Wordfence unavailable
[6/6] Correlation           1 diagnosis

SUMMARY
CRITICAL  0
HIGH      1
MEDIUM    3
LOW       2
INFO      14

COVERAGE
Filesystem           COMPLETE
Core baseline        COMPLETE
Plugin baseline      PARTIAL
YARA                  COMPLETE
Database              NOT RUN
Runtime               NOT RUN
```

## 15.4 Severity e confidence

Sempre separados:

```text
Severity: HIGH
Confidence: DETERMINISTIC
```

Nunca usar apenas cor ou porcentagem sem semântica.

## 15.5 Coverage states

- `COMPLETE`
- `PARTIAL`
- `SKIPPED`
- `UNAVAILABLE`
- `FAILED`
- `NOT_APPLICABLE`

Exemplo:

```text
Plugin integrity: PARTIAL
verified: 18
unverified: 3
provider_failures: 0
```

## 15.6 Finding card

```text
[HIGH] WP.UPLOAD.EXECUTABLE
Conteúdo executável encontrado em zona destinada a uploads

Artifact
  wp-content/uploads/2026/example.php

Confidence
  HIGH

Evidence
  content_type_hint: php
  zone: wp-content-uploads

Why this matters
  A zona é normalmente destinada a conteúdo não executável.

Possible benign explanations
  - plugin específico grava PHP nessa pasta
  - configuração custom deliberada

Next checks
  - verificar baseline/component owner
  - executar signatures/heuristics
  - revisar referências ao artifact
```

## 15.7 Formatos

### JSON

Canônico.

### Terminal

Operacional.

### Markdown

Tickets e documentação.

### HTML

Pós-MVP, self-contained e seguro.

### SARIF

Futuro.

## 15.8 UI web futura

Somente quando history/fleet justificar.

Páginas:

1. Scans
2. Scan Overview
3. Findings
4. Evidence
5. Components
6. Coverage
7. Diagnoses
8. Baselines
9. Rules
10. Providers

Nenhuma regra de negócio exclusiva do frontend.

## 15.9 Segurança e acessibilidade de output

- escape HTML;
- neutralize ANSI;
- preserve raw path somente como data segura;
- mostrar `[REDACTED_SECRET]`;
- truncation deve ser visível;
- não depender só de cor.

---

# 16. /secure-e2e — Arquitetura de Segurança End-to-End

O alvo comprometido deve ser considerado adversarial. O scanner pode ser deliberadamente atacado através do conteúdo que analisa.

## 16.1 Atores de ameaça

### A. Target comprometido

Controla arquivos, paths, symlinks, DB, configuração e conteúdo.

### B. Provider externo comprometido

Binary local ou rule pack retorna output malicioso.

### C. Baseline/rule package malicioso

ZIP ou manifest fornecido ao scanner contém path traversal ou payload.

### D. Remote target/MITM

Pode apresentar snapshot inconsistente ou atacar transporte.

### E. Report consumer

Analista abre HTML/terminal/Markdown contendo dados hostis.

## 16.2 Boundaries

```text
UNTRUSTED TARGET
      ↓
Artifact Reader Boundary
      ↓
Collectors / Parsers
      ↓
Evidence
      ↓
Rules / Providers
      ↓
Normalized Findings
      ↓
Report Renderer Boundary
      ↓
ANALYST
```

## 16.3 Proteção contra escrita

Regras de código:

- target files abertos como `rb`;
- detector não recebe write API;
- output directory validado fora do target por padrão;
- nenhuma função remediation dentro do scan flow;
- DB read-only;
- SQL WIRS-owned limitado a SELECT/metadata;
- external command por argument array, nunca string shell.

## 16.4 Command injection

Proibido:

```python
os.system(f"grep {pattern} {path}")
```

Usar:

- `shell=False`;
- lista de argumentos;
- executable allowlisted;
- cwd explícito;
- env sanitizado;
- timeout;
- output cap.

## 16.5 Environment

Subprocess deve receber somente environment necessário.

Avaliar remoção/controle de:

- `PYTHONPATH`;
- proxy vars quando networking não é permitido;
- variáveis de aplicação contendo secrets;
- configurações PHP herdadas perigosas.

## 16.6 Parsing

Todo parser deve ter:

- max bytes;
- max depth;
- decode seguro;
- timeout quando aplicável.

## 16.7 Archives

MVP não precisa expandir arbitrary archives do target.

Quando adicionar:

- zip slip;
- decompression bomb;
- recursive archives;
- symlink entry;
- device files;
- max file count;
- max expanded bytes.

## 16.8 Special files

- regular file → scan;
- dir → traverse;
- symlink → metadata only;
- socket/FIFO/device → nunca ler como regular file;
- hardlink → metadata/dedup onde possível.

## 16.9 Regex DoS

- validar rules;
- limitar input;
- preferir engine segura quando viável;
- timeout;
- nunca deixar custom regex travar processo inteiro.

## 16.10 Secrets

Não reportar:

- DB passwords;
- salts;
- API keys;
- private keys;
- tokens;
- `.env` completo;
- SMTP/cloud credentials.

Redaction antes da serialização final.

`store_raw_content: false` por default.

## 16.11 Baseline packages

Workflow:

1. declarar source;
2. calcular package hash;
3. extrair isoladamente;
4. path normalization;
5. gerar manifest;
6. registrar provenance;
7. futuramente assinar.

Nunca executar lifecycle/install scripts do package.

## 16.12 Rule packs

- versionados;
- provenance;
- validation;
- sem arbitrary Python em YAML/rules;
- experimental separado;
- assinatura futura.

## 16.13 External analyzers

Onde possível:

- menor privilégio;
- timeout;
- output cap;
- temp dir isolado;
- no write target;
- sandbox/container para snapshot/local.

## 16.14 WP-CLI

O uso de WP-CLI merece classificação por comando.

Default:

- preferir pre-load;
- `safe_only`;
- application-bootstrap opt-in;
- nunca rodar como root por conveniência.

## 16.15 Database

- least privilege;
- read-only;
- timeout;
- row cap;
- context cap;
- DSN sem password em log;
- evidence em table/column/PK, não full row.

## 16.16 SSH futuro

- host key verification;
- known_hosts;
- sem senha na command line;
- key/agent;
- sem `StrictHostKeyChecking=no` default;
- comandos remotos allowlisted;
- snapshot hash.

## 16.17 Reports

### HTML

- escape tudo;
- CSP forte;
- sem remote JS/CSS por default;
- sem `innerHTML` com conteúdo hostil.

### Terminal

- neutralizar control chars/ANSI.

### Markdown

- impedir link injection onde relevante.

## 16.18 Supply chain do WIRS

- dependency lock;
- audit;
- SBOM;
- CI least privilege;
- signed tags/releases no futuro;
- SECURITY.md;
- release artifacts verificáveis.

## 16.19 LLM boundary

LLM recebe somente:

```yaml
AnalysisPacket:
  findings: [...]
  redacted_snippets: [...]
  metadata: {...}
```

Conteúdo do source deve ser identificado no prompt como **evidência não confiável**, para impedir que prompt injection existente no código seja tratado como instrução.

LLM não recebe acesso arbitrário ao filesystem através desse contrato.

---

# 17. /to-issues — Backlog em Epics e Issues

Este backlog transforma a arquitetura em trabalho executável. As prioridades significam:

- **P0** — necessário para primeiro vertical slice útil;
- **P1** — necessário para MVP confiável;
- **P2** — maturação pós-MVP;
- **P3** — expansão de plataforma/produto.

Labels sugeridas:

```text
type:feature
type:security
type:test
type:docs
type:refactor
type:provider
type:adapter
area:core
area:wordpress
area:reporting
area:rules
area:database
area:remote
priority:P0
priority:P1
priority:P2
priority:P3
```

---

## EPIC 0 — Fundação do Repositório

### WIRS-001 — Inicializar projeto Python

**Prioridade:** P0

Acceptance criteria:

- `pyproject.toml`;
- package importável;
- `wirs --help`;
- pytest configurado;
- lint/type check;
- versão mínima Python documentada.

### WIRS-002 — Criar boundaries de arquitetura

**P0**

Criar:

- `domain`;
- `application`;
- `ports`;
- `infrastructure`;
- `providers`;
- `adapters`;
- `reporting`.

Acceptance:

- domain não importa WordPress/provider/UI;
- architecture test impede dependência reversa.

### WIRS-003 — CI baseline

**P0**

- test;
- lint;
- type;
- package build;
- coverage.

### WIRS-004 — SECURITY.md

**P1**

Incluir:

- vulnerability reporting;
- política para malware samples;
- secret handling;
- provider security;
- no-target-write guarantee.

### WIRS-005 — ADR framework

**P1**

Criar template + ADRs iniciais deste documento.

---

## EPIC 1 — Target e Artifact

### WIRS-010 — Target model

**P0**

- LocalDirectoryTarget;
- root normalization;
- ID;
- immutable metadata.

### WIRS-011 — SafePath

**P0 / Security Critical**

Acceptance:

- relative path canônico;
- escape do root rejeitado;
- path com bytes/Unicode estranho tratado;
- separadores normalizados.

### WIRS-012 — Artifact model

**P0**

Tipos:

- file;
- dir;
- symlink;
- special.

Metadata:

- size;
- mode;
- owner/group quando disponível;
- inode/device quando disponível;
- timestamps;
- relative path.

### WIRS-013 — Local filesystem inventory

**P0**

- recursivo;
- hidden files;
- symlink não seguido;
- permission errors → Coverage;
- bounded memory.

### WIRS-014 — Special file safety

**P0**

FIFO/socket/device nunca lidos como file comum.

### WIRS-015 — Content/file type hints

**P1**

- extensão;
- binary/text;
- PHP content hint;
- mismatch extension/content.

---

## EPIC 2 — Evidence, Findings e Coverage

### WIRS-020 — Evidence schema

**P0**

- stable ID;
- kind;
- source;
- artifact ref;
- provenance;
- redaction state;
- serialization.

### WIRS-021 — Finding schema

**P0**

- rule ID;
- severity;
- confidence;
- evidence refs;
- category;
- attributes.

### WIRS-022 — Severity/confidence validation

**P0**

Impedir estados inválidos.

### WIRS-023 — Coverage model

**P0**

Estados:

- COMPLETE;
- PARTIAL;
- SKIPPED;
- UNAVAILABLE;
- FAILED;
- NOT_APPLICABLE.

### WIRS-024 — Scan Manifest

**P1**

Guardar:

- scanner version;
- scan ID;
- time;
- target metadata;
- config hash;
- providers;
- rules versions;
- resource profile.

### WIRS-025 — Schema versioning

**P1**

Canonical JSON deve separar `schema_version` de `scanner_version`.

---

## EPIC 3 — Artifact Reader, Hashing e Resource Control

### WIRS-030 — ArtifactReader read-only

**P0**

- `rb`;
- streaming;
- budget;
- cancellation;
- special-file guard.

### WIRS-031 — HashService

**P0**

- SHA-256;
- streaming;
- memoization por scan;
- suporte a upstream algorithms.

### WIRS-032 — Profiles

**P0**

- soft;
- balanced;
- fast.

### WIRS-033 — Scheduler central

**P1**

- bounded queue;
- worker limits;
- cancel;
- nenhum detector criando pool ilimitado.

### WIRS-034 — Large-file policy

**P1**

- hash_stream;
- metadata_only;
- skip_content;
- Coverage explícito.

### WIRS-035 — Benchmark harness

**P1**

Métricas de throughput/RSS/CPU.

---

## EPIC 4 — Baseline e Integrity

### WIRS-040 — Baseline Manifest schema

**P0**

- component ID;
- version;
- source;
- trust;
- file list;
- hashes;
- provenance.

### WIRS-041 — Manifest comparator

**P0**

Estados:

- match;
- mismatch;
- expected missing;
- unexpected.

### WIRS-042 — `baseline create` de diretório

**P1**

```bash
wirs baseline create ./clean-component
```

### WIRS-043 — Baseline de archive/ZIP

**P1**

Com:

- zip-slip defense;
- max expansion;
- sem lifecycle script;
- sem symlink escape.

### WIRS-044 — Trust state explícito

**P1**

Referência não confiável não gera linguagem de trusted integrity violation.

### WIRS-045 — Cache de baseline

**P2**

### WIRS-046 — Signed manifests

**P2**

---

## EPIC 5 — IOC e Rule Engine Genérico

### WIRS-050 — IOC schema

**P0**

Tipos iniciais:

- literal;
- domain;
- URL fragment;
- path fragment;
- SHA-256.

### WIRS-051 — Streaming literal scanner

**P0**

- chunk-boundary correct;
- occurrence cap;
- bounded context;
- binary safe.

### WIRS-052 — Regex IOC

**P1**

- validation;
- timeout/budget;
- explicit type.

### WIRS-053 — Zone/path policy engine

**P0**

Plataformas declaram zonas; core avalia predicados genéricos.

### WIRS-054 — Executable content detector

**P0**

Separar “conteúdo parece executável” de “executável é proibido nesta zona”.

### WIRS-055 — PHP heuristics v0

**P0**

Sinais:

- dynamic execution;
- encoding chains;
- process/file/network APIs;
- dynamic functions;
- encoded literals.

Regra: sinal isolado fraco não vira critical.

### WIRS-056 — Entropy detector

**P1**

### WIRS-057 — Rule metadata

**P1**

- false positives;
- maturity;
- rationale;
- references.

### WIRS-058 — `wirs rules validate`

**P1**

---

## EPIC 6 — WordPress Adapter

### WIRS-060 — WordPress discovery

**P0**

Sem DB obrigatório.

### WIRS-061 — WordPress zone classifier

**P0**

### WIRS-062 — Version/locale discovery segura

**P0**

Sem application bootstrap sempre que possível.

### WIRS-063 — WP-CLI doctor

**P0**

- path;
- version;
- availability;
- timeout.

### WIRS-064 — Core checksum provider

**P0**

- JSON normalization;
- include-root;
- Coverage;
- provider version.

### WIRS-065 — Plugin checksum provider

**P0**

- strict mode;
- unsupported/unverified distinto de failure.

### WIRS-066 — Premium/custom baseline mapping

**P1**

Config associa path/component ao manifest/package confiável.

### WIRS-067 — MU-plugin inspection

**P1**

### WIRS-068 — Upload executable policy

**P0**

- PHP/script detection;
- exceptions/allowlist.

### WIRS-069 — Special config collector

**P1**

- `.htaccess`;
- `.user.ini`;
- selected `wp-config` facts;
- suspicious include/persistence semantics.

### WIRS-070 — DB IOC provider

**P1**

- exact IOC;
- read-only;
- bounded context;
- table/column/PK.

### WIRS-071 — Privileged user inventory

**P2**

### WIRS-072 — WP-Cron inventory

**P2**

### WIRS-073 — Multisite

**P2**

---

## EPIC 7 — External Analyzer Providers

### WIRS-080 — ExternalAnalyzer contract

**P0**

- capabilities;
- availability;
- version;
- timeout;
- cancellation;
- normalization.

### WIRS-081 — YARA provider

**P1**

- compile;
- warnings;
- errors;
- matches;
- tags;
- namespace;
- graceful absence.

### WIRS-082 — Built-in YARA scaffolding

**P1**

### WIRS-083 — Wordfence CLI provider

**P1**

- discovery;
- workers;
- read-only scan;
- parser;
- no remediation;
- provider state.

### WIRS-084 — Semgrep provider

**P2**

### WIRS-085 — Provider sandbox

**P2**

---

## EPIC 8 — Reporting e Redaction

### WIRS-090 — Canonical JSON

**P0**

### WIRS-091 — Terminal reporter

**P0**

### WIRS-092 — Secret redaction

**P0**

### WIRS-093 — Markdown reporter

**P1**

### WIRS-094 — Atomic report writer

**P1**

### WIRS-095 — HTML report

**P2**

Security:

- escaping;
- CSP;
- sem remote dependencies default.

### WIRS-096 — SARIF

**P3**

---

## EPIC 9 — Diagnosis e Correlation

### WIRS-100 — Finding relation model

**P1**

### WIRS-101 — Correlation engine v0

**P1**

### WIRS-102 — DX001–DX004

**P1**

### WIRS-103 — Diagnosis renderer

**P1**

### WIRS-104 — Evidence graph export

**P3**

---

## EPIC 10 — CLI e Configuração

### WIRS-110 — `wirs scan`

**P0**

### WIRS-111 — Config schema

**P0**

- versioned;
- safe defaults;
- CLI overrides;
- validation clara.

### WIRS-112 — `wirs doctor`

**P0**

Checar:

- runtime;
- output dir;
- WP-CLI;
- YARA;
- Wordfence;
- config.

### WIRS-113 — verbose/debug

**P1**

Debug não vaza secret.

### WIRS-114 — Exit code policy

**P0**

### WIRS-115 — Progress/cancel

**P1**

---

## EPIC 11 — Hardening do Próprio Scanner

### WIRS-120 — CommandRunner obrigatório

**P0**

`subprocess` direto fora da camada permitida deve falhar architecture check.

### WIRS-121 — Subprocess output cap

**P0**

### WIRS-122 — Environment sanitizer

**P1**

### WIRS-123 — Symlink/special-file suite

**P0**

### WIRS-124 — Output injection tests

**P1**

### WIRS-125 — Archive sandbox

**P1**

### WIRS-126 — Regex fuzz/stress

**P1**

### WIRS-127 — SBOM/dependency release pipeline

**P2**

### WIRS-128 — Rule signing

**P3**

---

## EPIC 12 — Snapshot e Remote

### WIRS-130 — Snapshot directory workflow

**P1**

### WIRS-131 — Archive target adapter

**P2**

### WIRS-132 — SSH abstraction

**P2**

### WIRS-133 — SFTP ArtifactSource

**P2**

### WIRS-134 — Remote stat/hash optimization

**P2**

### WIRS-135 — Snapshot integrity manifest

**P2**

### WIRS-136 — Remote WP-CLI provider

**P2**

Somente depois de remote command policy segura.

---

## EPIC 13 — PHP Generic

### WIRS-140 — PHP discovery

**P3**

### WIRS-141 — Composer inventory

**P3**

### WIRS-142 — Composer lock/baseline

**P3**

### WIRS-143 — PHP generic zone policies

**P3**

### WIRS-144 — PHP runtime config

**P3**

### WIRS-145 — Generic PHP rules

**P3**

---

## EPIC 14 — Runtime HTTP

### WIRS-150 — HTTP collector

**P2**

### WIRS-151 — Redirect chain

**P2**

### WIRS-152 — External origin extraction

**P2**

### WIRS-153 — Request profiles

**P2**

### WIRS-154 — Runtime/filesystem correlation

**P2**

### WIRS-155 — Browser/network provider

**P3**

---

## EPIC 15 — AI Analysis Opcional

### WIRS-160 — AnalysisPacket

**P3**

### WIRS-161 — AI redaction gate

**P3**

### WIRS-162 — LLM provider interface

**P3**

### WIRS-163 — Prompt-injection-safe framing

**P3**

### WIRS-164 — AI recommendation view

**P3**

Invariante: IA não modifica fatos determinísticos.

---

# 18. /roadmap — Roadmap de Produto e Engenharia

O roadmap deve permitir uso rápido sem transformar o MVP em arquitetura descartável.

## Fase A — Skeleton / 0.0.x

Entregar:

- repo;
- CLI;
- Target/Artifact;
- Evidence/Finding/Coverage;
- inventory;
- reader;
- hash;
- JSON;
- security path tests.

Exit criterion:

```bash
wirs scan tests/fixtures/generic/clean_tree
```

produz report válido.

## Fase B — Primeiro WordPress Slice / 0.1.0

Entregar:

- WP discovery;
- zones;
- WP-CLI doctor;
- core checksum;
- plugin checksum;
- IOC scanner;
- executable-content;
- upload/protected policies;
- PHP heuristics v0;
- terminal;
- JSON;
- soft profile;
- E2E fixtures.

Esta é a primeira versão operacionalmente útil.

## Fase C — Custom Components + YARA / 0.2.0

- operator baselines;
- ZIP/package baseline;
- premium themes/plugins;
- YARA;
- Markdown report;
- benchmark;
- stronger redaction.

## Fase D — Application State / 0.3.0

- DB IOC search;
- selected config;
- MU-plugin enhancements;
- cron;
- privileged users quando seguro;
- diagnoses iniciais.

## Fase E — External Ecosystem / 0.4.0

- Wordfence CLI;
- Semgrep opcional;
- vulnerability provider interface;
- analyzer sandbox.

## Fase F — Snapshot/Remote / 0.5.0

- archive/snapshot;
- SFTP/SSH read-only;
- snapshot manifest;
- remote policy.

Objetivo: não depender de instalação do WIRS no host alvo.

## Fase G — Runtime / 0.6.0

- HTTP collector;
- redirect/headers/hash;
- origins;
- request variants;
- runtime correlation.

## Fase H — PHP Generic / 0.7.0

- generic PHP adapter;
- Composer;
- PHP config;
- generic policies.

Aqui o branding pode começar a migrar de “WordPress Incident Response Scanner” para plataforma genérica, mantendo WordPress como adapter maduro.

## Fase I — Product Hardening / 0.8–0.9

- signed releases;
- SBOM;
- schema compatibility;
- scan compare;
- rule update mechanism;
- HTML;
- local history/cache;
- performance;
- benign corpus ampliado.

## 1.0

1.0 deve significar estabilidade, não “possui todas as features imagináveis”.

Critérios:

- CLI estável;
- schema estável;
- WordPress adapter forte;
- generic filesystem engine;
- custom baseline;
- YARA/external provider;
- DB/application evidence;
- snapshot/remote workflow;
- security model documentado;
- robust tests;
- reproducible reports;
- upgrade policy.

## Pós-1.0

- Laravel;
- Joomla/Drupal conforme demanda;
- Linux host collectors;
- containers/Kubernetes;
- evidence graph;
- web control plane;
- fleet scanning;
- signed org policies;
- LLM analyst;
- remediation como boundary separado.

---

# 19. /improve-codebase-architecture — Plano de Evolução Arquitetural

O objetivo é um **modular monolith com boundaries rígidos**, não uma arquitetura distribuída prematura.

## 19.1 Direção das dependências

```text
CLI / Interface
      ↓
Application
      ↓
Domain
↑             ↑
Ports         |
↑             |
Infrastructure / Providers / Adapters
```

Regras:

- `domain` usa stdlib e value objects básicos;
- `application` depende de domain + ports;
- `infrastructure` implementa ports;
- `providers` implementam capabilities externas;
- `adapters/wordpress` adiciona semântica de plataforma;
- `reporting` consome model read-only;
- CLI faz composition root.

Proibido:

```text
Domain -> WordPress
Domain -> WP-CLI
Domain -> YARA
Domain -> Wordfence
Domain -> Rich
Domain -> MySQL
```

## 19.2 Hexagonal architecture sem burocracia

Criar port apenas em boundary real.

Ports justificáveis:

- `ArtifactSource`;
- `ArtifactReader`;
- `BaselineProvider`;
- `ExternalAnalyzer`;
- `PlatformAdapter`;
- `CommandRunner`;
- `DatabaseReader`;
- `Reporter`.

Não criar interface para cada função pura.

## 19.3 Application services

### `ScanOrchestrator`

Controla lifecycle e ordem.

### `InventoryService`

Produz Artifacts.

### `IntegrityService`

Resolve baselines e compara.

### `DetectionService`

Agenda internal detectors e analyzers.

### `CoverageService`

Mantém estado de capabilities.

### `CorrelationService`

Produz relações/diagnoses.

### `ReportService`

Gera model final e entrega a renderers.

## 19.4 Collector, Detector e Provider

### Collector

Obtém fatos.

Exemplos:

- filesystem inventory;
- DB search;
- cron listing;
- HTTP capture.

### Detector

Avalia Artifacts/Evidence e gera Findings.

Exemplos:

- baseline mismatch;
- executable in zone;
- obfuscation.

### Provider

Implementa uma capability, muitas vezes usando ferramenta externa.

Exemplos:

- WP-CLI;
- YARA;
- Wordfence.

Provider output deve atravessar anti-corruption layer.

## 19.5 Anti-corruption layer

Provider-specific schema não pode vazar.

Ruim:

```python
if wf_result["signature_id"]:
    ...
```

em application code.

Bom:

```python
ProviderFinding(
    provider_id="wordfence-cli",
    external_rule_id="...",
    severity=...,
    evidence=...,
)
```

## 19.6 Error model

```text
WirsError
├── ConfigurationError
├── TargetError
├── SecurityBoundaryError
├── ProviderError
│   ├── ProviderUnavailable
│   ├── ProviderTimeout
│   ├── ProviderInvalidOutput
│   └── ProviderExecutionError
├── BaselineError
├── RulePackError
└── InternalInvariantError
```

Recoverable errors viram Coverage/Provider status.

`InternalInvariantError` normalmente aborta.

## 19.7 Provider health

```yaml
provider:
  id: yara
  status: available
  version: ...
  capabilities:
    - signature_scan
  runs:
    - status: completed
      artifacts_considered: 1200
      duration_ms: ...
```

## 19.8 Config precedence

```text
safe defaults
  < config file
  < environment não sensível
  < CLI flags
```

Secrets não devem ser CLI args quando shell history/process list puder expô-los.

## 19.9 Rules como data versus código

Exemplo declarativo futuro:

```yaml
id: WP.UPLOAD.EXECUTABLE
platform: wordpress
predicate:
  all:
    - zone: wp-content-uploads
    - artifact_content_type: executable_php
severity: high
confidence: high
```

Porém não construir DSL gigante no MVP.

Primeiro usar classes/predicados explícitos. Extrair DSL somente quando patterns realmente se repetirem.

## 19.10 Pipeline de leitura compartilhada

Evitar uma leitura por detector.

```text
Artifact
  ↓
stat/metadata
  ↓
stream
  ├── SHA-256
  ├── text/binary hint
  ├── IOC literal
  ├── PHP hint
  └── feature extraction
          ↓
       FeatureSet
          ↓
    heuristic rules
```

YARA/Wordfence ainda podem reler arquivos, mas detectores internos compartilham I/O.

## 19.11 Persistência interna

MVP:

- memória;
- JSON.

Posteriormente SQLite para:

- history;
- hash cache;
- scan compare;
- baseline metadata;
- findings.

PostgreSQL/control plane só quando houver fleet/multi-user real.

## 19.12 Incremental scan

Pós-MVP.

Nunca confiar somente em `mtime`.

Possíveis hints:

- size;
- ctime;
- inode;
- hash cache;
- periodic full scan.

Relatório deve indicar quando Evidence veio de cache.

## 19.13 Schema evolution

Separar:

```json
{
  "schema_version": "1.0",
  "scanner_version": "0.3.2"
}
```

Mudança breaking de campo → schema major.

Golden tests garantem compatibilidade.

## 19.14 Logging

Separar:

- progress UI;
- debug log;
- Evidence/report.

Nunca depender do log como única evidência.

Debug não imprime snippets/secrets por padrão.

## 19.15 Observability futuro

Métricas possíveis:

- throughput;
- provider latency;
- errors;
- Coverage ratio;
- rule hits;
- RSS;
- CPU.

Sem telemetry remota default. Qualquer telemetry futura deve ser opt-in.

## 19.16 Architecture tests

Exemplos:

- `domain` não pode importar `wordpress`, `yara`, `wordfence`, `rich`, `mysql`;
- detectors não chamam subprocess;
- subprocess somente via CommandRunner;
- provider não possui write target API;
- scanner não possui remediation import.

## 19.17 Quando refatorar

### Criar nova abstraction

Somente quando duas implementações realmente variarem e application começar a conhecer vendor.

### Criar rule DSL

Quando 5–10 regras apresentarem padrão repetitivo real.

### Introduzir SQLite

Quando history/compare/cache forem requisitos reais.

### Introduzir web UI

Quando navegação de múltiplos scans/fleet justificar.

### Introduzir server/control plane

Quando houver scheduling central, múltiplos usuários/agentes e storage compartilhado.

### Introduzir Rust/Go hot path

Somente após profiling provar gargalo em Python e após otimizar I/O/provider orchestration.

---

# 20. /scaffold-exercise — Exercício Guiado de Implementação

Esta sequência deve ser usada para validar arquitetura com vertical slices pequenos. Pode ser entregue ao Codex como uma série de tasks independentes.

## Exercise 1 — Domain primitives

Implementar:

- `Severity`;
- `ConfidenceClass`;
- `Target`;
- `Artifact`;
- `Evidence`;
- `Finding`;
- `CoverageEntry`.

Restrições:

- immutable quando razoável;
- serialização explícita;
- nenhum import WordPress;
- nenhum I/O dentro do domain object.

Tests:

- invalid enum rejeitado;
- Evidence ref obrigatório onde aplicável;
- round-trip;
- Coverage validado.

---

## Exercise 2 — Filesystem inventory seguro

Implementar `LocalArtifactSource`.

Fixture:

```text
root/
  a.php
  .hidden
  dir/b.txt
  link-out -> /tmp
  fifo
```

Acceptance:

- files presentes;
- hidden presente;
- link não atravessado;
- FIFO não aberto;
- path sempre relativo seguro.

---

## Exercise 3 — Hash uma vez

Implementar `HashService` usando ArtifactReader.

Tests:

- known SHA-256;
- duas requisições → uma leitura real;
- permission/cancel.

---

## Exercise 4 — JSON report

Implementar primeiro canonical report.

Não incluir file content bruto.

Criar golden fixture.

---

## Exercise 5 — PlatformAdapter

Contrato:

```python
class PlatformAdapter(Protocol):
    id: str
    def discover(...): ...
    def classify(...): ...
    def capabilities(...): ...
```

Implementar apenas discovery WordPress.

---

## Exercise 6 — WordPress zones

Criar classification tests para:

- core;
- root-special;
- plugin;
- theme;
- mu-plugin;
- uploads;
- cache;
- other.

---

## Exercise 7 — ExecutableInSensitiveZone

Separar:

1. detector que identifica conteúdo executável;
2. policy que avalia se ele é esperado na zone.

Isso permite reuso futuro em Laravel/PHP generic.

---

## Exercise 8 — IOC scanner

Implementar literal scan streaming.

Testar IOC cruzando boundary de chunks.

Adicionar occurrence cap/context cap.

---

## Exercise 9 — CommandRunner

Implementar:

- `shell=False`;
- argv;
- timeout;
- output cap;
- env sanitizer;
- cwd;
- cancel.

Security test:

```text
filename = "x;touch /tmp/pwned"
```

deve continuar literal, sem execução.

---

## Exercise 10 — `wirs doctor` / WP-CLI

Detectar:

- available;
- unavailable;
- execution failure;
- version.

Ainda sem scan WordPress.

---

## Exercise 11 — Core checksum provider

Fake provider parser primeiro.

Depois integration real.

Malformed JSON = ProviderInvalidOutput + Coverage degraded.

---

## Exercise 12 — Plugin checksum provider

Reutilizar mesma arquitetura.

Objetivo é provar que application não conhece formato WP-CLI específico.

---

## Exercise 13 — ScanOrchestrator v0

Pipeline real:

```text
inventory
→ platform discovery
→ zones
→ IOC/policy
→ WP checksum providers
→ Coverage
→ Report
```

Comando de aceitação:

```bash
wirs scan tests/fixtures/wordpress/modified_core --format json
```

---

## Exercise 14 — Redaction

Fixtures:

- DB password fake;
- API token fake;
- private key fake;
- benign random ID.

Acceptance:

- secrets somem;
- hashes/IDs normais continuam.

---

## Exercise 15 — YARA provider

Objetivo:

- rule compile;
- match;
- provider missing;
- rule error;
- Coverage.

---

## Exercise 16 — Operator baseline

Criar manifest de diretório/package confiável.

Security:

- no symlink escape;
- no scripts;
- package hash;
- provenance.

---

## Exercise 17 — DB IOC search

Primeira versão:

- IOC exato;
- table/column/PK;
- bounded context;
- redaction;
- read-only.

---

## Exercise 18 — Diagnosis v0

Correlacionar baseline mismatch + signature/heuristic no mesmo artifact.

Diagnosis só pode referenciar Finding IDs existentes.

---

# 21. Plano Fast-Track para o Primeiro Uso Operacional

## FT-1 — Core seguro

Issues:

- WIRS-001
- WIRS-002
- WIRS-010
- WIRS-011
- WIRS-012
- WIRS-013
- WIRS-020
- WIRS-021
- WIRS-023
- WIRS-030
- WIRS-031
- WIRS-090
- WIRS-110

Resultado:

```text
filesystem inventory + JSON + coverage
```

## FT-2 — Integridade WordPress

- WIRS-060
- WIRS-061
- WIRS-063
- WIRS-064
- WIRS-065
- WIRS-068

Resultado:

```text
WordPress discovery
+ official core/plugin integrity
+ sensitive zone policy
```

## FT-3 — Detection

- WIRS-050
- WIRS-051
- WIRS-054
- WIRS-055
- WIRS-091
- WIRS-092

Resultado:

```text
IOC + heuristics + human report
```

## FT-4 — Componentes customizados

- WIRS-040
- WIRS-041
- WIRS-042
- WIRS-043
- WIRS-066

Resultado:

```text
premium/custom plugin/theme baseline verification
```

Depois desse ponto, usar a ferramenta em múltiplos fixtures e snapshots conhecidos antes de adicionar complexidade.

---

# 22. Definition of Ready de Feature

Uma feature só entra em implementação quando:

1. problema está descrito;
2. sabemos se pertence ao core, adapter ou provider;
3. input/output estão definidos;
4. security boundary foi analisada;
5. falsos positivos foram considerados;
6. custo de recurso foi considerado;
7. fixtures foram definidos;
8. documentação externa foi verificada;
9. acceptance criteria existem;
10. não introduz remediation implicitamente.

# 23. Definition of Done de Detector

Detector finalizado quando:

- fixture positivo;
- pelo menos dois negativos benignos quando aplicável;
- severity/confidence documentadas;
- Evidence suficiente;
- resource budget;
- hostile input test;
- schema normalizado;
- rule list/docs;
- sem secret leakage;
- Coverage/applicability definida.

# 24. Definition of Done de Provider

Provider finalizado quando:

- docs oficiais registradas;
- versão testada;
- availability check;
- invocation bounded;
- malformed output tests;
- timeout test;
- ausência degrada Coverage;
- provenance/version;
- target mutation revisada;
- data egress documentado;
- licença documentada.

---

# 25. Invariantes Arquiteturais Críticas

Estas regras devem estar também em `ARCHITECTURE.md` e, quando possível, virar testes automáticos.

1. `scan` não escreve no target.
2. Finding não existe sem Evidence ou provenance explícita de provider.
3. Provider ausente nunca vira Coverage completo.
4. Platform concept não vaza para domain genérico.
5. Detector não executa source do target.
6. Target-controlled data nunca é interpolado em shell command.
7. Componente sem baseline não é malicioso por definição.
8. AI output não é Evidence determinística.
9. Symlink não é seguido fora do root por default.
10. Report não deve expor secrets conhecidos.
11. External remediation não participa de `scan`.
12. Detector não controla concurrency ilimitada.
13. Coverage gap é visível.
14. Canonical data é independente da UI.
15. Remover adapter WordPress não pode quebrar testes do core genérico.

---

# 26. Riscos de Produto e Engenharia

## Risco 1 — Virar clone de antivírus

Mitigação:

- integrar mature signature engines;
- focar em evidence/integrity/correlation.

## Risco 2 — Falso positivo excessivo

Mitigação:

- signal ≠ finding;
- severity ≠ confidence;
- benign corpus;
- rule maturity.

## Risco 3 — “Nenhum finding” virar “clean”

Mitigação:

- Coverage obrigatório;
- wording policy.

## Risco 4 — Derrubar shared hosting

Mitigação:

- soft profile;
- streaming;
- bounded workers;
- snapshot mode.

## Risco 5 — Target explorar o scanner

Mitigação:

- hostile-input model;
- no execution;
- safe parser;
- symlink/archive/regex controls.

## Risco 6 — WP-CLI executar código comprometido

Mitigação:

- command safety classification;
- `safe_only`.

## Risco 7 — Overengineering

Mitigação:

- vertical slice;
- nenhum web server/plugin marketplace/graph DB no MVP.

## Risco 8 — Arquitetura genérica abstrata demais

Mitigação:

- WordPress como reference adapter;
- abstração somente em variation points reais.

## Risco 9 — LLM virar oracle

Mitigação:

- optional provider;
- evidence-first;
- human/deterministic confirmation.

## Risco 10 — Baseline “limpo” não ser confiável

Mitigação:

- trust state explícito;
- provenance;
- package hash;
- assinatura futura.

---

# 27. Métricas de Sucesso

## Engenharia

- deterministic fixture accuracy;
- zero target writes;
- bounded RSS;
- provider failure isolation;
- stable schema;
- false-positive rate em benign corpus.

## Operação

- tempo até primeiro finding útil;
- percentual coberto por trusted integrity;
- findings com Evidence acionável;
- reprodutibilidade via snapshot;
- redução de trabalho manual.

## Produto

- novos adapters sem mudança no domain;
- providers integrados sem branch vendor no application;
- reports compatíveis entre versões;
- scans que não exigem instalação no target.

---

# 28. Decisões Técnicas Iniciais Recomendadas

```yaml
language: Python 3.11+
architecture: modular-monolith / ports-and-adapters
canonical_report: JSON
cli: Typer-or-Click
terminal: Rich-optional
tests: pytest
property_tests: Hypothesis
lint_format: Ruff
internal_hash: SHA-256
wp_integrity_provider: WP-CLI
signature_provider: YARA optional
malware_provider: Wordfence CLI optional
static_analysis_provider: Semgrep later
symlinks: do-not-follow
scan_mode: read-only
raw_evidence_storage: false
llm: disabled by default
remediation: out-of-scope
remote: post-first-MVP
```

Biblioteca específica pode mudar. Os boundaries de segurança/domínio não devem mudar sem ADR.

---

# 29. Exemplo de Lifecycle Completo

```text
$ wirs scan /srv/www/example --profile soft --report ./scan.json

1. Config validada.
2. Target root normalizado.
3. Scan Manifest criado.
4. Inventory executado.
5. Symlinks registrados sem traversal.
6. Platform discovery identifica WordPress.
7. Zones classificadas.
8. Stream interno calcula hashes/features/IOCs.
9. Core checksum provider executa se disponível.
10. Plugin checksum provider executa.
11. Operator baselines verificam custom components.
12. Policies executam.
13. YARA opcional executa.
14. External analyzer opcional executa.
15. Coverage fecha.
16. Correlation produz Diagnoses.
17. Redaction final valida report.
18. JSON escrito atomicamente fora do target.
19. Terminal summary renderizado.
20. Exit code reflete findings + completude.
```

Nenhuma etapa de `scan` remedia.

---

# 30. Direção Final do Produto

```text
                WIRS / Generic IR Scanner
                         │
           ┌─────────────┴─────────────┐
           │                           │
    Generic Evidence Core       Platform Knowledge
           │                           │
    ┌──────┼──────┐          ┌────────┼────────┐
Filesystem Baseline Rules   WordPress PHP Laravel ...
    │      │       │
    └──────┼───────┘
           │
      Provider Layer
  ┌────────┼───────────────┐
WP-CLI   YARA   Wordfence  Semgrep ...
           │
           ▼
   Evidence + Findings
           │
           ▼
      Correlation
           │
           ▼
       Diagnoses
           │
           ▼
Terminal / JSON / Markdown / HTML / future API
```

O diferencial de longo prazo não deve ser “temos mais regex”.

O diferencial deve ser:

- integridade confiável;
- explainable findings;
- Coverage;
- evidence correlation;
- operação segura sobre target hostil;
- adapters de plataforma;
- reports reproduzíveis;
- interoperabilidade com analyzers externos;
- IA opcional sem substituir verdade determinística.

Assim o MVP WordPress deixa de ser um projeto descartável e se torna a primeira implementação de uma plataforma muito maior.

---

# Apêndice A — Referências Externas Consultadas

As integrações devem ser revalidadas quando forem implementadas/atualizadas.

1. WordPress Developer Resources — `wp core verify-checksums`  
   https://developer.wordpress.org/cli/commands/core/verify-checksums/

2. WordPress Developer Resources — `wp plugin verify-checksums`  
   https://developer.wordpress.org/cli/commands/plugin/verify-checksums/

3. WordPress Developer Resources — `wp db search`  
   https://developer.wordpress.org/cli/commands/db/search/

4. WordPress Developer Resources — `wp cron event list`  
   https://developer.wordpress.org/cli/commands/cron/event/list/

5. WordPress Developer Resources — `wp config list`  
   https://developer.wordpress.org/cli/commands/config/list/

6. WordPress Developer Resources — Hardening WordPress  
   https://developer.wordpress.org/advanced-administration/security/hardening/

7. WordPress Developer Resources — File Permissions  
   https://developer.wordpress.org/advanced-administration/server/file-permissions/

8. Wordfence CLI repository  
   https://github.com/wordfence/wordfence-cli

9. Wordfence CLI docs/produto  
   https://www.wordfence.com/products/wordfence-cli/

10. Wordfence CLI malware scan examples  
    https://github.com/wordfence/wordfence-cli/blob/main/docs/malware-scan/Examples.md

11. YARA  
    https://yara.readthedocs.io/

12. Semgrep  
    https://semgrep.dev/docs/writing-rules/

13. Tree-sitter  
    https://tree-sitter.github.io/tree-sitter/using-parsers/

---

# Apêndice B — Checklist do Release 0.1.0

## Repository

- [ ] Python package
- [ ] CI
- [ ] architecture tests
- [ ] SECURITY.md
- [ ] ADRs

## Core

- [ ] Target
- [ ] SafePath
- [ ] Artifact
- [ ] inventory
- [ ] ArtifactReader
- [ ] hashing
- [ ] Evidence
- [ ] Finding
- [ ] Coverage

## WordPress

- [ ] discovery
- [ ] zones
- [ ] core checksum
- [ ] plugin checksum
- [ ] upload policy

## Detection

- [ ] literal IOC
- [ ] SHA-256 IOC
- [ ] executable hints
- [ ] PHP heuristic pack v0

## Reporting

- [ ] JSON
- [ ] terminal
- [ ] secret redaction
- [ ] atomic writer

## Tests

- [ ] clean fixture
- [ ] modified core
- [ ] unexpected protected file
- [ ] custom plugin unverified
- [ ] PHP in uploads
- [ ] hostile filename
- [ ] symlink escape
- [ ] provider unavailable
- [ ] soft benchmark

## Security

- [ ] `shell=False`
- [ ] no target writes E2E
- [ ] no symlink traversal
- [ ] no secrets no report
- [ ] provider output escaped

Com estes itens concluídos, o projeto pode receber a primeira tag operacional `0.1.0`.
