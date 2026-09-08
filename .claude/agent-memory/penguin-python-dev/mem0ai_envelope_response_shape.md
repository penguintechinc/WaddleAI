---
name: mem0ai-envelope-response-shape
description: mem0ai 2.0.18 hosted MemoryClient.search()/get_all() return a paginated envelope dict, not a bare list — no py.typed marker so mypy can't catch it
metadata:
  type: project
---

`shared/utils/memory_integration.py`'s `Mem0MemoryStore` treated
`MemoryClient.search()`/`.get_all()` returns as a bare `list`. In the pinned
mem0ai 2.0.18, `mem0/client/main.py` shows both return
`{"count": ..., "next": ..., "previous": ..., "results": [...]}` (a paginated
envelope), confirmed by reading the installed source directly. mem0 ships no
`py.typed` marker, so under `--ignore-missing-imports` the client resolves to
`Any` and mypy never flags the mismatch — this class of bug is invisible to
the type checker and must be caught by reading the library source or by a
mocked-envelope regression test, not by mypy.

**Fix pattern**: a module-level `_normalize_mem0_results(response, source)`
helper in `memory_integration.py` that accepts both a bare list (older/OSS
mem0) and the `{"results": [...]}` envelope, logs a warning and returns `[]`
on any other shape (matches the file's existing fail-soft contract), and is
routed through at every `client.search()`/`client.get_all()` call site.
`client.add()`'s return value is never consumed in this file, so it needed no
change.

**Why this matters**: before the fix, `search_memories`/`get_recent_memories`
silently returned `[]` in production against a real mem0ai 2.0.18 client
(iterating a dict's string keys instead of the results list raised
`AttributeError` inside the broad `except Exception` blocks) — the bug was
invisible in tests too, because the existing `FakeMem0Client` test double
returned bare lists, matching only the older shape.

**How to apply**: when touching any mem0ai call site in this repo, or when
mem0ai is upgraded, re-verify this envelope shape against the installed
source (`inspect.getsourcefile(mem0)`) rather than trusting IDE/mypy
inference — pinning the version does not stop a future intentional bump from
changing shape again. If adding new mem0ai call sites, route them through
`_normalize_mem0_results` too. See [[waddleai_management_test_harness_gotchas]]
for other test-double-shape-drift gotchas in this repo's test suite.
