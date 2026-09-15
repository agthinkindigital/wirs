# ADR-011 - Bundle forense local antes de remoto

- **Status:** aceito
- **Data:** 2026-09-14

## Contexto

Uma investigação real exigiu combinar uma árvore web, archives, logs de painel,
access logs, logs PHP, hashes e horários. A coleta foi feita por SSH porque o
analista trabalhava manualmente, não porque o produto precise controlar hosts
remotos. A proposta de agentes residentes, streaming e resposta automática
transformaria o WIRS em SIEM/EDR e quebraria a menor promessa útil do produto.

## Decisão

Até 1.0, o WIRS continua um scanner forense local/offline. Ele é instalado no
servidor ou no PC do analista e lê somente conteúdo já acessível nessa máquina.
A unidade reproduzível para investigações heterogêneas será o **Incident
Bundle**: uma pasta local, somente leitura, com manifesto versionado que declara
webroots, logs, snapshots, archives, papéis e provenance.

"Offline" aqui qualifica a aquisição do target: o scanner não busca arquivos
no host investigado. Providers opcionais podem acessar serviços upstream quando
habilitados; esse acesso deve ser explícito, seguro e refletido no Coverage.

SSH/SFTP, coleta ativa de rede, agentes residentes, message bus, dashboard
central, ML e resposta automática não são dependências do produto até 1.0. Se
forem construídos depois, usarão seams separados e consumirão/produzirão o mesmo
modelo canônico.

## Alternativas

- Implementar SSH/SFTP antes dos parsers locais: rejeitado porque mistura
  transporte, aquisição e análise antes de provar a semântica sobre fixtures.
- Construir plataforma contínua agora: rejeitado porque amplia privilégios,
  operação e superfície de ataque sem ser necessário para reproduzir a perícia.
- Receber muitos paths avulsos por flags: rejeitado como contrato principal
  porque reduz portabilidade e reprodutibilidade da investigação.

## Consequências

- Archive/snapshot local e PHP genérico são antecipados no roadmap.
- Logs locais ganham Evidence temporal, Coverage de retenção e correlação.
- Remote sai do caminho crítico pré-1.0; E12 passa a tratar bundle/archive local.
- Relatórios forenses derivam do JSON canônico; nenhuma view consulta o alvo.
- Remediação permanece fora de `scan`, conforme ADR-002.
