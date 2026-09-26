"""Tests for the language registry manifest schema and discovery.

This module tests the lang_registry.py module (T3.5).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from graphify_lang.manifest import LanguageManifest
from graphify_lang import registry

class TestLanguageManifest:
    """Tests for the LanguageManifest dataclass."""

    def test_valid_manifest_round_trip(self) -> None:
        """A valid manifest parses and round-trips correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test.toml"
            manifest_path.write_text(
                """
[language]
name = "testlang"
suffixes = [".test", ".tst"]
hook_suffixes = [".test"]

[grammar]
module = "tree-sitter-testlang"
extra = "testlang"

[extract]
runtime = "testlang.extract:build"
""",
                encoding="utf-8",
            )

            manifest, errors = LanguageManifest.from_toml(manifest_path)
            assert errors == [], f"Unexpected errors: {errors}"
            assert manifest.name == "testlang"
            assert manifest.suffixes == frozenset({".test", ".tst"})
            assert manifest.grammar == "tree-sitter-testlang"
            assert manifest.extra == "testlang"
            assert manifest.hook_suffixes == (".test",)

    def test_missing_required_field_name(self) -> None:
        """A manifest without 'name' is rejected with one-line error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test.toml"
            manifest_path.write_text(
                """
[language]
suffixes = [".test"]

[extract]
runtime = "testlang.extract:build"
""",
                encoding="utf-8",
            )

            manifest, errors = LanguageManifest.from_toml(manifest_path)
            assert len(errors) == 1
            assert "missing required field: language.name" in errors[0]
            assert not manifest.name

    def test_missing_required_field_suffixes(self) -> None:
        """A manifest without 'suffixes' is rejected with one-line error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test.toml"
            manifest_path.write_text(
                """
[language]
name = "testlang"

[extract]
runtime = "testlang.extract:build"
""",
                encoding="utf-8",
            )

            manifest, errors = LanguageManifest.from_toml(manifest_path)
            assert len(errors) == 1
            assert "missing required field: language.suffixes" in errors[0]
            assert not manifest.suffixes

    def test_missing_required_field_runtime(self) -> None:
        """A manifest without 'runtime' is rejected with one-line error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test.toml"
            manifest_path.write_text(
                """
[language]
name = "testlang"
suffixes = [".test"]
""",
                encoding="utf-8",
            )

            manifest, errors = LanguageManifest.from_toml(manifest_path)
            assert len(errors) == 1
            assert "missing required field: extract.runtime" in errors[0]

    def test_suffix_not_starting_with_dot(self) -> None:
        """A suffix not starting with '.' is rejected with one-line error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test.toml"
            manifest_path.write_text(
                """
[language]
name = "testlang"
suffixes = [".test", "test"]

[extract]
runtime = "testlang.extract:build"
""",
                encoding="utf-8",
            )

            manifest, errors = LanguageManifest.from_toml(manifest_path)
            assert len(errors) == 1
            assert "suffix 'test' must start with '.'" in errors[0]

    def test_suffixes_must_be_strings(self) -> None:
        """A suffixes list containing non-strings is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test.toml"
            manifest_path.write_text(
                """
[language]
name = "testlang"
suffixes = [".test", 123]

[extract]
runtime = "testlang.extract:build"
""",
                encoding="utf-8",
            )

            manifest, errors = LanguageManifest.from_toml(manifest_path)
            assert len(errors) == 1
            assert "suffixes must contain only strings" in errors[0]

    def test_hook_suffixes_must_be_strings(self) -> None:
        """A hook_suffixes list containing non-strings is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test.toml"
            manifest_path.write_text(
                """
[language]
name = "testlang"
suffixes = [".test"]
hook_suffixes = [".test", 123]

[extract]
runtime = "testlang.extract:build"
""",
                encoding="utf-8",
            )

            manifest, errors = LanguageManifest.from_toml(manifest_path)
            assert len(errors) == 1
            assert "hook_suffixes must contain only strings" in errors[0]

    def test_extra_must_be_string(self) -> None:
        """An 'extra' field that is not a string is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test.toml"
            manifest_path.write_text(
                """
[language]
name = "testlang"
suffixes = [".test"]

[grammar]
module = "test"
extra = 123

[extract]
runtime = "testlang.extract:build"
""",
                encoding="utf-8",
            )

            manifest, errors = LanguageManifest.from_toml(manifest_path)
            assert len(errors) == 1
            assert "extra must be a string" in errors[0]

    def test_empty_name_rejected(self) -> None:
        """An empty name is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test.toml"
            manifest_path.write_text(
                """
[language]
name = ""
suffixes = [".test"]

[extract]
runtime = "testlang.extract:build"
""",
                encoding="utf-8",
            )

            manifest, errors = LanguageManifest.from_toml(manifest_path)
            assert len(errors) == 1
            assert "name must be non-empty" in errors[0]

    def test_empty_suffixes_rejected(self) -> None:
        """An empty suffixes list is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test.toml"
            manifest_path.write_text(
                """
[language]
name = "testlang"
suffixes = []

[extract]
runtime = "testlang.extract:build"
""",
                encoding="utf-8",
            )

            manifest, errors = LanguageManifest.from_toml(manifest_path)
            assert len(errors) == 1
            assert "suffixes must not be empty" in errors[0]


class TestRegistryDiscovery:
    """Tests for registry discovery and caching."""

    def test_get_manifest_returns_registered(self) -> None:
        """get_manifest returns the registered manifest."""
        manifest, errors = LanguageManifest.from_toml(
            Path(__file__).parent / "lang" / "fixtures" / "autolisp.toml"
        )
        assert errors == [], f"Unexpected errors: {errors}"
        assert manifest.name == "autolisp"

    def test_get_manifest_for_suffix(self) -> None:
        """get_manifest_for_suffix returns the correct manifest."""
        registry.reset()
        manifest = registry.get_manifest_for_suffix(".lsp")
        assert manifest is not None
        assert manifest.name == "autolisp"

    def test_get_manifest_for_unknown_suffix(self) -> None:
        """get_manifest_for_suffix returns None for unknown suffix."""
        registry.reset()
        manifest = registry.get_manifest_for_suffix(".unknown")
        assert manifest is None


class TestRegistryEnvironment:
    """Tests for registry environment variable handling."""

    def test_graphify_lang_disable(self) -> None:
        """GRAPHIFY_LANG_DISABLE disables discovery."""
        original = os.environ.get("GRAPHIFY_LANG_DISABLE")
        try:
            os.environ["GRAPHIFY_LANG_DISABLE"] = "1"
            registry.reset()
            # Discovery should be disabled
            names = registry.registered_names()
            assert "autolisp" not in names
        finally:
            if original is None:
                os.environ.pop("GRAPHIFY_LANG_DISABLE", None)
            else:
                os.environ["GRAPHIFY_LANG_DISABLE"] = original
            registry.reset()  # later in-process tests see the plugins again


def test_sc2_no_plugin_tables_match_upstream_snapshot() -> None:
    """SC2: with discovery disabled, the six core tables equal the v8 snapshot.

    Subprocess, because the registry merges are irreversible in-process.
    Regenerate tests/upstream_tables.json per scripts/snapshot_tables.py.
    """
    import json
    import subprocess
    import sys

    root = Path(__file__).resolve().parent.parent
    env = {**os.environ, "GRAPHIFY_LANG_DISABLE": "1"}
    env.pop("GRAPHIFY_LANG_PATH", None)
    out = subprocess.run(
        [sys.executable, str(root / "scripts" / "snapshot_tables.py")],
        capture_output=True, text=True, env=env, check=True,
    ).stdout
    expected = json.loads((root / "tests" / "upstream_tables.json").read_text())
    assert json.loads(out) == expected


def test_lang_list_subcommand() -> None:
    """`graphify lang list` shows each registered language; disabled -> none (D-006)."""
    import subprocess
    import sys

    def run(disable: bool) -> str:
        env = {**os.environ}
        env.pop("GRAPHIFY_LANG_DISABLE", None)
        if disable:
            env["GRAPHIFY_LANG_DISABLE"] = "1"
        return subprocess.run(
            [sys.executable, "-m", "graphify", "lang", "list"],
            capture_output=True, text=True, env=env, check=True,
        ).stdout

    rows = {line.split()[0]: line.split() for line in run(False).splitlines()[1:]}
    assert rows["autolisp"] == ["autolisp", ".lsp*", ".mnl", "tree_sitter_commonlisp", "-", "autolisp"]
    assert rows["autolisp-dcl"] == ["autolisp-dcl", ".dcl", "-", "-", "autolisp"]
    assert run(True).strip() == "No plugin languages registered."
