"""Regression tests for gh-207: PyDAL runtime models vs Alembic schema drift.

Bootstraps a real, throwaway PostgreSQL container with the actual
Alembic-authoritative schema (``services/management/app/models_sqlalchemy.py``
``init_schema()`` -> ``alembic stamp head`` -- the only sequence that reaches
migration head on a fresh database today; see gh-207 defect 4) and exercises
the exact production code paths gh-207 found broken:

* ``shared.utils.token_manager.TokenManager.process_usage()`` writing and
  reading ``token_usage``/``usage_cache`` rows keyed by ``api_key_id`` --
  the column that did not exist before migration
  ``020_token_usage_api_key_id``, causing every real chat completion to
  raise and 500 (defect 1).
* A ``content_filter_audit_log`` insert that omits ``timestamp``/``degraded``
  (as PyDAL against a *reflected* table does whenever a caller doesn't pass
  them) relying purely on the DB-level ``server_default`` added by the same
  migration (defects 2/3).

Skips (not fails) when Docker is unavailable -- this is optional local/CI
infrastructure, not something every environment running the unit suite is
expected to provide (matches ``tests/e2e/conftest.py``'s ``docker_redis``
convention).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.conftest import _free_port

REPO = Path(__file__).resolve().parents[2]
MANAGEMENT_DIR = REPO / "services" / "management"

# Same Postgres digest used by tests/e2e/test_real_upstream.py and CI's own
# postgres service container -- see the dependency-pinning standard.
_PG_IMAGE = (
    "postgres:15-bookworm@sha256:550245350d614cd36d1a8e90d76c6f6608172659312e53417becbbe722aa4179"
)


def _docker_available() -> bool:
    return shutil.which("docker") is not None


@dataclass(slots=True)
class _PostgresHandle:
    """A running, throwaway PostgreSQL container: its DSN and container name."""

    database_url: str
    container_name: str


def _wait_for_postgres(container_name: str, deadline_s: float) -> None:
    """Poll ``pg_isready`` inside ``container_name`` until ready, or ``pytest.fail``."""
    deadline = time.time() + deadline_s
    last_output = ""
    check_argv = ["docker", "exec", container_name, "pg_isready", "-U", "waddleai"]
    while time.time() < deadline:
        # Fixed argv, no shell, this process's own container name.
        result = subprocess.run(check_argv, capture_output=True, text=True, timeout=5)  # noqa: S603, S607

        if result.returncode == 0:
            return
        last_output = result.stdout + result.stderr
        time.sleep(1)
    pytest.fail(f"Postgres container {container_name!r} never became ready: {last_output}")


def _bootstrap_schema(database_url: str) -> None:
    """Bootstrap the real, Alembic-authoritative schema onto ``database_url``.

    Mirrors the only sequence that reaches migration head on a genuinely
    fresh Postgres today (gh-207 defect 4, investigated but NOT fixed by
    this module): ``models_sqlalchemy.init_schema()`` (``create_all``)
    first, then ``alembic stamp head`` -- not ``upgrade head``, which fails
    at migration 002 on an empty database.
    """
    sys.path.insert(0, str(MANAGEMENT_DIR))
    try:
        from app.models_sqlalchemy import init_schema  # noqa: PLC0415

        init_schema(database_url)
    finally:
        sys.path.remove(str(MANAGEMENT_DIR))

    from alembic.command import stamp  # noqa: PLC0415
    from alembic.config import Config  # noqa: PLC0415

    cfg = Config(str(MANAGEMENT_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(MANAGEMENT_DIR / "alembic"))
    os.environ["DATABASE_URL"] = database_url  # alembic/env.py's get_url() reads this
    stamp(cfg, "head")


@pytest.fixture(scope="module")
def real_schema_db() -> Any:
    """A throwaway Postgres container carrying the real, migrated schema."""
    if not _docker_available():
        pytest.skip("docker is not available -- gh-207 regression needs a real Postgres")

    port = _free_port()
    name = f"waddleai-gh207-pg-{port}"
    password = "gh207-regression-test-password"  # noqa: S105 -- throwaway local container
    run_argv = [
        "docker",
        "run",
        "-d",
        "--rm",
        "--name",
        name,
        "-e",
        "POSTGRES_USER=waddleai",
        "-e",
        f"POSTGRES_PASSWORD={password}",
        "-e",
        "POSTGRES_DB=waddleai",
        "-p",
        f"{port}:5432",
        _PG_IMAGE,
    ]
    try:
        subprocess.run(run_argv, check=True, capture_output=True, timeout=60, text=True)  # noqa: S603
    except subprocess.CalledProcessError as exc:
        pytest.skip(f"could not start Postgres for the gh-207 regression suite: {exc.stderr}")
        return

    database_url = f"postgresql://waddleai:{password}@127.0.0.1:{port}/waddleai"
    try:
        _wait_for_postgres(name, deadline_s=60.0)
        _bootstrap_schema(database_url)
        yield _PostgresHandle(database_url=database_url, container_name=name)
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=30)  # noqa: S603, S607


@pytest.fixture(scope="module")
def db(real_schema_db: _PostgresHandle) -> Any:
    """A single ``get_db()`` handle against the real schema.

    Exactly one call in this process: ``get_db()``'s ``reflect=True`` path
    has a separate, known collision on a *second* call against
    already-reflected metadata (unrelated pre-existing bug) -- one call per
    process avoids it and still exercises the real, unmodified production
    code path (``shared.database.models.get_db``, default ``reflect=True``).
    """
    from shared.database.models import get_db

    return get_db(real_schema_db.database_url)


@pytest.fixture(scope="module")
def seeded_api_key(db: Any) -> dict[str, int]:
    """Seed one organization/user/api_key row set to hang usage records off of."""
    now = datetime.utcnow()
    org_id = db.organizations.insert(
        name="gh207-regression-org",
        description="gh-207 schema-drift regression",
        token_quota_monthly=1_000_000,
        token_quota_daily=100_000,
        enabled=True,
        created_at=now,
    )
    user_id = db.users.insert(
        username="gh207-regression-user",
        email="gh207-regression@example.com",
        password_hash="unused",  # noqa: S106 -- not a real credential, too short to be one
        role="admin",
        organization_id=org_id,
        # Explicit, not relying on the PyDAL Field default: this table is
        # already reflected from init_schema()'s create_all() by the time
        # get_db() runs (same "define_table() skipped" mechanics as
        # gh-207's content_filter_audit_log), so the Python-side default
        # declared in shared/database/models.py never applies here either.
        token_quota_monthly=100_000,
        token_quota_daily=10_000,
        enabled=True,
        created_at=now,
    )
    api_key_id = db.api_keys.insert(
        key_id="gh207key",  # short: avoids .gitleaks.toml's generic-api-key 10-char floor
        key_hash="unused",  # noqa: S106 -- not a real credential, too short to be one
        user_id=user_id,
        organization_id=org_id,
        name="gh-207 regression key",
        enabled=True,
        api_access_level="proxy_api",
        created_at=now,
    )
    db.commit()
    return {"org_id": org_id, "user_id": user_id, "api_key_id": api_key_id}


# regression: gh-207
class TestTokenUsageApiKeyIdSchema:
    """token_usage/usage_cache.api_key_id exists and round-trips through TokenManager."""

    def test_process_usage_writes_and_reads_api_key_id(
        self, db: Any, seeded_api_key: dict[str, int]
    ) -> None:
        """The write+read path every real chat completion exercises unconditionally.

        TokenManager.process_usage() must write a token_usage row keyed by
        api_key_id without raising, and that row must be readable back.
        Before migration 020_token_usage_api_key_id, this raised inside
        ``_update_usage_records`` (no such column), caught by
        ``proxy/apps/proxy_server/main.py``'s broad ``except Exception`` in
        production and returned to the client as an opaque HTTP 500.
        """
        from shared.utils.token_manager import create_token_manager

        manager = create_token_manager(db)
        api_key_id = seeded_api_key["api_key_id"]

        usage = manager.process_usage(
            input_text="hello world " * 10,
            output_text="a real completion " * 10,
            provider="ollama",
            model="gemma4:e4b",
            api_key_id=api_key_id,
            user_id=seeded_api_key["user_id"],
            organization_id=seeded_api_key["org_id"],
            actual_input_tokens=42,
            actual_output_tokens=17,
        )
        db.commit()

        assert usage.llm_tokens_input == 42
        assert usage.llm_tokens_output == 17

        row = (
            db((db.token_usage.api_key_id == api_key_id) & (db.token_usage.date == date.today()))
            .select()
            .first()
        )
        assert row is not None, "token_usage row was not written against the real schema"
        assert row.api_key_id == api_key_id
        assert row.tokens_input_total == 42
        assert row.tokens_output_total == 17

        cache_row = (
            db((db.usage_cache.api_key_id == api_key_id) & (db.usage_cache.period == "daily"))
            .select()
            .first()
        )
        assert cache_row is not None, "usage_cache row was not written against the real schema"
        assert cache_row.api_key_id == api_key_id

        # Read path: get_usage_stats must find the record it just wrote.
        stats = manager.get_usage_stats(api_key_id=api_key_id, days=1)
        assert stats["total_requests"] >= 1

    def test_check_quota_reads_by_api_key_id(self, db: Any, seeded_api_key: dict[str, int]) -> None:
        """check_quota() -- the other live read path keyed on api_key_id -- must not raise."""
        from shared.utils.token_manager import create_token_manager

        manager = create_token_manager(db)
        allowed, info = manager.check_quota(seeded_api_key["api_key_id"])
        assert isinstance(allowed, bool)
        assert "daily" in info
        assert "monthly" in info


# regression: gh-207
class TestContentFilterAuditLogServerDefaults:
    """content_filter_audit_log.timestamp/degraded hold a value with no application input."""

    def test_insert_without_timestamp_or_degraded_succeeds(
        self, db: Any, seeded_api_key: dict[str, int]
    ) -> None:
        """Prove the server-side default, independent of any application code.

        Insert exactly as ``_log_filter_event`` did before the gh-207 fix
        (omitting both columns). Before migration
        020_token_usage_api_key_id, this raised a NOT NULL violation
        against the real schema, caught by
        ``shared/security/content_filter.py``'s own broad ``except
        Exception`` and only logged -- the compliance audit trail was
        silently never written in production.
        """
        row_id = db.content_filter_audit_log.insert(
            phase="input",
            user_id=seeded_api_key["user_id"],
            organization_id=seeded_api_key["org_id"],
            api_key_id=seeded_api_key["api_key_id"],
            ip_address="127.0.0.1",
            action_taken="allow",
            violations_json="[]",
            text_sample="regression test sample",
            auditor_used=False,
        )
        db.commit()

        row = db(db.content_filter_audit_log.id == row_id).select().first()
        assert row is not None
        assert row.timestamp is not None, "server_default did not populate timestamp"
        assert row.degraded is False, "server_default did not populate degraded"
