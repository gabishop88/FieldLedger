"""03 role setup

Revision ID: 5e997b4cc306
Revises: aa9a3b46fcd8
Create Date: 2025-10-07 14:03:24.110933

"""

from collections.abc import Sequence

from alembic import op

from app.core.config import settings

# revision identifiers, used by Alembic.
revision: str = "5e997b4cc306"
down_revision: str | Sequence[str] | None = "aa9a3b46fcd8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    db = settings.POSTGRES_DB
    api_user = settings.POSTGRES_API_USER
    api_pass = settings.POSTGRES_API_PASSWORD
    ro_user = settings.POSTGRES_READONLY_USER
    ro_pass = settings.POSTGRES_READONLY_PASSWORD
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
    op.execute(f"DROP ROLE IF EXISTS {settings.POSTGRES_API_USER};")
    op.execute(f"DROP ROLE IF EXISTS {settings.POSTGRES_READONLY_USER};")
