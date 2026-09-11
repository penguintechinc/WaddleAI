---
name: proxy-worker-race-startup-bug
description: waddleai proxy container crashes in CI (4-worker race on schema bootstrap) — root-caused, not fixed, PR #152
metadata:
  type: project
---

waddleai `release/v0.2.X` integration-test: proxy container never starts in CI
(4th startup bug in the proxy-boot chain, found 2026-08-28, reported in PR #152,
not fixed — see BOUNDARY below).

**Root cause**: `proxy/Dockerfile` CMD runs `hypercorn apps.proxy_server.main:app
--workers 4`, spawning 4 independent OS processes (`multiprocessing` spawn
context). Each process independently calls `ProxyServer.startup()` →
`shared/database/models.py:get_db()` → `define_tables()`, with **no
cross-process lock**. On a fresh/empty DB, all 4 workers race to
`CREATE TABLE` for the same table names; Postgres accepts the first and the
rest crash with `psycopg2.errors.UniqueViolation` on
`pg_type_typname_nsp_index` (table varies non-deterministically — hit
`routing_rules_v2` once, `users` the next run). hypercorn surfaces this as a
`LifespanFailureError` and the whole container exits (exit code 0) within
6-13s.

PR #151's `_define_table_if_absent()` fix (commit `40e235e6`) only guards the
**single-process** reflect-then-define collision (skip `db.define_table()`
when the name is already in that process's own `db.tables`) — it does
nothing for multiple OS processes racing each other on a table that doesn't
exist anywhere yet. That fix's own local validation pre-loaded Postgres with
management's schema before starting proxy (so no CREATE TABLE ever ran,
no race window) — it never exercised the concurrent-bootstrap path the real
compose harness hits.

**Reproduction** (deterministic, twice, different table each time): built
the proxy image exactly as the `build-platform` CI job does (`docker buildx
build --platform linux/amd64 -f proxy/Dockerfile --build-arg BUILD_DATE=...
--build-arg VCS_REF=<sha> .`, repo-root context, no `target:`), ran it via
the real Dockerfile CMD against a fresh Postgres 15 container with only
`DATABASE_URL`+`LOG_LEVEL` env (matching the compose heredoc exactly), no
manual delay. Proxy races against **itself** — management doesn't need to be
running to trigger it.

**Not a missing-env issue**: `REDIS_URL`/`MANAGEMENT_SERVER_URL` both default
safely and `redis.from_url()` is lazy (no I/O at construction) — confirmed by
reading `main.py` and by the repro never reaching redis code before crashing
on the DB-table race.

**Possible fixes** (none applied — see [[boundary]]): a Postgres advisory
lock around `define_tables()`; single-worker schema bootstrap before
hypercorn forks to N workers; or move schema authority fully to
Alembic/management and make proxy's `get_db()` reflect-only (never call
`define_table()`).

**BOUNDARY — why not fixed here**: user set an explicit stop condition for
this investigation chain — a genuine proxy-source concurrency bug (not a
CI timing/env issue) means STOP and report rather than fix, because the
user wants to commission a holistic proxy-container-boot review instead of
another incremental patch. Only `.github/workflows/docker-build.yml` was
touched in PR #152 (readiness wait + failure-time `docker compose
ps`/`logs` dump) — no proxy source changed.

**mem0 note**: `mcp__mem0__add_memory` was broken server-side at the time
this was written (`AttributeError: 'str' object has no attribute 'get'` in
`mem0/memory/main.py:992`, unrelated to this task) — this finding lives only
in this file until mem0 is fixed and it gets re-added there too.

**UPDATE (2026-08-28, later same day)**: owner approved the proper fix.
`fix/proxy-schema-ownership` (worktree `.worktrees/proxy-schema-owner`, off
release commit `90cdd9777f5583f1a274d38a51dd767d55625e78`) makes the proxy
stop owning the schema entirely — single-process init / advisory lock, not
a blanket `migrate=False` (that would break contract tests, which apparently
rely on proxy-side table creation in some path). Being validated with 3x
clean `--workers 4` runs + all 5 integration endpoints green + contract
80/80 locally before push. This is the 4th and (per coordinator) hopefully
final release-CI-repair exemption in this chain: #149 (proxy Dockerfile
wrong requirements.txt) -> #150 (management REDIS_URL hardcoded in
TestingConfig) -> #151 (redundant migration step + proxy relative-import +
compose port 8000:8080 + MetaData double-registration guard) -> #152
(diagnostics only: proxy log dump + readiness wait -- this is what surfaced
the UniqueViolation crash in CI for the first time, confirming the
root-cause analysis in this file) -> fix/proxy-schema-ownership (the actual
fix, in flight).

**mem0 retry (2026-08-28)**: `mcp__mem0__add_memory` still throws the same
`AttributeError: 'str' object has no attribute 'get'` in
`mem0/memory/main.py:992` -- still broken server-side, not yet re-added
there.
