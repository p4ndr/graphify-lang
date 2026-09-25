"""Content-sniff router for suffixes that a plugin shares (plan 04 §3.1, S1/S3).

The VBA manifest here is test-only: a `[sniff]` table and a stub extractor that
returns one marker node. The real VBA plugin is T29. `.cls` is the shared
suffix: the built-in claimant is `extract_apex`.
"""
from __future__ import annotations

import getpass
import logging
import os
from dataclasses import replace
from pathlib import Path

import pytest

from graphify.extract import extract_apex
from graphify_lang import registry
from graphify_lang.manifest import LanguageManifest

FIXTURES = Path(__file__).parent / "fixtures" / "sniff"

VBA_TOML = r"""
[language]
name = "{name}"
suffixes = [".cls"]
priority = {priority}

[sniff]
head_bytes = {head_bytes}
min_score = 5
rules = [
  {{ re = '^VERSION 1\.0 CLASS', weight = 10 }},
  {{ re = '^Attribute VB_Name', weight = 10 }},
  {{ re = '^\s*(Public |Private |Friend )?(Sub|Function) \w+\(', weight = 3, flags = "i" }},
  {{ re = '^\s*Dim \w+ As ', weight = 3, flags = "i" }},
]

[extract]
runtime = "tests.test_lang_sniff"
"""


def _stub(tag: str):
    def extract(path: Path) -> dict:
        return {"nodes": [{"id": f"{tag}_{path.stem}", "label": tag}], "edges": []}
    extract.__name__ = f"extract_{tag}"
    return extract


def _manifest(tmp_path: Path, name: str = "vba", priority: int = 0,
              head_bytes: int = 4096) -> LanguageManifest:
    toml = tmp_path / f"{name}.toml"
    toml.write_text(VBA_TOML.format(name=name, priority=priority, head_bytes=head_bytes),
                    encoding="utf-8")
    manifest, errors = LanguageManifest.from_toml(toml)
    assert errors == []
    return replace(manifest, extract=_stub(name))


@pytest.fixture
def clean_registry():
    registry.reset()
    yield
    registry.reset()


def _router(*manifests: LanguageManifest):
    for m in manifests:
        registry._register_manifest(m)
    return registry.dispatch_table({".cls": extract_apex})[".cls"]


def _is_vba(result: dict, tag: str = "vba") -> bool:
    return [n.get("label") for n in result["nodes"]] == [tag]


@pytest.mark.parametrize("fixture, to_vba", [
    ("vba_class.cls", True),               # headerless: body rules only (R1)
    ("vba_class_bom_crlf.cls", True),      # BOM stripped before ^, CRLF lines
    ("apex_class.cls", False),
    ("apex_with_vb_comment.cls", False),   # VBA text mid-line in comments
    ("empty.cls", False),
    ("binary.cls", False),                 # NUL bytes: never sniffed as text
])
def test_routing_per_fixture(clean_registry, tmp_path, fixture, to_vba):
    route = _router(_manifest(tmp_path))
    path = FIXTURES / fixture
    result = route(path)
    if to_vba:
        assert _is_vba(result)
    else:
        assert result == extract_apex(path)


def test_router_has_stable_name(clean_registry, tmp_path):
    assert _router(_manifest(tmp_path)).__name__ == "sniff_router[.cls]"


def test_head_bytes_truncation(clean_registry, tmp_path):
    body = b"' padding line for the head window\r\n" * 150  # > 4096 bytes
    path = tmp_path / "late_header.cls"
    path.write_bytes(body + b'Attribute VB_Name = "Late"\r\n')
    assert _router(_manifest(tmp_path, head_bytes=4096))(path) == extract_apex(path)
    registry.reset()
    assert _is_vba(_router(_manifest(tmp_path, head_bytes=8192))(path))


def test_windows_1252_bytes(clean_registry, tmp_path):
    path = tmp_path / "cp1252.cls"
    path.write_bytes(b'Attribute VB_Name = "M\xf3dulo"\r\n'
                     b"Public Sub Caf\xe9()\r\nEnd Sub\r\n")
    assert _is_vba(_router(_manifest(tmp_path))(path))


def test_undecodable_head_falls_back(clean_registry, tmp_path):
    path = tmp_path / "noise.cls"
    path.write_bytes(bytes(range(0x80, 0x100)) * 4)
    assert _router(_manifest(tmp_path))(path) == extract_apex(path)


def test_tie_higher_priority_wins(clean_registry, tmp_path):
    route = _router(_manifest(tmp_path, "vba_a", priority=1),
                    _manifest(tmp_path, "vba_b", priority=5))
    assert _is_vba(route(FIXTURES / "vba_class.cls"), "vba_b")


def test_tie_equal_priority_first_wins_and_warns_once(clean_registry, tmp_path, caplog):
    route = _router(_manifest(tmp_path, "vba_a"), _manifest(tmp_path, "vba_b"))
    with caplog.at_level(logging.WARNING, logger="graphify_lang"):
        assert _is_vba(route(FIXTURES / "vba_class.cls"), "vba_a")
        assert _is_vba(route(FIXTURES / "vba_class_bom_crlf.cls"), "vba_a")
    ties = [r for r in caplog.records if "tie" in r.getMessage()]
    assert len(ties) == 1


def test_get_extractor_uses_router(clean_registry, tmp_path, monkeypatch):
    """End to end through the core dispatch table and `_get_extractor`."""
    import graphify.extract as extract
    import graphify.lang_registry as core
    monkeypatch.setattr(extract, "_DISPATCH", dict(extract._DISPATCH))
    monkeypatch.setattr(core, "_REGISTRY_AVAILABLE", True)
    registry._register_manifest(_manifest(tmp_path))
    core.apply_dispatch()
    vba = FIXTURES / "vba_class.cls"
    assert extract._get_extractor(vba).__name__ == "sniff_router[.cls]"
    assert _is_vba(extract._get_extractor(vba)(vba))
    apex = Path(__file__).parent / "fixtures" / "sample.cls"
    assert extract._get_extractor(apex)(apex) == extract_apex(apex)


def test_measured_start_point_vba_is_not_apex(clean_registry, tmp_path):
    """A real exported workbook class goes to the plugin (plan 04 §1)."""
    home = Path(os.path.expanduser(f"~{getpass.getuser()}"))  # conftest sandboxes HOME
    path = home / "repos/bim-chk/src/document/ThisWorkbook.cls"
    if not path.is_file():
        pytest.skip("bim-chk corpus not on this host")
    assert _is_vba(_router(_manifest(tmp_path))(path))
