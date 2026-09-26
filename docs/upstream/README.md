# Upstream PR drafts

Drafts of the pull requests the fork would send to `Graphify-Labs/graphify`
(branch `v8`), one per core seam. None is opened; opening one needs owner
approval (plan 01 T10, plan 05 hub D2). Each holds the problem, the minimal
upstream diff and a test.

| Draft | Seam | Fork finding |
|:------|:-----|:-------------|
| `pr-01-language-plugin-entry-points.md` | `detect.py` / `extract.py` registry lookups | plan 01 |
| `pr-02-resolver-context-fields.md` | `watch.py` / `cli.py` incremental context nodes | H1, E3 |
| `pr-03-watch-code-path-claims.md` | `watch.py` claimed-path trigger | M3 |
| `pr-04-resolver-suffix-casefold.md` | `resolver_registry.py` suffix case-fold | L13 |

To re-verify a draft on the current upstream:

```bash
git fetch upstream
git worktree add --detach /tmp/up-v8 upstream/v8
awk '/^```diff$/{p=1; next} /^```$/{p=0} p' docs/upstream/pr-02-resolver-context-fields.md > /tmp/pr.patch
git -C /tmp/up-v8 apply /tmp/pr.patch
(cd /tmp/up-v8 && <repo>/.venv/bin/python -m pytest tests/test_resolver_context_fields.py -q)
git worktree remove --force /tmp/up-v8
```

The drafts are independent: each applies to `upstream/v8` alone.
