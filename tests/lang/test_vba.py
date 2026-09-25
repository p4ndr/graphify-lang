"""Plan 04 S8 - VBA plugin (graphify_lang/vba): exact node / edge pins.

Fixture tree: tests/lang/fixtures/vba/ (Shapes.bas, Util.bas, IShape.cls,
clsCircle.cls, frmMain.frm). Runs the real ``graphify.extract.extract``
pipeline, so the registry dispatch, the `.cls` sniff router and the
cross-module resolver are all exercised.
"""
from __future__ import annotations

import getpass
import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from graphify.extract import _get_extractor, extract, extract_apex
from graphify_lang.vba.extract import extract_vba

FIXTURE = Path(__file__).parent / "fixtures" / "vba"
VBA_SUFFIXES = (".bas", ".cls", ".frm")


@pytest.fixture(scope="module")
def graph(tmp_path_factory):
    root = tmp_path_factory.mktemp("vba")
    shutil.copytree(FIXTURE, root, dirs_exist_ok=True)
    files = sorted(p for p in root.rglob("*") if p.is_file())
    return extract(files, cache_root=tmp_path_factory.mktemp("cache"), root=root)


def _ours(graph):
    return [n for n in graph["nodes"] if str(n.get("source_file", "")).endswith(VBA_SUFFIXES)]


def _edges(graph, *relations):
    lab = {n["id"]: n.get("label") for n in graph["nodes"]}
    return sorted((e["relation"], lab.get(e["source"]), lab.get(e["target"]))
                  for e in graph["edges"] if e["relation"] in relations)


def test_nodes_exact(graph):
    got = Counter((Path(n["source_file"]).name, n.get("node_kind"), n["label"]) for n in _ours(graph))
    assert got == Counter({
        ("Shapes.bas", "file", "Shapes.bas"): 1,
        ("Shapes.bas", "module", "Shapes"): 1,
        ("Shapes.bas", "declare", "GetTickCount"): 1,
        ("Shapes.bas", "type", "Point"): 1,
        ("Shapes.bas", "enum", "ShapeKind"): 1,
        ("Shapes.bas", "sub", "Draw"): 1,
        ("Shapes.bas", "sub", "Helper"): 1,
        ("Shapes.bas", "function", "Area"): 1,
        ("Shapes.bas", "sub", "WriteLog"): 1,
        ("Util.bas", "file", "Util.bas"): 1,
        ("Util.bas", "module", "Util"): 1,
        ("Util.bas", "sub", "Helper"): 1,
        ("Util.bas", "sub", "Run"): 1,
        ("IShape.cls", "file", "IShape.cls"): 1,
        ("IShape.cls", "class", "IShape"): 1,
        ("IShape.cls", "sub", "Render"): 1,
        ("clsCircle.cls", "file", "clsCircle.cls"): 1,
        ("clsCircle.cls", "class", "clsCircle"): 1,
        ("clsCircle.cls", "property", "Radius"): 2,       # Get + Let
        ("clsCircle.cls", "sub", "IShape_Render"): 1,
        ("frmMain.frm", "file", "frmMain.frm"): 1,
        ("frmMain.frm", "form", "frmMain"): 1,
        ("frmMain.frm", "sub", "UserForm_Initialize"): 1,
    })


def test_edges_exact(graph):
    """Comments, `Rem` and string literals give no call; builtins give none."""
    assert _edges(graph, "calls", "uses", "implements") == sorted([
        ("calls", "Draw", "Helper"),                 # after `:` on one line
        ("calls", "Draw", "GetTickCount"),           # Declare
        ("calls", "Draw", "Render"),                 # shape As IShape -> IShape.Render
        ("calls", "Draw", "Radius"),                 # c.Radius = ... -> Let only
        ("calls", "Helper", "WriteLog"),
        ("calls", "Run", "Helper"),                  # own private Helper, not Shapes'
        ("calls", "Run", "Draw"),                    # Shapes.Draw
        ("calls", "Run", "Area"),                    # unqualified public .bas member
        ("calls", "IShape_Render", "WriteLog"),
        ("calls", "IShape_Render", "Area"),
        ("calls", "UserForm_Initialize", "Radius"),  # mShape As clsCircle
        ("calls", "UserForm_Initialize", "Run"),     # Util.Run
        ("uses", "Draw", "Point"),
        ("uses", "Draw", "IShape"),                  # parameter type
        ("uses", "Draw", "clsCircle"),               # As New
        ("uses", "Run", "ShapeKind"),
        ("uses", "frmMain", "clsCircle"),            # module-level variable
        ("uses", "UserForm_Initialize", "clsCircle"),  # Set ... = New
        ("implements", "clsCircle", "IShape"),
    ])


def test_property_accessor_targets(graph):
    by_id = {n["id"]: n for n in graph["nodes"]}
    radius = [by_id[e["target"]].get("accessor") for e in graph["edges"]
              if e["relation"] == "calls" and by_id[e["target"]]["label"] == "Radius"]
    assert radius == ["let", "let"]


def test_contains_tree(graph):
    """file -> module / class / form -> members; every member has one parent."""
    got = _edges(graph, "contains")
    assert ("contains", "frmMain.frm", "frmMain") in got
    assert ("contains", "frmMain", "UserForm_Initialize") in got
    assert ("contains", "Shapes", "Point") in got
    members = [t for _, _, t in got if t not in {"Shapes", "Util", "IShape", "clsCircle", "frmMain"}]
    assert len(members) == len(_ours(graph)) - 10  # 5 files + 5 modules


def test_crlf_cp1252_continuation(tmp_path):
    path = tmp_path / "M\xf3dulo.bas"
    path.write_bytes(b'Attribute VB_Name = "M\xf3dulo"\r\n'
                     b"Public Function Caf\xe9( _\r\n"
                     b"    ByVal a As Long, _\r\n"
                     b"    ByVal b As Long) As Long\r\n"
                     b"    Caf\xe9 = a + Twice(b) ' Twice(0) in a comment\r\n"
                     b"End Function\r\n"
                     b"Private Function Twice(ByVal n As Long) As Long\r\n"
                     b"    Twice = n * 2\r\n"
                     b"End Function\r\n")
    result = extract_vba(path)
    nodes = {n["label"]: n for n in result["nodes"]}
    assert nodes["M\xf3dulo"]["node_kind"] == "module"
    assert (nodes["Caf\xe9"]["source_location"], nodes["Twice"]["source_location"]) == ("L2", "L7")
    assert [(e["relation"], e["source_location"]) for e in result["edges"]
            if e["relation"] == "calls"] == [("calls", "L5")]


def test_undecodable_bytes_never_raise(tmp_path):
    path = tmp_path / "noise.bas"
    path.write_bytes(bytes(range(256)) * 8)
    result = extract_vba(path)
    assert result["nodes"][0]["node_kind"] == "file"


def test_apex_sample_unchanged():
    """The shared `.cls` suffix still gives Apex files to extract_apex (D2)."""
    sample = Path(__file__).parent.parent / "fixtures" / "sample.cls"
    route = _get_extractor(sample)
    assert route.__name__ == "sniff_router[.cls]"
    assert route(sample) == extract_apex(sample)


def test_bas_and_frm_go_straight_to_vba():
    for suffix in (".bas", ".frm", ".BAS"):
        assert _get_extractor(Path("x" + suffix)) is extract_vba


def test_lang_list_rows():
    env = {k: v for k, v in os.environ.items() if k != "GRAPHIFY_LANG_DISABLE"}
    out = subprocess.run([sys.executable, "-m", "graphify", "lang", "list"],
                         capture_output=True, text=True, env=env, check=True).stdout
    rows = {line.split()[0]: line.split() for line in out.splitlines()[1:]}
    assert rows["vba"] == ["vba", ".bas", ".frm", "-", "-", "vba"]
    assert rows["vba-cls"] == ["vba-cls", ".cls*", "-", "sniff", "vba"]


def test_bim_chk_this_workbook():
    """Plan 04 §1 start point: 1 node from extract_apex; the plugin sees the class."""
    home = Path(os.path.expanduser(f"~{getpass.getuser()}"))  # conftest sandboxes HOME
    path = home / "repos/bim-chk/src/document/ThisWorkbook.cls"
    if not path.is_file():
        pytest.skip("bim-chk corpus not on this host")
    result = _get_extractor(path)(path)
    assert len(result["nodes"]) > 1
    assert Counter(n["node_kind"] for n in result["nodes"])["class"] == 1
