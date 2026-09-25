"""Content-sniff router for suffixes that a plugin shares (plan 04 §3.1, S1/S3).

Routing per fixture runs the real `vba-cls` manifest (`graphify_lang/vba`,
plan 04 S8). The engine tests (ties, `head_bytes`, priorities) keep a
test-only manifest with a stub extractor that returns one marker node, because
they vary the priority and the window. `.cls` is the shared suffix: the
built-in claimant is `extract_apex`.
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


def _is_stub(result: dict, tag: str = "vba") -> bool:
    return [n.get("label") for n in result["nodes"]] == [tag]


def _real_vba_cls() -> LanguageManifest:
    from graphify_lang.vba import _get_manifest
    return next(m for m in _get_manifest() if m.name == "vba-cls")


def _is_vba(result: dict) -> bool:
    return any(n.get("node_kind") == "class" for n in result["nodes"])


@pytest.mark.parametrize("fixture, to_vba", [
    ("vba_class.cls", True),               # headerless: body rules only (R1)
    ("vba_class_bom_crlf.cls", True),      # BOM stripped before ^, CRLF lines
    ("apex_class.cls", False),
    ("apex_with_vb_comment.cls", False),   # VBA text mid-line in comments
    ("empty.cls", False),
    ("binary.cls", False),                 # NUL bytes: never sniffed as text
])
def test_routing_per_fixture(clean_registry, fixture, to_vba):
    route = _router(_real_vba_cls())
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
    assert _is_stub(_router(_manifest(tmp_path, head_bytes=8192))(path))


def test_windows_1252_bytes(clean_registry, tmp_path):
    path = tmp_path / "cp1252.cls"
    path.write_bytes(b'Attribute VB_Name = "M\xf3dulo"\r\n'
                     b"Public Sub Caf\xe9()\r\nEnd Sub\r\n")
    assert _is_stub(_router(_manifest(tmp_path))(path))


def test_undecodable_head_falls_back(clean_registry, tmp_path):
    path = tmp_path / "noise.cls"
    path.write_bytes(bytes(range(0x80, 0x100)) * 4)
    assert _router(_manifest(tmp_path))(path) == extract_apex(path)


def test_tie_higher_priority_wins(clean_registry, tmp_path):
    route = _router(_manifest(tmp_path, "vba_a", priority=1),
                    _manifest(tmp_path, "vba_b", priority=5))
    assert _is_stub(route(FIXTURES / "vba_class.cls"), "vba_b")


def test_tie_equal_priority_first_wins_and_warns_once(clean_registry, tmp_path, caplog):
    route = _router(_manifest(tmp_path, "vba_a"), _manifest(tmp_path, "vba_b"))
    with caplog.at_level(logging.WARNING, logger="graphify_lang"):
        assert _is_stub(route(FIXTURES / "vba_class.cls"), "vba_a")
        assert _is_stub(route(FIXTURES / "vba_class_bom_crlf.cls"), "vba_a")
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
    assert _is_stub(extract._get_extractor(vba)(vba))
    apex = Path(__file__).parent / "fixtures" / "sample.cls"
    assert extract._get_extractor(apex)(apex) == extract_apex(apex)


def test_measured_start_point_vba_is_not_apex(clean_registry):
    """A real exported workbook class goes to the plugin (plan 04 §1)."""
    home = Path(os.path.expanduser(f"~{getpass.getuser()}"))  # conftest sandboxes HOME
    path = home / "repos/bim-chk/src/document/ThisWorkbook.cls"
    if not path.is_file():
        pytest.skip("bim-chk corpus not on this host")
    result = _router(_real_vba_cls())(path)
    assert _is_vba(result) and len(result["nodes"]) > 1


# --- manifest schema (plan 04 S2) -------------------------------------------

def _parse(tmp_path: Path, body: str):
    toml = tmp_path / "m.toml"
    toml.write_text(body + '\n[extract]\nruntime = "x"\n', encoding="utf-8")
    return LanguageManifest.from_toml(toml)


def test_schema_sniff_and_match_parse(tmp_path):
    m, errors = _parse(tmp_path, r"""
[language]
name = "astgrep"
suffixes = [".yml"]
priority = 3
[sniff]
head_bytes = 512
min_score = 2
rules = [{ re = '^id:', weight = 2 }, { re = '^RULE:', flags = "i" }]
[match]
globs = ["rules/**/*.yml"]
filenames = ["sgconfig.yml"]
""")
    assert errors == []
    assert (m.sniff.head_bytes, m.sniff.min_score, m.priority) == (512, 2, 3)
    assert m.sniff.score("id: x\nrule: y\n") == 3
    assert m.match_globs == ("rules/**/*.yml",) and m.match_filenames == ("sgconfig.yml",)


def test_schema_augment_kind(tmp_path):
    m, errors = _parse(tmp_path, """
[language]
name = "cc-kb"
kind = "augment"
augments = [".md"]
[match]
globs = ["docs/cc-*.md"]
""")
    assert errors == []
    assert (m.kind, m.augments, m.suffixes) == ("augment", frozenset({".md"}), frozenset())


@pytest.mark.parametrize("body, reason", [
    ('[language]\nname = "a"\nsuffixes = [".a"]\n[sniff]\nrules = [{ re = "(" }]',
     "bad regex"),
    ('[language]\nname = "a"\nsuffixes = [".a"]\n[sniff]\nmin_score = 3',
     "min_score set without sniff.rules"),
    ('[language]\nname = "a"\nsuffixes = [".a", ".b"]\noverrides = [".a"]\n'
     '[sniff]\nrules = [{ re = "x" }]',
     "overrides and [sniff] on the same suffix: .a"),
    ('[language]\nname = "a"\nsuffixes = [".a"]\n[sniff]\nrules = [{ re = "x", flags = "q" }]',
     "flags must use only"),
    ('[language]\nname = "a"\nkind = "augment"', "non-empty language.augments"),
    ('[language]\nname = "a"\nkind = "plugin"\nsuffixes = [".a"]', "language.kind must be"),
])
def test_schema_rejects(tmp_path, body, reason):
    m, errors = _parse(tmp_path, body)
    assert len(errors) == 1 and reason in errors[0], errors
    assert not m.name


def test_lsp_override_unchanged():
    """`overrides` still means 'wins with no sniff': .lsp goes straight to AutoLISP."""
    import graphify.extract as extract
    from graphify_lang.autolisp import extract_autolisp
    assert extract._DISPATCH[".lsp"] is extract_autolisp
    assert extract._DISPATCH[".cls"].__name__ == "sniff_router[.cls]"  # vba-cls, plan 04 S8


# --- detect hook for [match] data suffixes (plan 04 S4, §3.2) -----------------

DATA_TOML = r"""
[language]
name = "{name}"
suffixes = ["{suffix}"]
[sniff]
min_score = 1
rules = [{{ re = '{rule}' }}]
[match]
{match}
[extract]
runtime = "tests.test_lang_sniff"
"""


def _data_plugin(tmp_path: Path, name: str, suffix: str, rule: str, match: str):
    toml = tmp_path / f"{name}.toml"
    toml.write_text(DATA_TOML.format(name=name, suffix=suffix, rule=rule, match=match),
                    encoding="utf-8")
    manifest, errors = LanguageManifest.from_toml(toml)
    assert errors == []
    registry._register_manifest(replace(manifest, extract=_stub(name)))


@pytest.fixture
def data_plugins(clean_registry, tmp_path):
    _data_plugin(tmp_path, "cargo", ".toml", r"^\[(package|workspace)\]",
                 'filenames = ["Cargo.toml"]')
    _data_plugin(tmp_path, "astgrep", ".yml", r"^id:",
                 'globs = ["rules/**/*.yml", "rule-tests/**/*.yml"]\nfilenames = ["sgconfig.yml"]')
    _data_plugin(tmp_path, "ecschema", ".xml", r"<ECSchema", 'globs = ["**/*.xml"]')


def _file(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize("rel, text, expected", [
    ("Cargo.toml", "[package]\nname = 'x'\n", "code"),
    ("pyproject.toml", "[project]\nname = 'x'\n", "code"),   # package manifest, as upstream
    ("config/settings.toml", "[package]\n", None),          # no [match] hit: as upstream
    ("rules/x.yml", "id: no-eval\nlanguage: python\n", "code"),
    ("rules/deep/y.yml", "id: no-exec\n", "code"),
    ("rules/notes.yml", "title: not a rule\n", "document"),  # glob hit, sniff miss
    (".github/workflows/ci.yml", "id: build\non: push\n", "document"),
    ("schema/Plant.ecschema.xml", '<?xml version="1.0"?>\n<ECSchema schemaName="P">', "code"),
    ("docs/PSMaml.xml", '<?xml version="1.0"?>\n<helpItems>', None),
    ("pom.xml", "<project/>", "code"),                       # package manifest, as upstream
])
def test_detect_hook(data_plugins, tmp_path, rel, text, expected):
    from graphify.detect import classify_file
    got = classify_file(_file(tmp_path, rel, text))
    assert (got.value if got else None) == expected


def test_data_suffixes_stay_out_of_code_extensions(data_plugins):
    assert registry.registered_suffixes().isdisjoint({".yml", ".toml", ".xml"})
    assert registry.match_suffixes() == {".yml", ".toml", ".xml"}


def test_matched_data_file_extracts_through_router(data_plugins, tmp_path):
    table = registry.dispatch_table({})
    rule = _file(tmp_path, "rules/x.yml", "id: no-eval\n")
    other = _file(tmp_path, "ci.yml", "id: x\n")
    assert _is_stub(table[".yml"](rule), "astgrep")
    assert table[".yml"](other) == {"nodes": [], "edges": []}


# --- augment kind (plan 04 S5, §3.3) ----------------------------------------

AUGMENT_TOML = """
[language]
name = "stub-kb"
kind = "augment"
augments = ["{suffix}"]
[match]
globs = ["{glob}"]
[extract]
runtime = "tests.test_lang_sniff"
"""


def _stub_augment(path: Path, base: dict) -> dict:
    first = base["nodes"][0]["id"]
    return {
        "nodes": [
            {"id": f"stub_kb_{path.stem}", "label": "extra"},
            {"id": first, "label": "renamed"},        # existing id: dropped
            {"id": "no_prefix", "label": "x"},        # wrong prefix: dropped
        ],
        "edges": [{"source": first, "target": f"stub_kb_{path.stem}", "relation": "mentions"}],
        "attrs": {first: {"cc_id": "cc-XX000.001", "label": "overwritten?"}},
    }


def _augment_plugin(tmp_path: Path, suffix: str, glob: str) -> None:
    toml = tmp_path / "stub-kb.toml"
    toml.write_text(AUGMENT_TOML.format(suffix=suffix, glob=glob), encoding="utf-8")
    manifest, errors = LanguageManifest.from_toml(toml)
    assert errors == []
    registry._register_manifest(replace(manifest, augment=_stub_augment))


def test_augment_adds_without_changing_base(clean_registry, tmp_path):
    from graphify.extract import extract_markdown
    _augment_plugin(tmp_path, ".md", "docs/cc-*.md")
    assert ".md" not in registry.dispatch_table({".md": extract_markdown})  # per path
    doc = _file(tmp_path, "docs/cc-XX000.001.md", "# Title\n\n## Section\n\nSee cc-XX000.000.\n")
    assert registry.augment_extractor(doc, extract_markdown).__name__ == "augmented[.md]"

    def wrapped(p):
        return registry.augment_extractor(p, extract_markdown)(p)
    base, got = extract_markdown(doc), wrapped(doc)
    base_ids = [n["id"] for n in base["nodes"]]
    assert [n["id"] for n in got["nodes"]] == base_ids + [f"stub_kb_{doc.stem}"]
    assert [n["label"] for n in got["nodes"][:len(base_ids)]] == [n["label"] for n in base["nodes"]]
    assert got["nodes"][0]["cc_id"] == "cc-XX000.001"
    assert "cc_id" not in base["nodes"][0]                      # base not mutated
    assert got["edges"] == base["edges"] + [
        {"source": base_ids[0], "target": f"stub_kb_{doc.stem}", "relation": "mentions"}]
    other = _file(tmp_path, "README.md", "# Readme\n")          # [match] miss
    assert wrapped(other) == extract_markdown(other)
    assert ".md" not in registry.registered_suffixes()


def test_augment_composes_with_router(clean_registry, tmp_path):
    registry._register_manifest(_manifest(tmp_path))
    _augment_plugin(tmp_path, ".cls", "**/*.cls")
    router = registry.dispatch_table({".cls": extract_apex})[".cls"]

    def wrapped(p):
        return registry.augment_extractor(p, router)(p)
    got = wrapped(FIXTURES / "vba_class.cls")
    assert [n["label"] for n in got["nodes"]] == ["vba", "extra"]
    apex = wrapped(FIXTURES / "apex_class.cls")
    assert apex["nodes"][:-1] == [
        {**n, **({"cc_id": "cc-XX000.001"} if i == 0 else {})}
        for i, n in enumerate(extract_apex(FIXTURES / "apex_class.cls")["nodes"])]


def test_augment_on_package_manifest_path(clean_registry, tmp_path):
    """A package manifest is picked by name before _DISPATCH; the augment still runs."""
    from graphify.extract import _get_extractor
    from graphify.manifest_ingest import extract_package_manifest
    _augment_plugin(tmp_path, ".toml", "**/pyproject.toml")
    assert ".toml" not in registry.dispatch_table({})             # per-path, not per-suffix
    proj = _file(tmp_path, "pyproject.toml", "[project]\nname = 'demo'\n")
    wrapped = _get_extractor(proj)
    assert wrapped.__name__ == "augmented[.toml]"
    base, got = extract_package_manifest(proj), wrapped(proj)
    assert got["nodes"][:-1] == [{**base["nodes"][0], "cc_id": "cc-XX000.001"}]
    assert got["nodes"][-1]["id"] == f"stub_kb_{proj.stem}"
    other = _file(tmp_path, "sub/Cargo.toml", "[package]\nname = 'x'\n")  # [match] miss
    assert _get_extractor(other) is extract_package_manifest


@pytest.mark.parametrize("encoding", ["utf-16-le", "utf-16-be"])
def test_utf16_with_bom_is_sniffed(clean_registry, tmp_path, encoding):
    # A UTF-16 BOM means the NULs are the encoding, not binary content.
    path = tmp_path / f"{encoding}.cls"
    text = 'Attribute VB_Name = "Wide"\r\nPublic Sub Go()\r\nEnd Sub\r\n'
    path.write_bytes("﻿".encode(encoding) + text.encode(encoding))
    assert _is_stub(_router(_manifest(tmp_path))(path))


def test_utf16_without_bom_stays_binary(clean_registry, tmp_path):
    path = tmp_path / "nobom.cls"
    path.write_bytes('Attribute VB_Name = "Wide"\r\n'.encode("utf-16-le"))
    assert _router(_manifest(tmp_path))(path) == extract_apex(path)


def test_hook_suffixes_union_all_manifests(clean_registry, tmp_path):
    """Every manifest's hook_suffixes, a [match] data plugin and an augment included."""
    _data_plugin(tmp_path, "astgrep", ".yml", r"^id:", 'globs = ["rules/**/*.yml"]')
    data = registry.get_manifest("astgrep")
    registry._register_manifest(replace(data, hook_suffixes=(".yml", ".yaml")))
    registry._register_manifest(LanguageManifest(
        name="aug", suffixes=frozenset(), extract=_stub("aug"), kind="augment",
        augments=frozenset({".md"}), hook_suffixes=(".md",)))
    assert registry.hook_suffixes() == {".yml", ".yaml", ".md"}
    assert ".yml" not in registry.registered_suffixes()


def test_augment_extra_keys_ride_along(clean_registry, tmp_path):
    """A resolver payload key is carried; a key the base has is never replaced."""
    m = LanguageManifest(name="kb", suffixes=frozenset(), extract=_stub("kb"),
                         kind="augment", augments=frozenset({".md"}))
    base = {"nodes": [], "edges": [], "raw_calls": ["base"]}
    got = registry._merge(m, base, {"kb_refs": [1], "raw_calls": ["augment"]})
    assert got["kb_refs"] == [1] and got["raw_calls"] == ["base"]


def test_augment_failure_keeps_base(clean_registry, tmp_path, caplog):
    from graphify.extract import extract_markdown

    def boom(path, base):
        raise ValueError("bad augment")
    _augment_plugin(tmp_path, ".md", "docs/cc-*.md")
    m = registry.get_manifest("stub-kb")
    registry._register_manifest(replace(m, augment=boom))
    doc = _file(tmp_path, "docs/cc-XX000.001.md", "# Title\n")
    with caplog.at_level(logging.WARNING):
        got = registry.augment_extractor(doc, extract_markdown)(doc)
    assert got == extract_markdown(doc)
    assert "bad augment" in caplog.text
