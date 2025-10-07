"""role setup

Revision ID: 5e997b4cc306
Revises: aa9a3b46fcd8
Create Date: 2025-10-07 14:03:24.110933

"""
import os
from typing import Sequence, Union

from alembic import op
from dotenv import load_dotenv
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e997b4cc306'
down_revision: Union[str, Sequence[str], None] = 'aa9a3b46fcd8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
env_vars = [
    "POSTGRES_DB",
    "POSTGRES_API_USER",
    "POSTGRES_API_PASSWORD",
    "POSTGRES_READONLY_USER",
    "POSTGRES_READONLY_PASSWORD"
]


def get_env_vars() -> dict[str, str]:
    """ Ensures `env_vars` exist and returns their values in a list of the same size. """
    vals = [os.getenv(var) for var in env_vars]
    if not all(vals):
        load_dotenv("../../../../../.env")  # TODO: is this platform safe, or necessary?
    
    vals = [os.getenv(var) for var in env_vars]
    assert all(vals), "Make sure these are defined in .env:" + str(env_vars)
    return dict(zip(env_vars, vals)) # type: ignore


def upgrade() -> None:
    """Upgrade schema."""
    vals = get_env_vars()
    db = vals["POSTGRES_DB"]
    api_user = vals["POSTGRES_API_USER"]
    api_pass = vals["POSTGRES_API_PASSWORD"]
    ro_user = vals["POSTGRES_READONLY_USER"]
    ro_pass = vals["POSTGRES_READONLY_PASSWORD"]
    
    # Create roles
    op.execute(f"""
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

    # Grant Priveleges
    op.execute(f"""
        GRANT CONNECT ON DATABASE {db} TO {api_user}, {ro_user};
        GRANT USAGE ON SCHEMA asset TO {api_user}, {ro_user};
        GRANT USAGE ON SCHEMA identity TO {api_user}, {ro_user};
        GRANT USAGE ON SCHEMA operation TO {api_user}, {ro_user};
        GRANT USAGE ON SCHEMA ref TO {api_user}, {ro_user};
        
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA asset TO {api_user};
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA identity TO {api_user};
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA operation TO {api_user};
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ref TO {api_user};
        ALTER DEFAULT PRIVILEGES IN SCHEMA asset GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {api_user};
        ALTER DEFAULT PRIVILEGES IN SCHEMA identity GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {api_user};
        ALTER DEFAULT PRIVILEGES IN SCHEMA operation GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {api_user};
        ALTER DEFAULT PRIVILEGES IN SCHEMA ref GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {api_user};
        
        GRANT SELECT ON ALL TABLES IN SCHEMA asset TO {ro_user};
        GRANT SELECT ON ALL TABLES IN SCHEMA identity TO {ro_user};
        GRANT SELECT ON ALL TABLES IN SCHEMA operation TO {ro_user};
        GRANT SELECT ON ALL TABLES IN SCHEMA ref TO {ro_user};
        ALTER DEFAULT PRIVILEGES IN SCHEMA asset GRANT SELECT ON TABLES TO {ro_user};
        ALTER DEFAULT PRIVILEGES IN SCHEMA identity GRANT SELECT ON TABLES TO {ro_user};
        ALTER DEFAULT PRIVILEGES IN SCHEMA operation GRANT SELECT ON TABLES TO {ro_user};
        ALTER DEFAULT PRIVILEGES IN SCHEMA ref GRANT SELECT ON TABLES TO {ro_user};
        
        REVOKE CREATE ON SCHEMA public FROM {api_user}, {ro_user};
    """)
    

def downgrade() -> None:
    """Downgrade schema."""
    vals = get_env_vars()
    op.execute(f"DROP ROLE IF EXISTS {vals['POSTGRES_API_USER']};")
    op.execute(f"DROP ROLE IF EXISTS {vals['POSTGRES_READONLY_USER']};")
