"""Plan 05 S1 - a bad manifest is a one-line error, never an exception, and
suffixes are case-normalised (cc-CR000.001 L4)."""
from __future__ import annotations

from pathlib import Path

import pytest

from graphify_lang.manifest import LanguageManifest

_EXTRACT = '\n[extract]\nruntime = "x.extract:build"\n'


def _load(tmp_path: Path, text: str):
    path = tmp_path / "m.toml"
    path.write_text(text, encoding="utf-8")
    return LanguageManifest.from_toml(path)


@pytest.mark.parametrize("text", [
    'language = "x"\n',
    'grammar = "g"\n[language]\nname = "x"\nsuffixes = [".x"]\n' + _EXTRACT,
    'extract = "e"\n[language]\nname = "x"\nsuffixes = [".x"]\n',
    '[language]\nname = 7\nsuffixes = [".x"]\n' + _EXTRACT,
    '[language]\nname = ["x"]\nsuffixes = [".x"]\n' + _EXTRACT,
])
def test_l4_bad_sections_never_raise(tmp_path, text):
    manifest, errors = _load(tmp_path, text)
    assert len(errors) == 1 and "\n" not in errors[0]
    assert manifest.name == ""


def test_l4_suffixes_lower_cased(tmp_path):
    manifest, errors = _load(tmp_path, '[language]\nname = "x"\nsuffixes = [".LSP", ".Mnl"]\n'
                             'hook_suffixes = [".LSP"]\noverrides = [".DCL"]\n' + _EXTRACT)
    assert errors == []
    assert manifest.suffixes == frozenset({".lsp", ".mnl"})
    assert manifest.hook_suffixes == (".lsp",)
    assert manifest.overrides == frozenset({".dcl"})


def test_l4_augments_lower_cased(tmp_path):
    manifest, errors = _load(tmp_path, '[language]\nname = "x"\nkind = "augment"\n'
                             'augments = [".MD"]\n' + _EXTRACT)
    assert errors == []
    assert manifest.augments == frozenset({".md"})
