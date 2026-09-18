"""core tenancy tables

Revision ID: db2ddaadf0bb
Revises: 4b4537e31a98
Create Date: 2026-09-18 13:24:07.101823

"""

from alembic import op
from migrations.helpers import enable_tenant_rls

# revision identifiers, used by Alembic.
revision: str = "db2ddaadf0bb"
down_revision: str | None = "4b4537e31a98"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Tables are created first, all of them, before any RLS policy — the users table's
    # policy below references memberships, and memberships has foreign keys into users
    # and roles, so no single top-to-bottom order lets "create table" and "enable RLS"
    # be interleaved per table. Splitting the two passes avoids that ordering trap.

    # ===== tenants (LLD section 3.2) =====
    op.execute(
        "CREATE TABLE tenants ("
        "  id uuid PRIMARY KEY,"
        "  name text NOT NULL,"
        "  slug text UNIQUE NOT NULL,"
        "  gstin text,"
        "  timezone text NOT NULL DEFAULT 'Asia/Kolkata',"
        "  plan_code text NOT NULL DEFAULT 'free',"
        "  settings jsonb NOT NULL DEFAULT '{}',"
        "  status text NOT NULL DEFAULT 'active',"
        "  created_at timestamptz NOT NULL DEFAULT now(),"
        "  updated_at timestamptz NOT NULL DEFAULT now(),"
        "  version int NOT NULL DEFAULT 1"
        ")"
    )

    # ===== users (LLD section 3.2) =====
    # Global identity, no tenant_id: a user can belong to more than one tenant through
    # memberships.
    op.execute(
        "CREATE TABLE users ("
        "  id uuid PRIMARY KEY,"
        "  full_name text NOT NULL,"
        "  phone_enc bytea NOT NULL,"
        "  phone_hash bytea UNIQUE NOT NULL,"
        "  email citext UNIQUE,"
        "  password_hash text,"
        "  totp_secret_enc bytea,"
        "  preferred_lang text NOT NULL DEFAULT 'hi',"
        "  created_at timestamptz NOT NULL DEFAULT now()"
        ")"
    )

    # ===== roles (LLD section 3.2) =====
    op.execute(
        "CREATE TABLE roles ("
        "  id uuid PRIMARY KEY,"
        "  tenant_id uuid NOT NULL REFERENCES tenants(id),"
        "  name text NOT NULL,"
        "  permissions text[] NOT NULL,"
        "  is_system boolean NOT NULL DEFAULT false,"
        "  UNIQUE (tenant_id, name)"
        ")"
    )

    # ===== memberships (LLD section 3.2) =====
    op.execute(
        "CREATE TABLE memberships ("
        "  id uuid PRIMARY KEY,"
        "  tenant_id uuid NOT NULL REFERENCES tenants(id),"
        "  user_id uuid NOT NULL REFERENCES users(id),"
        "  role_id uuid NOT NULL REFERENCES roles(id),"
        "  kind text NOT NULL,"
        "  branch_id uuid,"
        "  employee_code text,"
        "  portal_customer_id uuid,"
        "  whatsapp_opt_in_at timestamptz,"
        "  privacy_notice_ack_at timestamptz,"
        "  status text NOT NULL DEFAULT 'active',"
        "  UNIQUE (tenant_id, user_id)"
        ")"
    )

    # ===== customers (LLD section 3.2) =====
    op.execute(
        "CREATE TABLE customers ("
        "  id uuid PRIMARY KEY,"
        "  tenant_id uuid NOT NULL REFERENCES tenants(id),"
        "  name text NOT NULL,"
        "  gstin text,"
        "  billing_address jsonb,"
        "  contact_phone_enc bytea,"
        "  contact_phone_hash bytea,"
        "  custom jsonb NOT NULL DEFAULT '{}'"
        ")"
    )

    # ===== sites (LLD section 3.2) =====
    op.execute(
        "CREATE TABLE sites ("
        "  id uuid PRIMARY KEY,"
        "  tenant_id uuid NOT NULL REFERENCES tenants(id),"
        "  customer_id uuid NOT NULL REFERENCES customers(id),"
        "  name text NOT NULL,"
        "  address jsonb,"
        "  lat double precision NOT NULL,"
        "  lng double precision NOT NULL,"
        "  geofence_radius_m int NOT NULL DEFAULT 150"
        "    CHECK (geofence_radius_m BETWEEN 30 AND 2000),"
        "  site_contact_phone_enc bytea"
        ")"
    )

    # ===== row-level security, now that every table it can reference exists =====

    # tenants does not use the standard tenant_isolation policy: a session only ever
    # sees its own tenant row, keyed by id rather than a tenant_id column. Platform
    # signup runs as kritvo_system, which bypasses RLS to create the row in the first place.
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY own_tenant ON tenants USING (id = app_tenant_id())")

    # A tenant session may only see users who are members of that tenant.
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY users_via_membership ON users USING ("
        "  EXISTS (SELECT 1 FROM memberships m"
        "          WHERE m.user_id = users.id AND m.tenant_id = app_tenant_id()))"
    )

    enable_tenant_rls("roles")
    enable_tenant_rls("memberships")
    # A portal session for customer X is scoped to its own row, by id.
    enable_tenant_rls("customers", portal_customer_column="id")
    enable_tenant_rls("sites", portal_customer_column="customer_id")


def downgrade() -> None:
    # users_via_membership references memberships, so PostgreSQL won't let memberships
    # be dropped while that policy still exists — drop the policy first. Every other
    # policy is dropped automatically along with its own table.
    op.execute("DROP POLICY users_via_membership ON users")

    # Dropping a table also drops any remaining policies and RLS setting on it, so the
    # rest of downgrade only needs to remove tables, in reverse-dependency order.
    op.execute("DROP TABLE sites")
    op.execute("DROP TABLE customers")
    op.execute("DROP TABLE memberships")
    op.execute("DROP TABLE roles")
    op.execute("DROP TABLE users")
    op.execute("DROP TABLE tenants")
