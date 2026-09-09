# Documentação do WIRS

- [`ARCHITECTURE.md`](ARCHITECTURE.md): como o sistema foi pensado e como as peças se encaixam.
- [`JORNADA-FT1.md`](JORNADA-FT1.md): a construção do núcleo, slice por slice, explicada para humanos.
- [`WIRS_MASTER_SPEC_PT-BR.md`](../WIRS_MASTER_SPEC_PT-BR.md): especificação viva (autoridade de produto e arquitetura).
- [`CONTEXT.md`](../CONTEXT.md): glossário do domínio.
- [`adr/`](adr/): decisões arquiteturais.
- [`providers/`](providers/): contrato de cada provider externo.
- [`agents/README.md`](agents/README.md): operação com agentes (domínio, tracker, triage).

Ordem de autoridade: código testado < docs do módulo < ADRs < spec mestra.
Divergência entre doc e código deve ser registrada, nunca ignorada.
