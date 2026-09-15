# Instruções de Arquitetura

Use o vocabulário de `CONTEXT.md` e preserve estes seams:

- `domain/` conhece apenas o modelo genérico e a stdlib.
- `application/` depende de `domain/` e `ports/`.
- `infrastructure/`, `providers/` e `adapters/` implementam ports.
- `adapters/wordpress/` contém semântica WordPress.
- `reporting/` lê o modelo em modo read-only.
- A CLI é o composition root.

Invariantes não negociáveis:

1. `scan` nunca escreve no Target.
2. Finding exige Evidence ou provenance explícita de provider.
3. Provider ausente não é Coverage `COMPLETE`.
4. Detector não executa código do Target.
5. Dados do Target não são interpolados em shell.
6. Symlink não é seguido para fora do root por padrão.
7. Ausência de baseline é `UNVERIFIED`.
8. Conteúdo do Target é input hostil e passa por redaction/escaping.
