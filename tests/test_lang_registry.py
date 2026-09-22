"""Tests for the language registry manifest schema and discovery.

This module tests the lang_registry.py module (T3.5).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from graphify_lang.manifest import LanguageManifest
from graphify_lang import registry
from graphify_lang.registry import (
    _init_state,
    _RegistryState,
    get_manifest,
    get_manifest_for_suffix,
    iter_manifests,
    registered_names,
    registered_suffixes,
)


class TestLanguageManifest:
    """Tests for the LanguageManifest dataclass."""

    def test_valid_manifest_round_trip(self) -> None:
        """A valid manifest parses and round-trips correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test.toml"
            manifest_path.write_text(
                """
name = "testlang"
suffixes = [".test", ".tst"]
extract = "testlang.extract:extract_testlang"
grammar = "tree-sitter-testlang"
extra = "testlang"
hook_suffixes = [".test"]
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
suffixes = [".test"]
extract = "testlang.extract:extract_testlang"
""",
                encoding="utf-8",
            )

            manifest, errors = LanguageManifest.from_toml(manifest_path)
            assert len(errors) == 1
            assert "missing required field: name" in errors[0]
            assert not manifest.name

    def test_missing_required_field_suffixes(self) -> None:
        """A manifest without 'suffixes' is rejected with one-line error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test.toml"
            manifest_path.write_text(
                """
name = "testlang"
extract = "testlang.extract:extract_testlang"
""",
                encoding="utf-8",
            )

            manifest, errors = LanguageManifest.from_toml(manifest_path)
            assert len(errors) == 1
            assert "missing required field: suffixes" in errors[0]
            assert not manifest.suffixes

    def test_missing_required_field_extract(self) -> None:
        """A manifest without 'extract' is rejected with one-line error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test.toml"
            manifest_path.write_text(
                """
name = "testlang"
suffixes = [".test"]
""",
                encoding="utf-8",
            )

            manifest, errors = LanguageManifest.from_toml(manifest_path)
            assert len(errors) == 1
            assert "missing required field: extract" in errors[0]

    def test_suffix_not_starting_with_dot(self) -> None:
        """A suffix not starting with '.' is rejected with one-line error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test.toml"
            manifest_path.write_text(
                """
name = "testlang"
suffixes = ["test"]
extract = "testlang.extract:extract_testlang"
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
name = "testlang"
suffixes = [".test", 123]
extract = "testlang.extract:extract_testlang"
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
name = "testlang"
suffixes = [".test"]
extract = "testlang.extract:extract_testlang"
hook_suffixes = [".test", 123]
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
name = "testlang"
suffixes = [".test"]
extract = "testlang.extract:extract_testlang"
extra = 123
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
name = ""
suffixes = [".test"]
extract = "testlang.extract:extract_testlang"
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
name = "testlang"
suffixes = []
extract = "testlang.extract:extract_testlang"
""",
                encoding="utf-8",
            )

            manifest, errors = LanguageManifest.from_toml(manifest_path)
            assert len(errors) == 1
            assert "suffixes must not be empty" in errors[0]


class TestRegistryDiscovery:
    """Tests for registry discovery and caching."""

    @pytest.fixture(autouse=True)
    def reset_state(self) -> None:
        """Reset the registry state before and after each test."""
        registry._STATE = None
        yield
        registry._STATE = None

    def test_registered_names_empty_initially(self) -> None:
        """registered_names() returns empty list before any registration."""
        assert registered_names() == []

    def test_iter_manifests_empty_initially(self) -> None:
        """iter_manifests() yields nothing before any registration."""
        assert list(iter_manifests()) == []

    def test_get_manifest_none_for_unknown_name(self) -> None:
        """get_manifest() returns None for unknown language."""
        assert get_manifest("nonexistent") is None

    def test_get_manifest_for_suffix_none_for_unknown_suffix(self) -> None:
        """get_manifest_for_suffix() returns None for unknown suffix."""
        assert get_manifest_for_suffix(".xyz") is None


class TestRegistryEnvironment:
    """Tests for registry environment variable handling."""

    @pytest.fixture(autouse=True)
    def reset_state(self) -> None:
        """Reset the registry state before and after each test."""
        registry._STATE = None
        yield
        registry._STATE = None

    def test_init_state_caches_state(self) -> None:
        """_init_state caches the state after first call."""
        state1 = _init_state()
        state2 = _init_state()
        assert state1 is state2  # Same object returned

    def test_init_state_respects_reset(self) -> None:
        """Resetting _STATE allows a new state to be created."""
        # Create initial state
        state1 = _init_state()
        assert state1.enabled

        # Reset
        registry._STATE = None

        # Create new state
        state2 = _init_state()
        assert state2.enabled
        assert state1 is not state2  # New object created
