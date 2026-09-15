# WIRS — Product Charter

> Documento normativo de produto. Se a direção mudar, este arquivo deve ser
> atualizado antes do roadmap, das Epics e das Issues.

## Identidade

O WIRS é um scanner read-only de segurança, integridade e código suspeito para
aplicações web, especializado primeiro em WordPress e sustentado por um core
genérico para PHP e outros CMS/frameworks.

Seu trabalho principal é reduzir milhares de arquivos a uma lista pequena,
auditável e priorizada de Artifacts que merecem investigação humana.

## Promessa

- Inventariar o Target e tornar a cobertura explícita.
- Comparar com baselines quando existirem, sem confundir integridade com benignidade.
- Analisar conteúdo mesmo quando não houver baseline.
- Explicar cada Finding por Evidence, severidade, confiança e contexto.
- Produzir relatório reproduzível sem prometer que o site está limpo.

## Não objetivos atuais

- SIEM, XDR, EDR, SOAR ou monitoramento contínuo.
- Daemon, agente residente, Kafka, Redis ou fleet obrigatória.
- SSH obrigatório ou serviço remoto obrigatório.
- Dashboard web obrigatório.
- IA como detector ou fonte de Evidence determinística.
- Quarentena, bloqueio, remediação ou resposta automática.

## Ordem de expansão

```text
filesystem/código
→ WordPress forte
→ signatures/correlation/report
→ PHP Generic
→ outros adapters
→ logs opcionais
→ IP/threat intelligence
→ aquisição remota
→ IA
```

## Invariantes de produto

1. Feature futura nunca bloqueia o scanner local.
2. Content analysis sem baseline é obrigatória quando aplicável.
3. Integridade não substitui content analysis.
4. Logs enriquecem o mesmo modelo; não fundam o scanner.
5. SSH é um acquisition seam, não a fundação do produto.
6. IA é um analysis seam, opt-in e posterior.
7. UI nunca contém regra de negócio.
8. Diagnosis file-centric existe antes de Diagnosis host-centric.
9. Um caso real informa regras e gaps; não redefine sozinho o produto.
10. Toda nova Epic declara o Horizonte e a Capacidade principal deste Charter.

## Gate de promoção

Uma proposta só entra no Roadmap se melhorar a detecção, priorização,
Evidence, Finding, Coverage, Diagnosis ou report do scanner, ou se for um seam
necessário para isso. Caso contrário, permanece em `docs/future/` ou em um
`docs/case-studies/`.
