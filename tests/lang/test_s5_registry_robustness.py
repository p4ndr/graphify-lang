"""Plan 05 S5 - registry robustness (cc-CR000.001 M1, E4, M5, M3, L6, L7, L8,
L10, L13, N5).

M1: one plugin that fails to load costs only itself. L7: one entry-point group.
M5 (hub D4): ``GRAPHIFY_LANG_PATH`` folders are loaded after the entry points,
and a path plugin is part of the AST cache fingerprint (E1). E4: ``graphify
lang list --check``. M3: ``graphify watch`` sees plugin-claimed data files. L6:
no upper-case suffix variants. L8: a failing core hook logs at debug level.
L10: the ``[match]`` routers stay in ``_DISPATCH`` (accepted). L13: the
resolver case-fold is pinned. N5: ``[match] filenames`` compare case-folded.
"""
from __future__ import annotations

import importlib.metadata
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from graphify_lang import registry
from graphify_lang.manifest import LanguageManifest

FIXTURES = Path(__file__).parent / "fixtures"

_TOY_TOML = """schema = 1
[language]
name = "toy"
suffixes = [".toy"]
[extract]
runtime = "toy_pkg.extract"
"""
_TOY_PY = """from pathlib import Path


def extract(path):
    return {"nodes": [{"id": "toy_" + Path(path).stem, "label": Path(path).name,
                       "file_type": "code", "source_file": str(path)}], "edges": []}
"""


@pytest.fixture(autouse=True)
def _fresh_registry(monkeypatch):
    monkeypatch.delenv("GRAPHIFY_LANG_PATH", raising=False)
    monkeypatch.delenv("GRAPHIFY_LANG_DISABLE", raising=False)
    registry.reset()
    yield
    registry.reset()
    for name in [m for m in sys.modules if m == "toy_pkg" or m.startswith("toy_pkg.")]:
        del sys.modules[name]


def _toy_folder(root: Path) -> Path:
    """A path plugin: ``toy.toml`` at the folder root, its runtime in ``toy_pkg/``."""
    (root / "toy_pkg").mkdir(parents=True)
    (root / "toy_pkg" / "__init__.py").write_text("")
    (root / "toy_pkg" / "extract.py").write_text(_TOY_PY)
    (root / "toy.toml").write_text(_TOY_TOML)
    return root


class _EP:
    def __init__(self, name, target):
        self.name, self._target = name, target

    def load(self):
        return self._target


def _good() -> LanguageManifest:
    return LanguageManifest(name="good", suffixes=frozenset({".good"}), extract=lambda p: {})


def _bad() -> LanguageManifest:
    raise ValueError("graphify-lang.toml: ['TOML parse error']")


# --- M1, L7 --------------------------------------------------------------------

def test_m1_bad_entry_point_isolated(monkeypatch, caplog):
    monkeypatch.setattr(importlib.metadata, "entry_points",
                        lambda group=None: [_EP("bad", _bad), _EP("good", _good)]
                        if group == "graphify_lang_plugins" else [])
    with caplog.at_level(logging.WARNING, logger="graphify_lang.registry"):
        assert registry.registered_names() == ["good"]
    assert "failed to load entry point bad" in caplog.text


def test_l7_single_group(monkeypatch):
    groups: list[str] = []
    monkeypatch.setattr(importlib.metadata, "entry_points",
                        lambda group=None: groups.append(group) or [])
    registry.registered_names()
    assert groups == ["graphify_lang_plugins"]
    source = Path(registry.__file__).read_text()
    assert "importlib_metadata" not in source and "graphify_lang.plugins" not in source


# --- M5 ------------------------------------------------------------------------

def test_m5_lang_path_loads_plugin(tmp_path, monkeypatch):
    folder = _toy_folder(tmp_path / "plugins")
    monkeypatch.setenv("GRAPHIFY_LANG_PATH", os.pathsep.join([str(folder), ""]))
    before = list(sys.path)
    names = registry.registered_names()
    assert names[-1] == "toy" and "autolisp" in names          # entry points first
    assert sys.path == before                                  # folder on sys.path for the import only
    src = tmp_path / "a.toy"
    src.write_text("x")
    assert registry.get_manifest_for_suffix(".toy").extract(src)["nodes"][0]["id"] == "toy_a"


def test_m5_missing_dir_warns(tmp_path, monkeypatch, caplog):
    missing = tmp_path / "nope"
    monkeypatch.setenv("GRAPHIFY_LANG_PATH", str(missing))
    with caplog.at_level(logging.WARNING, logger="graphify_lang.registry"):
        names = registry.registered_names()
    assert "autolisp" in names
    assert str(missing) in caplog.text


def test_m5_bad_path_manifest_isolated(tmp_path, monkeypatch, caplog):
    folder = _toy_folder(tmp_path / "plugins")
    (folder / "broken.toml").write_text("[language\n")
    (folder / "nocall.toml").write_text(_TOY_TOML.replace('"toy"', '"nocall"')
                                        .replace(".toy", ".nocall")
                                        .replace("toy_pkg.extract", "toy_pkg"))
    monkeypatch.setenv("GRAPHIFY_LANG_PATH", str(folder))
    with caplog.at_level(logging.WARNING, logger="graphify_lang.registry"):
        names = registry.registered_names()
    assert "toy" in names and "nocall" not in names
    assert "broken.toml" in caplog.text and "nocall.toml" in caplog.text


def test_m5_path_plugin_in_cache_fingerprint(tmp_path, monkeypatch):
    """E1 covers path plugins: editing a path plugin's manifest or code moves
    the AST cache namespace."""
    import graphify.cache as cache
    import graphify.lang_registry as core

    saved = cache._EXTRACTOR_VERSION
    folder = _toy_folder(tmp_path / "plugins")
    monkeypatch.setenv("GRAPHIFY_LANG_PATH", str(folder))

    def namespace() -> str:
        registry.reset()
        core._fingerprint.cache_clear()
        core._namespace_ast_cache(registry)
        return cache._EXTRACTOR_VERSION

    try:
        first = namespace()
        assert "toy" in registry.registered_names()
        (folder / "toy.toml").write_text(_TOY_TOML + "# edited\n")
        second = namespace()
        (folder / "toy_pkg" / "extract.py").write_text(_TOY_PY + "# edited\n")
        third = namespace()
        assert len({first, second, third}) == 3
    finally:
        monkeypatch.delenv("GRAPHIFY_LANG_PATH")
        registry.reset()
        core._fingerprint.cache_clear()
        cache._EXTRACTOR_VERSION = saved


# --- E4 ------------------------------------------------------------------------

def _lang_check(env_path: str | None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items()
           if k not in ("GRAPHIFY_LANG_DISABLE", "GRAPHIFY_LANG_PATH")}
    if env_path is not None:
        env["GRAPHIFY_LANG_PATH"] = env_path
    return subprocess.run([sys.executable, "-m", "graphify", "lang", "list", "--check"],
                          capture_output=True, text=True, env=env)


def test_e4_lang_list_check(tmp_path):
    clean = _lang_check(None)
    rows = [line.split() for line in clean.stdout.splitlines()]
    assert clean.returncode == 0, clean.stderr
    assert len(rows) == 9 and all(r[1] == "ok" for r in rows), clean.stdout

    folder = _toy_folder(tmp_path / "plugins")
    (folder / "broken.toml").write_text("[language\n")
    bad = _lang_check(str(folder))
    assert bad.returncode == 1
    rows = {line.split()[0]: line for line in bad.stdout.splitlines()}
    assert rows["toy"].split()[1] == "ok"
    broken = str(folder / "broken.toml")
    assert rows[broken].split()[1] == "error:" and "TOML parse error" in rows[broken]


# --- M3 ------------------------------------------------------------------------

def _claimed_files(root: Path) -> dict[str, Path]:
    files = {
        "xml": FIXTURES / "ecschema" / "Base.01.00.00.ecschema.xml",
        "yml": FIXTURES / "astgrep" / "rules" / "python" / "no-eval.yml",
        "toml": FIXTURES / "cargo" / "Cargo.toml",
        "md": FIXTURES / "cc_kb" / "docs" / "cc-XX000.001.md",
    }
    out = {}
    for key, src in files.items():                             # whole trees: [match] and roots
        tree = src.relative_to(FIXTURES).parts[0]
        if not (root / tree).exists():
            shutil.copytree(FIXTURES / tree, root / tree)
        out[key] = root / src.relative_to(FIXTURES)
    return out


def test_m3_watch_triggers_on_claimed_xml_yml_toml_md(tmp_path):
    from graphify.watch import _batch_needs_llm_flag, _batch_triggers_rebuild

    files = _claimed_files(tmp_path)
    for key, path in files.items():
        assert _batch_triggers_rebuild([path]) is True, key
    for key in ("xml", "yml"):                                  # language claims: code
        assert _batch_needs_llm_flag([files[key]]) is False, key
    assert _batch_needs_llm_flag([files["md"]]) is True        # an augmented doc stays a doc
    plain_toml = tmp_path / "pyproject.toml"
    plain_toml.write_text("[project]\nname = 'x'\n")
    plain_xml = tmp_path / "settings.xml"
    plain_xml.write_text("<settings/>\n")
    assert _batch_triggers_rebuild([plain_toml]) is False
    assert _batch_triggers_rebuild([plain_xml]) is False


def _watchdog_available() -> bool:
    try:
        import watchdog  # noqa: F401
    except ImportError:
        return False
    return True


@pytest.mark.skipif(not _watchdog_available(), reason="watchdog not installed")
def test_m3_watch_handler_sees_claimed_xml(tmp_path, monkeypatch):
    from graphify import watch as watch_mod

    root = tmp_path / "corpus"
    root.mkdir()
    calls: list[Path] = []
    monkeypatch.setattr(watch_mod, "_rebuild_code", lambda p, **kw: calls.append(p) or True)
    monkeypatch.setattr(watch_mod, "_notify_only", lambda p: None)
    threading.Thread(target=watch_mod.watch, args=(root,), kwargs={"debounce": 0.2},
                     daemon=True).start()
    time.sleep(0.5)
    shutil.copy(FIXTURES / "ecschema" / "Base.01.00.00.ecschema.xml", root)
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and not calls:
        time.sleep(0.1)
    assert calls, "an ECSchema .xml write should trigger _rebuild_code"


# --- L6, L8, L10, L13, N5 ---------------------------------------------------------

def test_l6_no_upper_variants(tmp_path):
    import graphify.extract as extract
    import graphify.lang_registry as core

    for table in (core.get_code_suffixes(), core.get_registry_suffixes(), set(extract._DISPATCH)):
        plugin = {s for s in table if s.lower() in {".lsp", ".mnl", ".dcl", ".bas", ".frm",
                                                     ".mki", ".mke", ".xml", ".yml", ".yaml"}}
        assert plugin == {s.lower() for s in plugin}, sorted(plugin)
    src = tmp_path / "ERR.LSP"
    src.write_text("(defun c:go () (princ))\n")
    labels = {n["label"] for n in extract._get_extractor(src)(src)["nodes"]}
    assert "c:go" in labels                                     # upstream lower-cases the suffix


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="L8: core hook sites swallow errors silently")
def test_l8_hook_error_logged(tmp_path, monkeypatch, caplog):
    from graphify.detect import classify_file
    from graphify.extract import _get_extractor

    def boom(*a, **k):
        raise RuntimeError("l8 boom")

    monkeypatch.setattr(registry, "claims_file", boom)
    monkeypatch.setattr(registry, "augment_extractor", boom)
    xml = tmp_path / "a.xml"
    xml.write_text("<a/>")
    md = tmp_path / "a.md"
    md.write_text("# a\n")
    with caplog.at_level(logging.DEBUG, logger="graphify.lang_registry"):
        classify_file(xml)
        assert _get_extractor(md) is not None                   # the stock extractor survives
    hits = [r for r in caplog.records if "l8 boom" in r.getMessage()]
    assert len(hits) == 2, [r.getMessage() for r in caplog.records]


def test_l10_claimed_yml_still_extracted(tmp_path):
    """L10 closed as accepted: a ``[match]``-only suffix keeps its router in
    ``_DISPATCH``, because ``_get_extractor`` finds extractors only there."""
    import graphify.extract as extract

    shutil.copytree(FIXTURES / "astgrep", tmp_path / "astgrep")
    rule = tmp_path / "astgrep" / "rules" / "python" / "no-eval.yml"
    assert extract._DISPATCH[".yml"].__name__ == "sniff_router[.yml]"
    kinds = {n.get("node_kind") for n in extract._get_extractor(rule)(rule)["nodes"]}
    assert "rule" in kinds, kinds


def test_l13_upper_suffix_activates_resolver():
    """Pins the fork's case-fold in ``run_language_resolvers`` (T10.4): a
    ``.LSP`` file activates the AutoLISP resolver."""
    from graphify.resolver_registry import LanguageResolver, run_language_resolvers

    autolisp = registry.get_manifest("autolisp").resolver
    ran: list[bool] = []
    spy = LanguageResolver(name="spy", suffixes=autolisp.suffixes,
                           resolve=lambda *a: ran.append(True))
    run_language_resolvers([Path("ERR.LSP")], [], [], [], resolvers=[spy])
    assert ran == [True]


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="N5: [match] filenames compare case-sensitively")
def test_n5_cargo_toml_casefold(tmp_path):
    inner = lambda p: {"nodes": [], "edges": []}               # noqa: E731
    lower = tmp_path / "cargo.toml"
    lower.write_text('[workspace]\nmembers = ["a"]\n')
    assert registry.augment_extractor(lower, inner) is not inner
