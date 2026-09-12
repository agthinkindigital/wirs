"""Wizard interativo de scan (WIRS-129). Só Rich (já dependência).

Pergunta plataforma → formatos → target → (report) → confirma, e devolve as
respostas para o `scan` executar. Prompts vão para stderr (stdout é sagrado).
Sem entrada (EOF/pipe vazio) aborta com erro acionável em vez de travar.
Futuros (php/joomla, markdown/html/pdf) aparecem desabilitados: honestidade
sobre o que existe.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt

_PLATAFORMAS = {"1": "wordpress"}
_FORMATOS = {"1": "terminal", "2": "json"}
_FUTUROS = {"3", "4", "5"}


@dataclass(frozen=True)
class WizardAnswers:
    target: Path
    format: str
    report: Path | None


def run_wizard(
    console: Console | None = None,
    target_arg: Path | None = None,
) -> WizardAnswers | None:
    """Conduz o wizard. None = cancelado pelo operador; ValueError = resposta inválida."""
    console = console or Console(file=sys.stderr, highlight=False)
    console.print("[bold]wirs[/bold] · assistente de scan")

    escolha = Prompt.ask(
        "Plataforma [1 wordpress, 2 php (em breve), 3 joomla (em breve)]",
        default="1",
        console=console,
    )
    if escolha.strip() != "1":
        raise ValueError("plataforma ainda não suportada. Use flags para wordpress.")

    formatos = Prompt.ask(
        "Formatos, ex. 1,2 [1 terminal, 2 json, 3+ em breve]", default="1,2", console=console
    )
    pedidos = {f.strip() for f in formatos.split(",") if f.strip()}
    if not pedidos or not pedidos <= set(_FORMATOS):
        raise ValueError("escolha só entre 1 (terminal) e 2 (json).")

    if target_arg is not None:
        alvo = target_arg
    else:
        bruto = Prompt.ask("Target (diretório a analisar)", console=console)
        alvo = Path(bruto.strip()).expanduser()
    if not alvo.exists() or not alvo.is_dir():
        raise ValueError(f"target inválido: {alvo}")

    relatorio: Path | None = None
    if "2" in pedidos:
        destino = Prompt.ask("Salvar JSON em (vazio = só stdout)", default="", console=console)
        if destino.strip():
            relatorio = Path(destino.strip()).expanduser()

    tela = "terminal" if "1" in pedidos else "json"
    console.print(
        f"vai rodar: scan {alvo} --format {tela}" + (f" --report {relatorio}" if relatorio else "")
    )
    confirma = Prompt.ask("Executar? [s/n]", default="s", console=console)
    if confirma.strip().lower() not in ("s", "sim", "y", "yes"):
        console.print("cancelado: nada foi executado.")
        return None
    return WizardAnswers(target=alvo, format=tela, report=relatorio)
