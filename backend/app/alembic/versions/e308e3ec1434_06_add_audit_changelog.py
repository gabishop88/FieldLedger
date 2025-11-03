"""06 add audit changelog

Revision ID: e308e3ec1434
Revises: 2030eaf24e49
Create Date: 2025-10-29 09:53:40.592417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e308e3ec1434'
down_revision: Union[str, Sequence[str], None] = '2030eaf24e49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create changelog table
    op.create_table("changelog",
    sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text("uuidv7()")),
    sa.Column("timestamp", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    sa.Column("revision", sa.String(32), nullable=False),
    sa.Column("schema", sa.String(32), nullable=False),
    sa.Column("table", sa.String(32), nullable=False),
    sa.Column("op", sa.String(32), nullable=False),
    sa.Column("role", sa.String(32), nullable=False, server_default=sa.text("SESSION_USER")),
    sa.Column("new_data", postgresql.JSONB),
    sa.Column("old_data", postgresql.JSONB),
    sa.Column("app_user", postgresql.JSONB),
    sa.PrimaryKeyConstraint('id'),
    schema="audit"
    )
    
    # Create function to get the current user
    op.execute("""--sql
    CREATE OR REPLACE FUNCTION iam.get_current_user() RETURNS jsonb
    LANGUAGE plpgsql STABLE AS $$
    DECLARE
        user_id UUID;
        user_info JSONB;
    BEGIN
        -- STEP 1: safely get app.current_user setting
        BEGIN
            user_id := current_setting('app.current_user', true)::UUID;
        EXCEPTION WHEN others THEN
            RETURN NULL;
        END;
        IF user_id IS NULL THEN 
            RETURN NULL;
        END IF;

        -- STEP 2: Get the user record and return it (or NULL if it didn't exist).
        SELECT to_jsonb(u) INTO user_info FROM iam.app_user AS u WHERE u.id = user_id;
        RETURN user_info;
    END;
    $$;
    """)
    
    # Create function to log a table change to the changelog table
    op.execute("""--sql
    CREATE OR REPLACE FUNCTION audit.change_trigger() RETURNS trigger AS $$
    DECLARE
        app_user JSONB;
        revision TEXT;
    BEGIN
        app_user := iam.get_current_user();

        SELECT version_num INTO revision FROM alembic_version LIMIT 1;

        INSERT INTO audit.changelog("revision", "schema", "table", "op", "new_data", "old_data", "app_user")
        VALUES (revision, TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP, to_jsonb(NEW), to_jsonb(OLD), app_user);

        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)
    
    # Apply the change trigger to existing tables
    op.execute("""--sql
    CREATE TRIGGER user_audit
    AFTER INSERT OR UPDATE OR DELETE ON iam.app_user
    FOR EACH ROW EXECUTE FUNCTION audit.change_trigger();
    """)
    
    op.execute("""--sql
    CREATE TRIGGER farm_audit
    AFTER INSERT OR UPDATE OR DELETE ON asset.farm
    FOR EACH ROW EXECUTE FUNCTION audit.change_trigger();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP FUNCTION IF EXISTS audit.change_trigger() CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS iam.get_current_user();")
    op.drop_table('changelog', schema='audit')
