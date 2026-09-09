"""Guardas de arquitetura (WIRS-002, ADR-003).

Cada teste varre imports reais via AST. A prova de que o guarda funciona está
na verificação por mutação: uma violação introduzida de propósito deve quebrar
o teste correspondente.
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "wirs"


def _top_level_imports(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return found


def _violations(package: str, forbidden: set[str]) -> dict[str, set[str]]:
    base = SRC / package
    hits: dict[str, set[str]] = {}
    for py_file in sorted(base.rglob("*.py")):
        bad = _top_level_imports(py_file) & forbidden
        if bad:
            hits[str(py_file.relative_to(SRC))] = bad
    return hits


def test_domain_nao_importa_plataforma_provider_ui() -> None:
    """ADR-003: domain/ usa só stdlib — nunca wordpress/yara/wordfence/rich/mysql/typer."""
    forbidden = {"wordpress", "yara", "wordfence", "rich", "mysql", "typer"}
    assert _violations("domain", forbidden) == {}


def test_detectors_nao_usam_subprocess() -> None:
    """Detector avalia Evidence — nunca cria processo (WIRS-120: só via CommandRunner)."""
    assert _violations("detectors", {"subprocess"}) == {}


def test_application_so_conhece_domain_e_ports() -> None:
    """Hexagonal sem burocracia: application depende de domain + ports, nada além."""
    import ast as _ast

    stdlib = {
        "__future__",
        "collections",
        "dataclasses",
        "enum",
        "hashlib",
        "json",
        "os",
        "pathlib",
        "re",
        "stat",
        "time",
        "types",
        "typing",
        "uuid",
    }
    bad: dict[str, set[str]] = {}
    for py_file in sorted((SRC / "application").rglob("*.py")):
        mods = _top_level_imports(py_file)
        vendor = {m for m in mods if "." not in m} - stdlib - {"wirs"}
        internal = set()
        for node in _ast.walk(_ast.parse(py_file.read_text(encoding="utf-8"))):
            if isinstance(node, _ast.ImportFrom) and (node.module or "").startswith("wirs."):
                internal.add(node.module.split(".")[1])
        internal -= {"domain", "ports"}
        hits = vendor | internal
        if hits:
            bad[str(py_file.relative_to(SRC))] = hits
    assert bad == {}


def test_subprocess_so_via_command_runner() -> None:
    """WIRS-120: `import subprocess` fora da camada permitida quebra o build."""
    allowed = {"infrastructure/command_runner.py"}
    hits: dict[str, set[str]] = {}
    for py_file in sorted(SRC.rglob("*.py")):
        rel = str(py_file.relative_to(SRC)).replace("\\", "/")
        if rel in allowed:
            continue
        if "subprocess" in _top_level_imports(py_file):
            hits[rel] = {"subprocess"}
    assert hits == {}
