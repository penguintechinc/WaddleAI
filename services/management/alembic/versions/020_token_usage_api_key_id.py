"""Add token_usage/usage_cache.api_key_id; harden content_filter_audit_log defaults.

Fixes gh-207 (schema drift between the PyDAL runtime models
(``shared/database/models.py``) and this Alembic-authoritative schema):

1. ``shared/utils/token_manager.py`` reads/writes ``token_usage.api_key_id``
   and ``usage_cache.api_key_id`` in ~12 places, called unconditionally on
   every real chat completion (``proxy/apps/proxy_server/main.py``'s
   ``chat_completions()``). Neither column ever existed on this schema --
   only ``virtual_key_id``, tied to the separate ``virtual_keys`` table that
   the proxy request path never reads or writes (the pipeline's own
   ``MeterStage``/``TokenBudgetStage`` reference ``ctx.user.vkey_id``, an
   attribute ``shared.auth.rbac.UserContext`` -- the only class ever
   assigned to ``ctx.user`` -- never sets, so that pathway has always been
   inert; ``virtual_key_id`` is otherwise only exercised by the
   management service's own virtual-key CRUD, a separate admin feature).
   Every real (non-cache-hit) chat completion raised inside
   ``process_usage()``, caught by ``main.py``'s broad ``except Exception``,
   and returned to the client as an opaque HTTP 500. This migration adds
   ``api_key_id`` (nullable FK to ``api_keys.id``, matching the PyDAL
   model's reference target) to both tables; ``virtual_key_id`` is left in
   place (see gh-207 discussion -- dropping it is a separate, larger call
   and this migration does not touch it).

2/3. ``content_filter_audit_log.timestamp``/``degraded`` are ``NOT NULL``.
   The ORM model (``models_sqlalchemy.py``) only ever declared Python-side
   defaults (``default=datetime.utcnow`` / ``default=False``) -- migrations
   005/011's ``op.create_table``/``add_column`` calls *did* specify
   ``server_default`` for both, but per gh-207 defect 4, no real deployment
   has ever actually replayed those migration bodies: ``alembic upgrade
   head`` cannot reach past migration 002 on a genuinely fresh database
   (``001_baseline`` is a documented no-op), so every existing
   alpha/beta/gamma database was actually provisioned by a one-time manual
   ``Base.metadata.create_all()`` against the ORM model, then
   ``alembic stamp head`` -- which means the *model's* column definitions,
   not the migration scripts' DDL, are what is actually live. Both columns
   therefore exist with no server-side default in every real deployment.
   ``shared/security/content_filter.py``'s ``_log_filter_event`` inserted
   through PyDAL's *reflected* Table object (``get_db()`` defaults to
   ``reflect=True``) without either value, so the audit-log insert threw a
   NOT NULL violation on every real filtering decision, swallowed by that
   function's own broad ``except Exception`` -- the compliance audit trail
   was silently never written. Fixed at both layers: this migration adds
   ``server_default`` to both columns (holds regardless of which layer
   inserts the row), and ``_log_filter_event`` now also sets both values
   explicitly.

Safe on a populated database: the new FK columns are added nullable (no
backfill required -- existing rows simply have no known api_key_id), and
the ``content_filter_audit_log`` changes are ``ALTER COLUMN ... SET
DEFAULT`` only, which never touches existing rows.

Revision ID: 020_token_usage_api_key_id
Revises: 019_gemma4_e4b_minimum
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "020_token_usage_api_key_id"
down_revision: str | None = "019_gemma4_e4b_minimum"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(bind: sa.engine.Connection, table: str, column: str) -> bool:
    """True if `column` already exists on `table` (guard for pre-migration ORM drift)."""
    return column in {c["name"] for c in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    """Add api_key_id to token_usage/usage_cache; add server defaults to audit-log columns."""
    bind = op.get_bind()

    # gh-207 defect 1 -- guard-add api_key_id (nullable: existing rows have
    # no known key, and NOT NULL would require a backfill this migration
    # cannot safely perform). FK target matches shared/database/models.py's
    # Field("api_key_id", "reference api_keys").
    if not _has_column(bind, "token_usage", "api_key_id"):
        op.add_column(
            "token_usage",
            sa.Column(
                "api_key_id",
                sa.Integer(),
                sa.ForeignKey("api_keys.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
        op.create_index("idx_token_usage_api_key_id", "token_usage", ["api_key_id"])

    if not _has_column(bind, "usage_cache", "api_key_id"):
        op.add_column(
            "usage_cache",
            sa.Column(
                "api_key_id",
                sa.Integer(),
                sa.ForeignKey("api_keys.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
        op.create_index("idx_usage_cache_api_key_id", "usage_cache", ["api_key_id"])

    # gh-207 defects 2/3 -- server-side defaults so the row is valid
    # regardless of which layer (SQLAlchemy ORM, raw SQL, or PyDAL against
    # a reflected table) performs the insert. ALTER COLUMN ... SET DEFAULT
    # never touches existing rows.
    op.alter_column(
        "content_filter_audit_log",
        "timestamp",
        existing_type=sa.DateTime(),
        server_default=sa.func.now(),
        existing_nullable=False,
    )
    op.alter_column(
        "content_filter_audit_log",
        "degraded",
        existing_type=sa.Boolean(),
        server_default=sa.false(),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Drop the server defaults and the guard-added api_key_id columns."""
    op.alter_column(
        "content_filter_audit_log",
        "degraded",
        existing_type=sa.Boolean(),
        server_default=None,
        existing_nullable=False,
    )
    op.alter_column(
        "content_filter_audit_log",
        "timestamp",
        existing_type=sa.DateTime(),
        server_default=None,
        existing_nullable=False,
    )

    bind = op.get_bind()

    if _has_column(bind, "usage_cache", "api_key_id"):
        op.drop_index("idx_usage_cache_api_key_id", table_name="usage_cache")
        op.drop_column("usage_cache", "api_key_id")

    if _has_column(bind, "token_usage", "api_key_id"):
        op.drop_index("idx_token_usage_api_key_id", table_name="token_usage")
        op.drop_column("token_usage", "api_key_id")
