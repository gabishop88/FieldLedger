"""03 role setup

Revision ID: 5e997b4cc306
Revises: aa9a3b46fcd8
Create Date: 2025-10-07 14:03:24.110933

"""

import os
from collections.abc import Sequence

from alembic import op
from dotenv import load_dotenv

# revision identifiers, used by Alembic.
revision: str = "5e997b4cc306"
down_revision: str | Sequence[str] | None = "aa9a3b46fcd8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
env_vars = [
    "POSTGRES_DB",
    "POSTGRES_API_USER",
    "POSTGRES_API_PASSWORD",
    "POSTGRES_READONLY_USER",
    "POSTGRES_READONLY_PASSWORD",
]


def get_env_vars() -> dict[str, str | None]:
    """Ensures `env_vars` exist and returns their values in a list of the same size."""
    vals = [os.getenv(var) for var in env_vars]
    if not all(vals):
        load_dotenv("../../../../../.env")  # TODO: is this platform safe, or necessary?

    vals = [os.getenv(var) for var in env_vars]
    assert all(vals), "Make sure these are defined in .env: " + str(env_vars)
    return dict(zip(env_vars, vals, strict=False))


def upgrade() -> None:
    """Upgrade schema."""
    vals = get_env_vars()
    db = vals["POSTGRES_DB"]
    api_user = vals["POSTGRES_API_USER"]
    api_pass = vals["POSTGRES_API_PASSWORD"]
    ro_user = vals["POSTGRES_READONLY_USER"]
    ro_pass = vals["POSTGRES_READONLY_PASSWORD"]
    schemas = ["asset", "iam", "operation", "ref"]

    # Create roles
    op.execute(f"""--sql
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='{api_user}') THEN
                CREATE ROLE {api_user} LOGIN PASSWORD '{api_pass}';
            END IF;
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='{ro_user}') THEN
                CREATE ROLE {ro_user} LOGIN PASSWORD '{ro_pass}';
            END IF;
        END$$;
    """)

    # Let new roles connect and read/write on new schemas
    # Prevent non-admin roles from creating in public schema.
    op.execute(f"""--sql
        GRANT CONNECT ON DATABASE {db} TO {api_user}, {ro_user};
        GRANT USAGE ON SCHEMA {", ".join(schemas)} TO {api_user}, {ro_user};
        REVOKE CREATE ON SCHEMA public FROM {api_user}, {ro_user};
    """)

    for schema in schemas:
        op.execute(f"""--sql
            GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema} TO {api_user};
            GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {ro_user};
            ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {api_user};
            ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO {ro_user};
        """)  # noqa: E501


def downgrade() -> None:
    """Downgrade schema."""
    vals = get_env_vars()
    op.execute(f"DROP ROLE IF EXISTS {vals['POSTGRES_API_USER']};")
    op.execute(f"DROP ROLE IF EXISTS {vals['POSTGRES_READONLY_USER']};")
