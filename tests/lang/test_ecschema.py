"""Plan 04 S12 - ECSchema plugin (graphify_lang/ecschema): exact pins.

Fixture tree: tests/lang/fixtures/ecschema/ - an EC 3.1 schema (Base), an
EC 3.2 schema with a comment before the root and no .ecschema.xml suffix
(sub/Domain.xml), an EC 2.0 UTF-16 schema with an ``ec:`` prefix (Legacy),
malformed XML (Broken), a DOCTYPE (Dtd), and XML / XSD that must stay as
upstream classifies them (commands.xml, settings.xml, maml.xsd). Runs the real
``graphify.extract.extract`` pipeline, so dispatch and the resolver are exercised.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pytest

import graphify_lang.ecschema.extract as ec_extract
from graphify.detect import classify_file
from graphify.extract import _get_extractor, extract
from graphify.lang_registry import format_languages
from graphify_lang.ecschema.extract import extract_ecschema

FIXTURE = Path(__file__).parent / "fixtures" / "ecschema"
CLAIMED = ["Base.01.00.00.ecschema.xml", "Broken.01.00.ecschema.xml",
           "Legacy.01.00.ecschema.xml", "sub/Domain.xml"]
UPSTREAM = ["Dtd.ecschema.xml", "commands.xml", "settings.xml", "maml.xsd"]
CORPORA = [Path.home() / "repos" / r for r in ("BentleyHelp", "bentley-pyplace")]
_CLASS_TAGS = {"ECClass", "ECEntityClass", "ECStructClass", "ECCustomAttributeClass",
               "ECRelationshipClass"}


@pytest.fixture(scope="module")
def root(tmp_path_factory):
    r = tmp_path_factory.mktemp("ecschema")
    shutil.copytree(FIXTURE, r, dirs_exist_ok=True)
    return r


@pytest.fixture(scope="module")
def graph(root, tmp_path_factory):
    files = [root / p for p in CLAIMED]
    return extract(files, cache_root=tmp_path_factory.mktemp("cache"), root=root)


def _label(graph):
    return {n["id"]: n.get("label") for n in graph["nodes"]}


def test_listed():
    row = next(line for line in format_languages().splitlines() if line.startswith("ecschema "))
    assert row.split() == ["ecschema", ".xml", "-", "sniff+match", "ecschema"]


def test_classification(root):
    # D8: only a root <ECSchema is claimed; every other .xml / .xsd is upstream's None.
    got = sorted(p.relative_to(root).as_posix() for p in root.rglob("*.x*")
                 if classify_file(p) is not None)
    assert got == sorted(CLAIMED)
    assert [classify_file(root / p) for p in UPSTREAM] == [None] * len(UPSTREAM)
    assert classify_file(root / CLAIMED[0]).value == "code"
    assert _get_extractor(root / "sub" / "Domain.xml").__name__ == "sniff_router[.xml]"


def test_nodes_exact(graph):
    got = Counter((Path(n["source_file"]).name, n.get("node_kind"), n["label"], n.get("ec_kind"))
                  for n in graph["nodes"])
    base, legacy, domain = CLAIMED[0], CLAIMED[2], "Domain.xml"
    assert got == Counter({
        (base, "file", base, None): 1,
        (base, "schema", "Base", None): 1,
        (base, "enumeration", "Status", None): 1,
        (base, "class", "Element", "entity"): 1,           # ECCustomAttributes body skipped
        (base, "class", "PhysicalElement", "entity"): 1,
        (base, "class", "Point", "struct"): 1,
        (base, "class", "Note", "custom_attribute"): 1,
        (base, "class", "ElementOwnsElements", "relationship"): 1,
        (base, "property", "Code", "primitive"): 1,
        (base, "property", "State", "primitive"): 1,
        (base, "property", "Origin", "struct"): 1,
        (base, "property", "Tags", "array"): 1,
        (base, "property", "Corners", "struct_array"): 1,
        (base, "property", "Owner", "navigation"): 1,
        (base, "property", "X", "primitive"): 1,
        (CLAIMED[1], "file", CLAIMED[1], None): 1,          # malformed: file node only
        (legacy, "file", legacy, None): 1,
        (legacy, "schema", "Legacy", None): 1,
        (legacy, "class", "Valve", "entity"): 1,
        (legacy, "class", "Port", "struct"): 1,
        (legacy, "class", "Rating", "custom_attribute"): 1,
        (legacy, "class", "ValveHasPort", "relationship"): 1,  # commented / nameless: none
        (legacy, "property", "Size", "primitive"): 1,
        (legacy, "property", "Ports", "struct_array"): 1,   # EC 2.0 isStruct array
        (domain, "file", domain, None): 1,
        (domain, "schema", "Domain", None): 1,
        (domain, "class", "Pump", "entity"): 1,
        (domain, "class", "PumpFeedsElement", "relationship"): 1,
        (domain, "property", "State", "primitive"): 1,
        (domain, "property", "Inlet", "struct"): 1,
    })


def test_attrs(graph):
    by = {(Path(n["source_file"]).name, n["label"]): n for n in graph["nodes"]}
    assert {k: by[("Base.01.00.00.ecschema.xml", "Base")][k]
            for k in ("ec_version", "version", "alias", "ec_references")} == {
        "ec_version": "3.1", "version": "01.00.00", "alias": "bs",
        "ec_references": ["CoreCustomAttributes.01.00.00"]}
    assert by[("Legacy.01.00.ecschema.xml", "Legacy")]["ec_version"] == "2.0"
    assert by[("Domain.xml", "Domain")]["ec_references"] == ["Base.01.00.00", "Missing.01.00.00"]
    assert by[("Base.01.00.00.ecschema.xml", "Element")]["modifier"] == "Abstract"
    assert by[("Base.01.00.00.ecschema.xml", "Status")]["ec_backing_type"] == "int"
    assert by[("Base.01.00.00.ecschema.xml", "Owner")]["ec_type"] == "ElementOwnsElements"
    assert by[("Domain.xml", "Inlet")]["ec_type"] == "bs:Point"
    assert by[("Legacy.01.00.ecschema.xml", "Valve")]["source_location"] == "L4"  # UTF-16 lines


def test_edges_exact(graph):
    lab = _label(graph)
    got = sorted((e["relation"], lab[e["source"]], lab[e["target"]], e["confidence"])
                 for e in graph["edges"] if e["relation"] != "contains")
    assert got == sorted([
        ("uses", "State", "Status", "EXTRACTED"),
        ("uses", "Origin", "Point", "EXTRACTED"),
        ("uses", "Corners", "Point", "EXTRACTED"),
        ("uses", "Owner", "ElementOwnsElements", "EXTRACTED"),
        ("inherits", "PhysicalElement", "Element", "EXTRACTED"),
        ("source_constraint", "ElementOwnsElements", "Element", "EXTRACTED"),
        ("target_constraint", "ElementOwnsElements", "Element", "EXTRACTED"),  # own alias
        ("uses", "Ports", "Port", "EXTRACTED"),
        ("source_constraint", "ValveHasPort", "Valve", "EXTRACTED"),
        ("target_constraint", "ValveHasPort", "Port", "EXTRACTED"),
        ("source_constraint", "PumpFeedsElement", "Pump", "EXTRACTED"),
        # cross-file (resolve.py); Missing / ms:Ghost and CoreCustomAttributes do not resolve
        ("imports", "Legacy", "Base", "EXTRACTED"),        # 01.00 == 01.00.00
        ("imports", "Domain", "Base", "EXTRACTED"),
        ("inherits", "Valve", "PhysicalElement", "EXTRACTED"),
        ("inherits", "Pump", "PhysicalElement", "EXTRACTED"),
        ("inherits", "PumpFeedsElement", "ElementOwnsElements", "EXTRACTED"),
        ("uses", "State", "Status", "EXTRACTED"),
        ("uses", "Inlet", "Point", "EXTRACTED"),
        ("target_constraint", "PumpFeedsElement", "Element", "EXTRACTED"),
    ])
    contains = Counter(e["relation"] for e in graph["edges"])["contains"]
    assert contains == 26   # 30 nodes; every one but the 4 file nodes has one parent


@pytest.mark.parametrize("name, reason", [("Broken.01.00.ecschema.xml", "mismatched tag"),
                                          ("Dtd.ecschema.xml", "DOCTYPE refused")])
def test_bad_xml_warns_and_keeps_file_node(caplog, name, reason):
    with caplog.at_level(logging.WARNING, logger=ec_extract.__name__):
        result = extract_ecschema(FIXTURE / name)
    assert [n["node_kind"] for n in result["nodes"]] == ["file"]
    assert reason in caplog.text


def test_duplicate_schema_prefers_nearest(tmp_path):
    # The same schema checked in twice: the copy sharing the longer path prefix wins.
    for d in ("a", "b"):
        (tmp_path / d).mkdir()
        shutil.copy(FIXTURE / CLAIMED[0], tmp_path / d / CLAIMED[0])
    shutil.copy(FIXTURE / "sub" / "Domain.xml", tmp_path / "a" / "Domain.xml")
    files = [tmp_path / "a" / CLAIMED[0], tmp_path / "b" / CLAIMED[0], tmp_path / "a" / "Domain.xml"]
    graph = extract(files, cache_root=tmp_path / "cache", root=tmp_path)
    src = {n["id"]: n["source_file"] for n in graph["nodes"]}
    imports = [e for e in graph["edges"] if e["relation"] == "imports"]
    assert [(Path(src[e["target"]]).parent.name, e["confidence"]) for e in imports] == [("a", "INFERRED")]


def _truth(path: Path) -> int | None:
    """Class elements with a typeName directly under the root (ElementTree, not expat)."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    return sum(1 for c in root if c.tag.rpartition("}")[2] in _CLASS_TAGS and c.get("typeName"))


@pytest.mark.parametrize("corpus", CORPORA, ids=lambda p: p.name)
def test_corpus_class_count(tmp_path, corpus):
    if not (corpus / ".git").exists():
        pytest.skip(f"{corpus.name} not present")
    ls = subprocess.run(["git", "-C", str(corpus), "ls-files", "*.xml"],
                        capture_output=True, text=True, check=True).stdout.split()
    files = [corpus / p for p in ls if classify_file(corpus / p) is not None]
    assert files
    graph = extract(files, cache_root=tmp_path, root=corpus)
    got = Counter(Path(n["source_file"]).as_posix() for n in graph["nodes"]
                  if n.get("node_kind") == "class")
    for f in files:
        truth = _truth(f)
        assert got.get(f.relative_to(corpus).as_posix(), 0) == (truth or 0), f
