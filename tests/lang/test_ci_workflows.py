"""Plan 05 review-fix S002 - the workflow files parse, and the fork CI gates.

E2 guards the M7 class: a workflow that does not parse fails only when its
event fires, which for publish.yml is a release.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
FORK_CI = WORKFLOWS / "graphify-lang-ci.yml"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _steps(job: str) -> list[dict]:
    return _load(FORK_CI)["jobs"][job]["steps"]


def _step(job: str, needle: str) -> dict:
    found = [s for s in _steps(job) if needle in s.get("run", "")]
    assert len(found) == 1, f"{job}: {len(found)} steps run {needle!r}"
    return found[0]


@pytest.mark.parametrize("path", sorted(WORKFLOWS.glob("*.yml")), ids=lambda p: p.name)
def test_s2_e2_every_workflow_parses(path):
    data = _load(path)
    assert isinstance(data, dict) and isinstance(data.get("jobs"), dict) and data["jobs"]
    assert True in data or "on" in data  # PyYAML reads the bare key `on` as True


def test_s2_m1_pip_audit_skips_the_editable_project_and_gates():
    step = _step("security-scan", "pip-audit")
    assert "--skip-editable" in step["run"] and "--strict" not in step["run"]
    assert not step.get("continue-on-error")


def test_s2_m2_bandit_over_the_fork_layer_gates():
    step = _step("security-scan", "bandit -r graphify_lang -ll")
    assert not step.get("continue-on-error")


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="S2-L1 red")
def test_s2_l1_matrix_does_not_fail_fast():
    assert _load(FORK_CI)["jobs"]["test"]["strategy"].get("fail-fast") is False


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="S2-N1 red")
def test_s2_n1_token_is_read_only():
    assert _load(FORK_CI).get("permissions") == {"contents": "read"}


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="S2-N2 red")
def test_s2_n2_tag_filter_matches_fork_tags_only():
    assert _load(FORK_CI)[True]["push"]["tags"] == ["v*\\+lang.*"]


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="S2-E1 red")
def test_s2_e1_tag_run_installs_the_wheel_and_loads_every_plugin():
    jobs = _load(FORK_CI)["jobs"]
    assert "wheel" in jobs
    run = "\n".join(s.get("run", "") for s in jobs["wheel"]["steps"])
    assert "uv build" in run and "graphify lang list --check" in run
    assert "refs/tags/" in jobs["wheel"]["if"]
