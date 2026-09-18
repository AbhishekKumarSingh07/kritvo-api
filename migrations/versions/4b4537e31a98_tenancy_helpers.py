"""tenancy helpers

Revision ID: 4b4537e31a98
Revises:
Create Date: 2026-09-18 13:22:31.496115

"""

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4b4537e31a98"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # citext gives case-insensitive, unique email columns (users.email in the next
    # migration). Trusted since PostgreSQL 13, so the database owner can install it
    # without superuser rights.
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    # LLD section 2.2. STABLE (not VOLATILE) so the planner can evaluate them once per
    # statement; current_setting(..., true) returns NULL instead of raising when unset.
    # nullif(..., '') matters: after a transaction-local setting ends, PostgreSQL can
    # return '' instead of NULL, and the RLS policy comparison must then match nothing.
    op.execute(
        "CREATE FUNCTION app_tenant_id() RETURNS uuid "
        "LANGUAGE sql STABLE AS "
        "$$ SELECT nullif(current_setting('app.tenant_id', true), '')::uuid $$"
    )
    op.execute(
        "CREATE FUNCTION app_customer_id() RETURNS uuid "
        "LANGUAGE sql STABLE AS "
        "$$ SELECT nullif(current_setting('app.customer_id', true), '')::uuid $$"
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION app_customer_id()")
    op.execute("DROP FUNCTION app_tenant_id()")
    op.execute("DROP EXTENSION IF EXISTS citext")
