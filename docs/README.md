# Documentação do WIRS

- `WIRS_MASTER_SPEC_PT-BR.md` (raiz): especificação viva — autoridade de produto e arquitetura.
- `CONTEXT.md` (raiz): glossário do domínio.
- `docs/adr/`: decisões arquiteturais (formato: contexto, decisão, alternativas, consequências).
- `docs/providers/`: contrato de cada provider externo (versão testada, comandos,
  outputs, exit codes, riscos, licença, fallback, última validação).
- `docs/agents/`: índice de domínio, tracker e labels para agentes.

Ordem de autoridade: código testado < docs do módulo < ADRs < spec mestra.
Divergência entre doc e código deve ser registrada, nunca ignorada.
