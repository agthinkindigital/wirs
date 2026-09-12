"""YARA provider (WIRS-081).

Sem yara-python instalado, os testes do caminho real usam um stub que replica
o contrato validado em docs/providers/yara-python.md; com a lib ausente de
verdade, só o teste de UNAVAILABLE roda (resto pula).
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import pytest

from wirs.domain import Artifact, ArtifactKind, LocalDirectoryTarget, SafePath
from wirs.domain.errors import ProviderInvalidOutput, ProviderUnavailable
from wirs.infrastructure.reader import ArtifactReader, ReadBudget
from wirs.ports.analysis import ExternalAnalyzer
from wirs.providers import yara_provider
from wirs.providers.yara_provider import YaraAnalyzer


class _FakeMatch:
    def __init__(
        self, rule="PHP_WEBSHELL", namespace="builtin", tags=("webshell", "php"), meta=None
    ):
        self.rule = rule
        self.namespace = namespace
        self.tags = list(tags)
        self.meta = meta or {}


class _FakeRules:
    def __init__(self, matches):
        self._matches = matches

    def match(self, data=None, filepath=None, timeout=None):
        return self._matches


class _FakeYara(ModuleType):
    class SyntaxError(Exception):
        pass

    class Error(Exception):
        pass

    class TimeoutError(Error):
        pass

    def __init__(self, matches=(), syntax_error=None):
        super().__init__("yara")
        self._matches = matches
        self._syntax_error = syntax_error

    def compile(self, source=None, **kwargs):
        if self._syntax_error is not None:
            raise self.SyntaxError(self._syntax_error)
        return _FakeRules(self._matches)


@pytest.fixture()
def com_yara(monkeypatch):
    monkeypatch.setattr(yara_provider, "_yara", _FakeYara([_FakeMatch()]))
    return yara_provider


def _artifact(tmp_path: Path, nome: str = "evil.php", conteudo: bytes = b"<?php // x\n"):
    (tmp_path / nome).write_bytes(conteudo)
    root = LocalDirectoryTarget(tmp_path).root
    return Artifact(kind=ArtifactKind.FILE, path=SafePath(root, nome))


def _analyzer(tmp_path: Path, **kwargs):
    return YaraAnalyzer(
        rules_source='rule ok { strings: $a = "x" condition: $a }',
        reader=ArtifactReader(),
        budget=ReadBudget(max_bytes=1 << 20),
        **kwargs,
    )


def test_match_sintetico_normalizado(com_yara, tmp_path: Path) -> None:
    analyzer = _analyzer(tmp_path)
    assert isinstance(analyzer, ExternalAnalyzer)

    resultado = analyzer.scan([_artifact(tmp_path)])

    assert resultado.provider_id == "yara"
    (achado,) = resultado.findings
    assert achado.external_rule_id == "PHP_WEBSHELL"
    assert achado.artifact_ref == "evil.php"
    assert achado.attributes["tags"] == ["webshell", "php"]
    assert achado.attributes["namespace"] == "builtin"


def test_sem_lib_e_unavailable(tmp_path: Path) -> None:
    if "yara" in sys.modules or yara_provider._yara is not None:
        pytest.skip("yara-python instalado: caminho real coberto no CI")

    analyzer = _analyzer(tmp_path)

    disp = analyzer.available()
    assert not disp.available
    assert "wirs[yara]" in disp.reason
    with pytest.raises(ProviderUnavailable):
        analyzer.scan([_artifact(tmp_path)])


def test_pack_com_erro_sintaxe_vira_provider_failure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(yara_provider, "_yara", _FakeYara(syntax_error="linha 1"))
    analyzer = _analyzer(tmp_path)

    with pytest.raises(ProviderInvalidOutput, match="não compila"):
        analyzer.scan([_artifact(tmp_path)])


def test_timeout_pula_arquivo_e_continua(tmp_path: Path, monkeypatch) -> None:
    class _RegrasComTimeout(_FakeRules):
        def match(self, data=None, filepath=None, timeout=None):
            raise _FakeYara.TimeoutError("lento demais")

    class _YaraComTimeout(_FakeYara):
        def compile(self, source=None, **kwargs):
            return _RegrasComTimeout([])

    monkeypatch.setattr(yara_provider, "_yara", _YaraComTimeout([_FakeMatch()]))
    analyzer = _analyzer(tmp_path)

    resultado = analyzer.scan([_artifact(tmp_path), _artifact(tmp_path)])

    assert resultado.findings == ()
