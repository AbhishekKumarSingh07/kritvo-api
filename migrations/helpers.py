"""Shared helpers for Alembic migrations (LLD section 2.2)."""

from alembic import op


def enable_tenant_rls(table: str, *, portal_customer_column: str | None = None) -> None:
    """Turn on the standard tenant-isolation policy for a table that has ``tenant_id``.

    Every migration that creates a tenant table calls this in the same migration that
    creates the table, so the two can never drift apart (LLD section 2.4 coverage check).

    ``portal_customer_column`` names the column a client-portal session may additionally
    be scoped to (LLD section 2.2's restrictive ``portal_scope`` policy) — pass it for
    tables the customer portal reads, and leave it unset for internal-only tables.
    """
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation ON {table} "
        "USING (tenant_id = app_tenant_id()) "
        "WITH CHECK (tenant_id = app_tenant_id())"
    )
    if portal_customer_column is not None:
        op.execute(
            f"CREATE POLICY portal_scope ON {table} AS RESTRICTIVE "
            f"USING (app_customer_id() IS NULL OR {portal_customer_column} = app_customer_id())"
        )


def disable_tenant_rls(table: str, *, portal_scoped: bool = False) -> None:
    """Reverse of ``enable_tenant_rls``, for migration downgrades."""
    if portal_scoped:
        op.execute(f"DROP POLICY portal_scope ON {table}")
    op.execute(f"DROP POLICY tenant_isolation ON {table}")
    op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
