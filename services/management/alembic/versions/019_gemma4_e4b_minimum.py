"""Raise the Gemma 4 floor from ``e2b`` to ``e4b`` for every internal role.

Testing on 2026-09-07 found ``gemma4:e2b`` -- the tag migrations 008 and 010
seeded as the routing-classifier / docs-fetch / summarize default -- too weak
to do the job: it does not classify tool type and complexity reliably enough
to route on. ``e4b`` is the new supported minimum for the quick/light internal
roles; general-purpose local generation should reach for ``gemma4:12b``
wherever the host can carry it (see ``shared/vectorstore/factory.py``).

This is a data migration, not a schema change. Migrations 008 and 010 are
fixed historical seeds and are deliberately left alone -- a database already
carrying their rows has to be moved forward, not rewritten -- so the update
runs here and applies to fresh installs (008 -> 010 -> 019) and existing
deployments alike.

Only rows still holding the withdrawn default are touched: an operator who
already moved an assignment to ``12b``/``26b``/``31b`` keeps their choice, and
the WHERE clause makes the upgrade idempotent. ``min_vram`` moves 2 -> 4 GB
with the registry row, since e4b's larger effective parameter count is exactly
what makes it usable and the fleet cap enforcer places on that number.

Valid Gemma 4 tags are ``e2b``/``e4b``/``12b``/``26b``/``31b`` -- the ``e``
prefix marks the MatFormer effective-size variants only, so the 12B tag is
``12b``, never ``e12b``, and ``gemma4:2b`` does not exist at all.

Revision ID: 019_gemma4_e4b_minimum
Revises: 018_model_access_policies
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "019_gemma4_e4b_minimum"
down_revision: str | None = "018_model_access_policies"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD_TAG = "gemma4:e2b"
_NEW_TAG = "gemma4:e4b"
_OLD_MIN_VRAM = 2
_NEW_MIN_VRAM = 4


def _retag(conn: sa.Connection, from_tag: str, to_tag: str, min_vram: int) -> None:
    """Move every registry and assignment row on ``from_tag`` over to ``to_tag``.

    Shared by upgrade and downgrade so the two directions cannot drift; the
    WHERE clauses keep it idempotent and leave operator-chosen tags untouched.
    """
    conn.execute(
        sa.text(
            "UPDATE model_registry SET name = :to_tag, ollama_tag = :to_tag, "
            "min_vram = :min_vram WHERE name = :from_tag"
        ),
        {"to_tag": to_tag, "from_tag": from_tag, "min_vram": min_vram},
    )
    conn.execute(
        sa.text("UPDATE model_assignments SET model_name = :to_tag WHERE model_name = :from_tag"),
        {"to_tag": to_tag, "from_tag": from_tag},
    )


def upgrade() -> None:
    """Retag the withdrawn ``gemma4:e2b`` default to ``gemma4:e4b``."""
    _retag(op.get_bind(), _OLD_TAG, _NEW_TAG, _NEW_MIN_VRAM)


def downgrade() -> None:
    """Restore ``gemma4:e2b`` -- reinstates a tag known not to work; see module docstring."""
    _retag(op.get_bind(), _NEW_TAG, _OLD_TAG, _OLD_MIN_VRAM)
