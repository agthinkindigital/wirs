# Gate 0.2.0 — Plano Operacional

**Data da reconstrução:** 2026-10-02  
**Repositório:** `agthinkindigital/wirs`  
**Branch de trabalho:** `develop`  
**Resultado atual:** NÃO ELEGÍVEL para promoção a `main`

Este documento registra a reconstrução factual e o plano verificável para levar o
WIRS de `main` `0.1.0` ao gate `0.2.0`. Não autoriza promoção, alteração de
versão, fechamento de Epic ou implementação de feature.

## Limites desta execução

- `main` não será alterada.
- `pyproject.toml`, `src/wirs/__init__.py` e qualquer fonte de versão permanecem
  em `0.1.0`.
- `CHANGELOG.md` não recebe trabalho ainda não promovido.
- Nenhuma feature, regra ou correção funcional será implementada nesta fase.
- Correções puramente de formatação/CI só podem ocorrer na fase operacional
  seguinte, com commit próprio e verificação reproduzível.

## Fontes e precedência

1. `AGENTS.md` e suas invariantes.
2. `docs/PRODUCT-CHARTER.md` para identidade, limites e horizonte.
3. `CONTEXT.md` para vocabulário.
4. `WIRS_MASTER_SPEC_PT-BR.md` para contratos e critérios técnicos.
5. `docs/ARCHITECTURE.md` e ADRs aplicáveis.
6. GitHub Issues para escopo, aceite, dependências e estado.
7. Código e testes para o que realmente funciona.
8. `ORCHESTRATOR-ROADMAP.md` para ordem estratégica.
9. `ESTADO_ORQUESTRATOR.md` para snapshot, nunca para substituir o tracker.

Quando uma fonte histórica diverge do tracker ou do checkout, a divergência é
registrada; a história não é reescrita silenciosamente.

## Reconstrução factual

### Branches e release

| Item | Evidência | Estado |
|---|---|---|
| Release publicada | tag `v0.1.0`, release GitHub de 2026-09-10 | confirmado |
| `main` | `a8cdb32`, ainda declara pacote `0.1.0` | linha publicada |
| `develop` | `2373012`, `origin/develop` sincronizada | linha de trabalho |
| Relação entre branches | `main...develop`: `ahead_by=42`, `behind_by=6`, `status=diverged` | bloqueio de promoção |
| Versão do pacote | `pyproject.toml` e `src/wirs/__init__.py`: `0.1.0` | correto nesta fase |
| Release `0.2.0` | inexistente | correto nesta fase |

Antes de qualquer promoção, a divergência de histórico precisa ser reconciliada
explicitamente em `develop` e auditada novamente. Não presumir fast-forward.

### Tracker confirmado

- Fechadas: #65, #66, #67, #70, #76, #77 e #80.
- Abertas e fora do escopo mínimo de `0.2.0`: #68, #69, #71–#75, #78, #79,
  #81 e #88. #70, #76 e #80 estão fechadas antecipadamente; seus follow-ons
  não entram no gate mínimo.
- P1 aberto com potencial de bloquear a release: #84, falso negativo de
  webshell por `dynamic_function + file_network`.
- P1 aberto com potencial de bloquear a release: #87, diagnoses vazias no caso
  real de Ofir apesar de #77 fechada.
- #86 permanece aberta e descreve contextos de Evidence/HTML; a capability já
  existe em parte, mas o aceite do tracker não está formalmente concluído.
- Epics E02, E03, E05, E06, E07, E08, E09, E10, E12 e E13 continuam abertas.
  E04 está fechada. Epic aberta não é automaticamente blocker se o plano
  delimitar explicitamente o subconjunto que compõe a versão.

### Verificação técnica atual

No checkout do candidato `2373012`:

```text
uv run pytest tests -q       -> 241 passed, 5 skipped
uv run ruff check .          -> passou
uv run ruff format --check . -> falhou em 4 arquivos
uv run mypy src/             -> Success: no issues found in 64 source files
uv run python -m build       -> wirs-0.1.0.tar.gz e wirs-0.1.0-py3-none-any.whl
```

A CI `37041876058` confirma que o job YARA passou, mas os jobs `test` falharam
no format check; os demais jobs da matriz foram cancelados. Portanto, não existe
CI verde para o commit candidato atual.

Arquivos que o format check reportou:

- `src/wirs/cli/app.py`
- `src/wirs/reporting/canonical.py`
- `tests/integration/test_scan_report.py`
- `tests/unit/test_yara_provider.py`

## Escopo reconstruído do gate

O Master Spec define a Fase C/`0.2.0` como operator baselines, baseline ZIP,
YARA no `scan`, artifact canônico, Markdown, benchmark e redaction reforçada.
O roadmap operacional agrupa isso com M4, content analysis bounded e Diagnosis
file-centric. O gate deve ser avaliado por subconjuntos, não por fechamento
artificial de Epics que possuem backlog posterior.

### M3 — Artifact + YARA

| Capacidade | Issues/fonte | Evidência atual | Situação do gate |
|---|---|---|---|
| Baselines, trust, comparator, ZIP e assinatura | #48–#52, #56–#58 / E04 | Epic E04 fechada; testes existentes | tecnicamente atendido |
| Artifact canônico schema 2.0 | #65 / E02 | fechado; goldens, refs, redaction e roundtrip no checkout | tecnicamente atendido; checklist/Epic precisam sincronização |
| ExternalAnalyzer/YARA no scan | #60–#62, #66 / E07 | fechados; CI YARA atual passa | tecnicamente atendido; checklist/Epic precisam sincronização |
| Markdown e reporting base | #28, #40, #41, #53, #59 / E08 | fechados; testes existentes | tecnicamente atendido; subset precisa ser explicitado |

### M4 — Content analysis + Diagnosis

| Capacidade | Issues/fonte | Evidência atual | Situação do gate |
|---|---|---|---|
| Leitura bounded, budgets e cancelamento | #26, #27, #67 / E03 | #67 fechada; benchmark e testes publicados | tecnicamente atendido; checklist/Epic estão stale |
| Regras/detecção necessárias ao fluxo | #36–#39 / E05 | slices fechadas; critérios da Epic ainda desmarcados | precisa auditoria de aceite da Epic |
| Diagnosis file-centric | #77 / E09 | fechada; domínio, refs, hipóteses e testes existentes | tecnicamente atendido; #87 é regressão P1 aberta |

### Fora do gate mínimo

- #70/PHP genérico, #76/relações e #80/HTML são capacidades antecipadas ou
  de horizonte posterior; não substituem M3/M4 e não devem alterar o número da
  versão sozinhas.
- #68/#69 são M5/`0.3.0`; #71–#75 são M6; #78/#79 são follow-ons de Diagnosis
  e dependem de capacidades posteriores; #81 é PDF opcional.
- #84 e #87 não pertencem ao conjunto histórico original de Issues de M3/M4,
  mas são riscos P1 conhecidos. Pela regra de QA de release, entram como
  bloqueadores até haver decisão formal e evidência de não regressão.

## Matriz de gates

| Gate | Saída verificável | Estado | Próxima ação |
|---|---|---|---|
| A0. Escopo congelado | Lista M3/M4 aprovada, sem puxar M5–M7 | parcial | registrar aprovação do subconjunto e blockers P1 |
| A1. Histórico reproduzível | `develop` reconciliada com `main`, sem alterar `main` | bloqueado | planejar merge/reconciliação explícita e novo CI |
| A2. Tracker coerente | Aceites das Issues e checklists das Epics refletem código publicado | bloqueado | comentários de evidência e decisão do maintainer; não fechar automaticamente |
| A3. M3 | artifact 2.0, baselines, YARA, Markdown e redaction validados | tecnicamente atendido | QA formal da DAG e atualização dos checklists |
| A4. M4 | bounded analysis e Diagnosis file-centric reproduzíveis | tecnicamente atendido com risco | resolver/aceitar formalmente #84 e #87 |
| A5. QA local | pytest, Ruff, format, mypy, security e build | bloqueado | corrigir os 4 arquivos de formatação e repetir todos os checks |
| A6. CI | matriz Python, YARA, build e artefacto no commit candidato | bloqueado | push do candidato e aguardar todos os jobs verdes |
| A7. Documentação | roadmap, estado, versão e guias sem drift; Changelog ainda histórico | bloqueado | atualizar somente após decisões do tracker e QA |
| A8. Release candidate | versão 0.2.0 preparada, sem promover | não iniciado | só depois de A0–A7; ainda não alterar versão nesta fase |
| A9. Promoção | `main`, tag, release, Changelog e artefatos reproduzíveis | proibido nesta run | execução futura separada e autorizada |

## Plano de execução após a reconstrução

1. **Normalizar o candidato:** aplicar apenas a formatação exigida pelo CI,
   revisar o diff e publicar um commit de manutenção em `develop`.
2. **Reconciliar histórico:** incorporar a linha publicada de `main` em
   `develop` pela estratégia aprovada pelo maintainer; não fazer reset, force
   push ou alteração direta de `main`.
3. **Fechar a matriz M3/M4:** publicar evidências por Issue, marcar apenas
   critérios realmente verificados e registrar que as Epics continuam abertas
   quando tiverem backlog fora de `0.2.0`.
4. **Tratar P1:** reproduzir #84 e #87 com fixtures equivalentes, ou registrar
   decisão explícita de bloqueio/escopo. Sem isso, o release gate permanece
   vermelho.
5. **Executar QA de DAG:** suíte completa, security tests, golden tests,
   formatação, mypy, build, matriz Python/YARA e verificação de conteúdo do
   wheel. Guardar SHA, URLs de CI e contagens reais.
6. **Sincronizar documentação:** atualizar snapshot de estado, pendências do
   roadmap e esta auditoria com addendum datado. Não registrar no Changelog o
   que ainda não chegou à `main`.
7. **Reavaliar elegibilidade:** emitir uma nova tabela A0–A8. Só se todos os
   gates passarem poderá ser preparado um plano separado de promoção.

## Critério de saída da Fase A

A Fase A termina quando:

- o escopo M3/M4 e os não-objetivos estão aprovados;
- o desvio `main`/`develop` está registrado com estratégia de reconciliação;
- cada capability tem Issue, teste, evidência e responsável identificáveis;
- #84/#87 têm decisão formal ou permanecem explicitamente bloqueando;
- a falha de formatação da CI está registrada como manutenção pendente;
- nenhum documento chama `develop` de release publicada;
- nenhum commit de promoção, mudança de versão ou feature nova ocorreu.

Até esses critérios serem satisfeitos, o estado normativo é:

> `develop` atualizado, `main` em `0.1.0`, gate `0.2.0` não elegível.

## Decisões das Fases B e C — 2026-10-02

### `0.2.0` versus `0.1.1`

O alvo permanece **`0.2.0`**, não `0.1.1`. O conjunto inclui capacidades
coerentes de M3/M4 e evolução breaking do artifact canônico para schema 2.0;
isso não é uma correção compatível de patch. A versão instalada/publicada
continua `0.1.0` até uma promoção formal. Nenhum número será alterado nesta
execução.

### Promoção `develop` → `main`

Não haverá promoção nesta execução. A promoção futura só poderá ocorrer depois
de A0–A8, com a divergência entre as branches reconciliada explicitamente,
commit candidato reproduzível, CI verde, QA de release, atualização coordenada
de versão/README/Changelog e tag/release. `main` permanece em `0.1.0`.

### Issues críticas e bloqueios

| Issue | Estado confirmado | Decisão desta execução |
|---|---|---|
| #68 | OPEN; M5/`0.3.0` | não implementar nem fechar; permanece fora de `0.2.0` |
| #75 | OPEN; adapter de logs | não implementar; bloqueia #78 e permanece fora de M3/M4 |
| #78 | OPEN; bloqueada por #75 | não implementar nem reordenar para antes do gate atual |
| #79 | OPEN; depende de #76 | não implementar; segue após a sequência de Diagnosis |
| #84 | OPEN/P1; falso negativo de webshell | não implementar; blocker de segurança requer decisão e evidência futura |
| #87 | OPEN/P1; diagnoses vazias no caso Ofir | não implementar; blocker de Diagnosis requer decisão e evidência futura |

Nenhuma Issue ou Epic controversa será fechada automaticamente. Comentários de
evidência, quando feitos em execução futura, não equivalem a fechamento.

### Sequência mínima após esta execução

1. Manter a falha de `ruff format --check` registrada; não formatar arquivos
   nesta run.
2. Reconciliar `main` e `develop` sem alterar `main`, usando estratégia aprovada
   pelo maintainer.
3. Auditar os critérios e checklists de M3/M4 sem encerrar Epics com backlog
   posterior.
4. Obter decisão formal sobre #84 e #87; enquanto isso, o gate permanece
   bloqueado.
5. Executar novamente QA local e CI no SHA candidato, tratando format como
   requisito obrigatório e falha como falha.
6. Reavaliar A0–A8; somente depois preparar uma execução separada de promoção.

### Riscos aceitos e não resolvidos

- A CI final pode permanecer vermelha exclusivamente por formatação; isso não
  será reportado como sucesso.
- `main` e `develop` estão divergentes, portanto um candidato não é
  automaticamente reproduzível por fast-forward.
- Checklists de Epics e Issues fechadas ainda contêm estado histórico stale;
  sincronizar sem evidência seria falsificar o gate.
- #84 representa risco de falso negativo de segurança e #87 representa falha de
  priorização/Diagnosis em caso real.
- Capabilities antecipadas (#70, #76 e #80) não podem substituir o conjunto
  M3/M4 nem antecipar a versão.
