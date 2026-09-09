# SECURITY.md

## Garantia central

`wirs scan` **nunca escreve no target**: não apaga, renomeia, quarentena,
modifica permissão, desativa plugin, altera banco, regenera cache nem remedia.
Remediação, se existir um dia, será outro subsistema, outro namespace de
comandos e outro modelo de autorização.

## Modelo de ameaça (resumo)

O alvo comprometido é adversarial: controla arquivos, nomes, symlinks, banco,
configuração e qualquer string que termine em relatório. Providers externos
podem retornar output malicioso. Ver Seção 16 do spec (`/secure-e2e`).

Fronteiras obrigatórias:

- arquivos do target abertos como `rb`, via `ArtifactReader` (streaming + budget);
- subprocess apenas via `CommandRunner` (`shell=False`, argv allowlisted, timeout, output cap, env sanitizado);
- symlink nunca seguido fora do root por padrão; FIFO/socket/device nunca lidos como arquivo;
- regex validadas com budget; parsers com max bytes/depth;
- redaction de secrets na fronteira de coleta, antes da serialização;
- renderers tratam todo conteúdo do alvo como hostil (escape HTML, ANSI neutralizado).

## Amostras de malware

Não commitar malware executável real. Fixtures usam amostras sintéticas e
inertes que representam técnicas sem risco de execução. Corpus malicioso real,
se um dia necessário, fica em repositório privado/controlado separado.

### Regra anti-antivírus (aprendida na #37)

Até *strings de teste* podem sumir: o Windows Defender quarantinou um arquivo
de teste que continha `eval($_GET...` contíguo. Por isso, nenhum arquivo do
repo — fixture, teste ou doc — pode conter assinatura viva de webshell/malware
em sequência contígua. Fragmentar literais na fonte (`"ev" + "al("`, nunca
`"eval("`), com comentário `NOTA ANTI-AV` explicando. Vale também para o
formatador: nada de concatenação implícita que o `ruff format` juntaria de
volta — usar `+` explícito. Amostra que o AV come é teste que "passa" sem
existir.

## Reporte de vulnerabilidades

Abra uma GitHub Issue com label `type:security` ou contate o mantenedor em
privado para vulnerabilidades sensíveis. Não inclua dumps, secrets ou dados
de alvos reais em Issues públicas.
