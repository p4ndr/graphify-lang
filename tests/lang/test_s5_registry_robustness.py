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
    dist = None

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


def test_n5_cargo_toml_casefold(tmp_path):
    inner = lambda p: {"nodes": [], "edges": []}               # noqa: E731
    lower = tmp_path / "cargo.toml"
    lower.write_text('[workspace]\nmembers = ["a"]\n')
    assert registry.augment_extractor(lower, inner) is not inner


# --- plan 05 review-fix part 5 (cc-CR000.003 S005) ----------------------------

def _ret(tag: str) -> str:
    return ("def extract(path):\n"
            f"    return {{'nodes': [{{'id': '{tag}', 'label': '{tag}', 'file_type': 'code',\n"
            "                         'source_file': str(path)}], 'edges': []}\n")


def _path_plugin(folder: Path, name: str, runtime: str, body: str) -> Path:
    """A path plugin whose runtime is the top-level module ``<runtime>.py``."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{name}.toml").write_text(
        f'schema = 1\n[language]\nname = "{name}"\nsuffixes = [".{name}"]\n'
        f'[extract]\nruntime = "{runtime}"\n')
    (folder / f"{runtime}.py").write_text(body)
    return folder


@pytest.fixture
def _modules_restored():
    """Undo what a path plugin put into ``sys.modules`` (before the fix, a
    runtime named ``wave`` replaces the stdlib module process-wide)."""
    saved = dict(sys.modules)
    yield
    for name in [m for m in sys.modules if m not in saved]:
        del sys.modules[name]
    sys.modules.update(saved)


def test_s5_h1_path_plugins_namespaced(tmp_path, monkeypatch, _modules_restored):
    a = _path_plugin(tmp_path / "a", "alpha", "plugin", _ret("from-a"))
    b = _path_plugin(tmp_path / "b", "beta", "plugin", _ret("from-b"))
    d = _path_plugin(tmp_path / "d", "delta", "wave", _ret("from-d"))  # a stdlib name
    wave_before = sys.modules.get("wave")
    monkeypatch.setenv("GRAPHIFY_LANG_PATH", os.pathsep.join(map(str, (a, b, d))))
    src = tmp_path / "x.src"
    src.write_text("x")
    ids = {n: registry.get_manifest(n).extract(src)["nodes"][0]["id"]
           for n in ("alpha", "beta", "delta")}
    assert ids == {"alpha": "from-a", "beta": "from-b", "delta": "from-d"}
    assert sys.modules.get("wave") is wave_before                  # nothing shadowed
    assert "plugin" not in sys.modules
    import wave
    assert hasattr(wave, "open")
    check = _lang_check(os.pathsep.join(map(str, (a, b, d))))
    assert check.returncode == 0, check.stdout + check.stderr
    rows = check.stdout.splitlines()
    assert any("clash" in r and "plugin" in r for r in rows), check.stdout
    assert any("clash" in r and "wave" in r for r in rows), check.stdout


def test_s5_m1_bad_path_entry_isolated(tmp_path, monkeypatch):
    folder = _toy_folder(tmp_path / "plugins")
    bad = "~nosuchuser_zz/plugins"
    monkeypatch.setenv("GRAPHIFY_LANG_PATH", os.pathsep.join([bad, str(folder)]))
    names = registry.registered_names()
    assert "bmake" in names and "toy" in names                 # later folders still load
    assert bad in registry.load_errors()


def test_s5_m1_entry_points_failure_isolated(tmp_path, monkeypatch):
    def broken(group=None):
        raise RuntimeError("corrupt distribution metadata")
    monkeypatch.setattr(importlib.metadata, "entry_points", broken)
    folder = _toy_folder(tmp_path / "plugins")
    monkeypatch.setenv("GRAPHIFY_LANG_PATH", str(folder))
    assert registry.registered_names() == ["toy"]
    assert "corrupt distribution metadata" in registry.load_errors()["entry points"]


def test_s5_m1_check_fails_and_suffixes_kept():
    check = _lang_check("~nosuchuser_zz/plugins")
    assert check.returncode == 1, check.stdout
    env = {k: v for k, v in os.environ.items() if k != "GRAPHIFY_LANG_DISABLE"}
    env["GRAPHIFY_LANG_PATH"] = "~nosuchuser_zz/plugins"
    out = subprocess.run([sys.executable, "-c",
                          "import graphify.detect as d; print('.mki' in d.CODE_EXTENSIONS)"],
                         capture_output=True, text=True, env=env)
    assert out.stdout.strip() == "True", out.stderr


def test_s5_m1_check_fails_when_registry_unavailable(monkeypatch):
    import graphify.lang_registry as core

    monkeypatch.setattr(core, "_apply_registry", lambda: None)
    monkeypatch.setattr(core, "apply_registry", lambda: None)
    monkeypatch.setattr(core, "_REGISTRY_AVAILABLE", False)
    table, ok = core.check_languages()
    assert not ok and "registry" in table


def test_s5_m3_relative_entry_rejected(tmp_path, monkeypatch, caplog):
    _toy_folder(tmp_path / "plugins")
    monkeypatch.chdir(tmp_path / "plugins")
    monkeypatch.setenv("GRAPHIFY_LANG_PATH", ".")
    with caplog.at_level(logging.WARNING, logger="graphify_lang.registry"):
        names = registry.registered_names()
    assert "toy" not in names
    assert "absolute" in registry.load_errors().get(".", "")
    assert "absolute" in caplog.text


def test_s5_l1_lazy_sibling_import(tmp_path, monkeypatch, _modules_restored):
    body = ("def extract(path):\n"
            "    from . import s5l1_helper\n"
            "    return s5l1_helper.result(path)\n")
    folder = _path_plugin(tmp_path / "p", "lazy", "s5l1_plugin", body)
    (folder / "s5l1_helper.py").write_text(
        "def result(path):\n    return {'nodes': [{'id': 'lazy'}], 'edges': []}\n")
    monkeypatch.setenv("GRAPHIFY_LANG_PATH", str(folder))
    before = list(sys.path)
    assert registry.get_manifest("lazy").extract(tmp_path / "a.lazy")["nodes"] == [{"id": "lazy"}]
    assert sys.path == before and "s5l1_helper" not in sys.modules


def test_s5_l2_duplicate_names_first_wins(tmp_path, monkeypatch):
    first = LanguageManifest(name="good", suffixes=frozenset({".good"}), extract=lambda p: {})
    second = LanguageManifest(name="good", suffixes=frozenset({".other"}), extract=lambda p: {})
    monkeypatch.setattr(importlib.metadata, "entry_points",
                        lambda group=None: [_EP("one", first), _EP("two", second)]
                        if group == "graphify_lang_plugins" else [])
    folder = _toy_folder(tmp_path / "plugins")
    monkeypatch.setenv("GRAPHIFY_LANG_PATH", os.pathsep.join([str(folder), str(folder)]))
    assert registry.get_manifest("good") is first
    assert registry.get_manifest_for_suffix(".other") is None
    errors = registry.load_errors()
    assert "already registered" in errors.get("two", "")
    assert registry.registered_names() == ["good", "toy"]
    assert list(errors) == ["two"]                             # the repeated folder loads once


def test_s5_l3_non_manifest_toml_skipped(tmp_path, monkeypatch):
    folder = _toy_folder(tmp_path / "plugins")
    (folder / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    (folder / "ruff.toml").write_text("line-length = 99\n")
    monkeypatch.setenv("GRAPHIFY_LANG_PATH", str(folder))
    assert "toy" in registry.registered_names()
    assert registry.load_errors() == {}


def _harness(root: Path) -> dict[str, Path]:
    pages = {
        "docs/cc-XX000.001.md": "# Doc\n",
        "scripts/tool.ps1": "Write-Output 1\n",
        "agents/in-scope.md": "# A\n\nRuns `scripts/tool.ps1`.\n",
        "agents/missing.md": "# A\n\nRuns `scripts/none.ps1`.\n",
        "agents/mention.md": "# A\n\nSee cc-XX000.001.\n",
    }
    for rel, text in pages.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    return {rel: root / rel for rel in pages}


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="S5-M2: any .md with a relative link or path span is claimed")
def test_s5_m2_watch_claims_cc_mention_or_in_scope_path(tmp_path):
    import graphify.extract  # noqa: F401  (applies the registry)
    import graphify.lang_registry as core

    h = _harness(tmp_path / "harness")
    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "other.md").write_text("# O\n")
    (plain / "linked.md").write_text("# P\n\nSee [o](other.md) and `src/app.py`.\n")
    (plain / "mention.md").write_text("# P\n\nSee cc-XX000.001.\n")
    claimed = {p.name if p.parent == plain else str(p.relative_to(tmp_path / "harness")):
               core.watch_claims(p) for p in [*h.values(), *plain.glob("*.md")]
               if p.suffix == ".md"}
    assert claimed == {
        "docs/cc-XX000.001.md": False,       # a cc doc with no mention
        "agents/in-scope.md": True,          # names a file under its harness root
        "agents/missing.md": False,          # names no file
        "agents/mention.md": True,
        "other.md": False,
        "linked.md": False,                  # a relative link and a path span, no harness
        "mention.md": True,
    }


def test_s5_m2_augment_watch_predicate(tmp_path, caplog):
    """Engine side of S5-M2: an augment's ``watch`` predicate decides; with none,
    "adds anything" does; a failing predicate claims the file."""
    from dataclasses import replace

    from graphify.extract import extract_markdown

    def adds(path, base):
        return {"attrs": {base["nodes"][0]["id"]: {"aug_x": 1}}}

    def boom(path):
        raise RuntimeError("watch boom")

    doc = tmp_path / "a.md"
    doc.write_text("# T\n")
    aug = LanguageManifest(name="aug", suffixes=frozenset(), extract=lambda p: {},
                           kind="augment", augments=frozenset({".md"}),
                           match_globs=("*.md",), augment=adds)
    got = {}
    for key, manifest in (("none", aug), ("false", replace(aug, watch=lambda p: False)),
                          ("boom", replace(aug, watch=boom))):
        registry.reset()
        registry._register_manifest(manifest)
        with caplog.at_level(logging.WARNING, logger="graphify_lang.registry"):
            got[key] = registry.augment_watch_claims(doc, extract_markdown)
    assert got == {"none": True, "false": False, "boom": True}
    assert "watch boom" in caplog.text


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="S5-N1: a hook's `import logging` makes logging a local name")
def test_s5_n1_hook_logging_not_a_local_name():
    import graphify.cli
    import graphify.detect
    import graphify.extract

    hooks = []
    for module in (graphify.cli, graphify.detect, graphify.extract):
        lines = Path(module.__file__).read_text(encoding="utf-8").splitlines()
        hooks += [lines[i + 1].strip() for i, line in enumerate(lines)
                  if "graphify-lang: log, never break core" in line]
    assert len(hooks) == 7
    assert set(hooks) == {"import logging as _lang_logging"}, hooks


_TEMPLATE = Path(registry.__file__).parent / "templates" / "path-plugin"


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="S5-E1: no path-plugin template yet")
def test_s5_e1_path_plugin_template_loads(tmp_path, monkeypatch, _modules_restored):
    assert _TEMPLATE.is_dir()
    monkeypatch.setenv("GRAPHIFY_LANG_PATH", str(_TEMPLATE))
    assert "example" in registry.registered_names()
    assert registry.load_errors() == {}
    src = tmp_path / "a.example"
    src.write_text("item one\nitem two\n")
    labels = {n["label"] for n in registry.get_manifest("example").extract(src)["nodes"]}
    assert {"a.example", "one", "two"} <= labels
