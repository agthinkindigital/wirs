# ADR-007 — LLM fora do pipeline determinístico

- **Status:** aceito
- **Data:** 2026-09-08

## Contexto

LLM pode ajudar a classificar e sugerir próximos checks, mas output de IA
não é evidência e prompt injection via código do alvo é risco real.

## Decisão

LLM é `AnalysisProvider` opcional, desabilitado por padrão: recebe apenas
`AnalysisPacket` redigido, nunca modifica fato determinístico sem nova
evidência/regra ou confirmação humana. Scan nunca depende de IA.

## Consequências

- Conteúdo do alvo é marcado como não-confiável no prompt.
- Sem `.env`, keys, `wp-config.php` bruto, dumps ou árvore sem filtro no packet.
