"""Baseline Manifest schema (WIRS-040)."""

from __future__ import annotations

from wirs.domain import BaselineManifest, BaselineTrust


def test_manifest_valido_com_round_trip() -> None:
    manifest = BaselineManifest(
        component_id="akismet",
        version="5.3",
        source="operator-zip",
        trust=BaselineTrust.TRUSTED_OPERATOR,
        files={
            "akismet.php": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "readme.txt": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        },
        package_hash="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    )

    assert manifest.files["akismet.php"].startswith("e3b0c442")
    assert manifest.trust is BaselineTrust.TRUSTED_OPERATOR

    restaurado = BaselineManifest.from_dict(manifest.to_dict())
    assert restaurado == manifest


def _base(**over) -> BaselineManifest:
    args: dict = {
        "component_id": "x",
        "version": "1.0",
        "source": "op",
        "trust": BaselineTrust.TRUSTED_OPERATOR,
        "files": {"a.php": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
    }
    args.update(over)
    return BaselineManifest(**args)


def test_travessia_duplicata_hash_e_confianca() -> None:
    import pytest

    with pytest.raises(ValueError, match="travessia"):
        _base(
            files={
                "../../etc/x": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            }
        )
    with pytest.raises(ValueError, match="absoluto"):
        _base(files={"/etc/x": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"})
    with pytest.raises(ValueError, match="duplicado"):
        _base(
            files={
                "a/../a.php": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "a.php": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            }
        )
    with pytest.raises(ValueError, match="64 hex"):
        _base(files={"a.php": "zzz"})
    with pytest.raises(ValueError):
        _base(component_id="")
    with pytest.raises(ValueError, match="version"):
        _base(version="")
    with pytest.raises(ValueError, match="source"):
        _base(source="")
    with pytest.raises(ValueError):
        BaselineTrust("confio-muito")  # type: ignore[call-arg]

    # Referência não-confiável carrega linguagem diferente (ver #44/UNVERIFIED).
    ref = _base(trust=BaselineTrust.UNVERIFIED_REFERENCE)
    assert ref.trust is BaselineTrust.UNVERIFIED_REFERENCE
