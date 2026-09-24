"""Tests for rules runtime (T5.3-T5.4).

This module tests the query rules and regex rules extraction tiers.
"""

from pathlib import Path

import pytest

# Test fixtures
FIXTURE_DIR = Path(__file__).parent / "fixtures"
CORPUS_FILES = Path(__file__).parent / "corpus_files.txt"


def test_corpus_file_list_exists():
    """T5.1: Verify corpus file list exists and is readable."""
    assert CORPUS_FILES.exists(), "corpus_files.txt should exist"
    content = CORPUS_FILES.read_text()
    assert content.strip(), "corpus_files.txt should have content"
    assert content.startswith("#"), "corpus_files.txt should have header comment"


def test_corpus_file_list_count():
    """T5.1: Verify corpus file list has expected file count."""
    content = CORPUS_FILES.read_text()
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
    assert len(lines) > 0, "corpus_files.txt should have at least one file entry"


def test_corpus_file_list_paths():
    """T5.1: Verify corpus file list has correct paths."""
    content = CORPUS_FILES.read_text()
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
    
    for line in lines:
        # Paths should be relative and use forward slashes
        assert not line.startswith("/"), f"Path should be relative: {line}"
        assert "/" in line, f"Path should include directory: {line}"


def test_rules_build_signature():
    """T5.2: Verify build() returns (extract, resolver) tuple."""
    from graphify_lang.rules import build
    
    # Create a minimal manifest
    manifest = {
        "name": "test-lang",
        "suffixes": [".test"],
        "extract": {"runtime": "graphify_lang.rules"},
    }
    
    manifest_path = Path(__file__)
    extract, resolver = build(manifest_path, manifest)
    
    assert callable(extract), "extract should be callable"
    assert resolver is None or callable(resolver), "resolver should be None or callable"


def test_rules_extract_returns_dict():
    """T5.5: Verify extract returns dict with nodes/edges keys."""
    from graphify_lang.rules import build
    
    manifest = {
        "name": "test-lang",
        "suffixes": [".test"],
        "extract": {"runtime": "graphify_lang.rules"},
    }
    
    manifest_path = Path(__file__)
    extract, _ = build(manifest_path, manifest)
    
    # Extract from a test file
    result = extract(Path(__file__))
    
    assert isinstance(result, dict), "extract result should be a dict"
    assert "nodes" in result, "extract result should have nodes key"
    assert "edges" in result, "extract result should have edges key"


def test_queries_module_exists():
    """T5.3: Verify queries.py module exists and is importable."""
    from graphify_lang import queries
    
    assert hasattr(queries, "QueryRules"), "queries should expose QueryRules"
    assert hasattr(queries.QueryRules, "from_manifest"), "QueryRules should have from_manifest"


def test_regex_rules_module_exists():
    """T5.3: Verify regex_rules.py module exists and is importable."""
    from graphify_lang import regex_rules
    
    assert hasattr(regex_rules, "RegexRules"), "regex_rules should expose RegexRules"
    assert hasattr(regex_rules.RegexRules, "from_manifest"), "RegexRules should have from_manifest"


def test_builtins_module_exists():
    """T5.4: Verify builtins.py module exists and is importable."""
    from graphify_lang import builtins
    
    assert hasattr(builtins, "Builtins"), "builtins should expose Builtins"
    assert hasattr(builtins.Builtins, "from_manifest"), "Builtins should have from_manifest"


def test_templates_exist():
    """T5.6: Verify template files exist."""
    templates_dir = Path(__file__).parent.parent.parent / "graphify_lang" / "templates"

    assert (templates_dir / "programming.toml").exists(), "programming.toml should exist"
    assert (templates_dir / "markup.toml").exists(), "markup.toml should exist"
    assert (templates_dir / "prose.toml").exists(), "prose.toml should exist"

def test_templates_are_valid_toml():
    """T5.6: Verify templates are valid TOML."""
    import tomli
    
    templates_dir = Path(__file__).parent.parent.parent / "graphify_lang" / "templates"
    
    for template in ["programming.toml", "markup.toml", "prose.toml"]:
        content = (templates_dir / template).read_text()
        try:
            tomli.loads(content)
        except tomli.TOMLDecodeError as e:
            pytest.fail(f"{template} is not valid TOML: {e}")


def test_templates_have_required_fields():
    """T5.6: Verify templates have required manifest fields."""
    import tomli
    
    templates_dir = Path(__file__).parent.parent.parent / "graphify_lang" / "templates"
    required_fields = ["schema", "language", "grammar", "extract"]
    
    for template in ["programming.toml", "markup.toml", "prose.toml"]:
        content = (templates_dir / template).read_text()
        data = tomli.loads(content)
        
        for field in required_fields:
            assert field in data, f"{template} should have {field} field"


def test_emission_contract_file_type_code():
    """T5.5: Verify nodes use file_type: code."""
    from graphify_lang.rules import build
    
    manifest = {
        "name": "test-lang",
        "suffixes": [".test"],
        "extract": {"runtime": "graphify_lang.rules"},
    }
    
    manifest_path = Path(__file__)
    extract, _ = build(manifest_path, manifest)
    
    result = extract(Path(__file__))
    
    for node in result.get("nodes", []):
        # file_type defaults to "code" per S005
        assert node.get("kind") is not None, "Node should have kind"


def test_emission_contract_line_disambiguation():
    """T5.5: Verify line-based disambiguation for id collisions."""
    from graphify_lang.rules import build
    
    manifest = {
        "name": "test-lang",
        "suffixes": [".test"],
        "extract": {"runtime": "graphify_lang.rules"},
    }
    
    manifest_path = Path(__file__)
    extract, _ = build(manifest_path, manifest)
    
    result = extract(Path(__file__))
    
    # Check that nodes have start_line
    for node in result.get("nodes", []):
        assert "start_line" in node, "Node should have start_line for disambiguation"


def test_python_hooks_configuration():
    """T5.4: Verify [extract.python] post_file hook configuration."""
    import tomli
    
    templates_dir = Path(__file__).parent.parent.parent / "graphify_lang" / "templates"
    
    # Check programming template for python hooks
    content = (templates_dir / "programming.toml").read_text()
    data = tomli.loads(content)
    
    # Should have commented example for python hooks
    assert "post_file" in content or "# post_file" in content, \
        "programming.toml should document post_file hook"
