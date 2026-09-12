"""Pack builtin de regras YARA (WIRS-082).

Sem yara-python, o engine real não roda aqui: o teste prova que o pack
carrega (regras certas, experimental fora por default) com stub de contrato;
o match positivo/negativo real roda no CI com a lib.
"""

from __future__ import annotations

from pathlib import Path

from wirs.ports.analysis import ExternalAnalyzer
from wirs.providers import yara_provider
from wirs.providers.yara_provider import YaraAnalyzer

PACK = Path(__file__).resolve().parents[2] / "rules" / "yara"


def test_pack_builtin_carrega_sem_experimental(monkeypatch) -> None:
    fontes: dict = {}

    class _Compile:
        def __call__(self, source=None, **kwargs):
            fontes["source"] = source
            return type("R", (), {"match": staticmethod(lambda **k: [])})()

    class _Yara:
        SyntaxError = type("SyntaxError", (Exception,), {})
        Error = type("Error", (Exception,), {})
        TimeoutError = type("TimeoutError", (Exception,), {})
        compile = _Compile()

    monkeypatch.setattr(yara_provider, "_yara", _Yara())

    analyzer = YaraAnalyzer.from_pack(PACK)

    assert isinstance(analyzer, ExternalAnalyzer)
    assert analyzer.scan([]).findings == ()
    assert "WIRS_PHP_Webshell_EvalChain" in fontes["source"]
    assert "WIRS_PHP_Dynamic_Include" in fontes["source"]
    assert "WIRS_EXP_PHP_Long_Encoded_Literal" not in fontes["source"]


def _stub_yara(monkeypatch, fontes: dict):
    class _Compile:
        def __call__(self, source=None, **kwargs):
            fontes["source"] = source
            return type("R", (), {"match": staticmethod(lambda **k: [])})()

    class _Yara:
        SyntaxError = type("SyntaxError", (Exception,), {})
        Error = type("Error", (Exception,), {})
        TimeoutError = type("TimeoutError", (Exception,), {})
        compile = _Compile()

    monkeypatch.setattr(yara_provider, "_yara", _Yara())


def test_experimental_opt_in_e_pack_vazio(tmp_path, monkeypatch) -> None:
    import pytest

    from wirs.domain.errors import ProviderInvalidOutput

    fontes: dict = {}
    _stub_yara(monkeypatch, fontes)

    YaraAnalyzer.from_pack(PACK, experimental=True).scan([])
    assert "WIRS_EXP_PHP_Long_Encoded_Literal" in fontes["source"]

    vazio = tmp_path / "pack"
    vazio.mkdir()
    with pytest.raises(ProviderInvalidOutput, match="sem regras"):
        YaraAnalyzer.from_pack(vazio)
