"""set up schemas

Revision ID: aa9a3b46fcd8
Revises: 467c05fa4c34
Create Date: 2025-10-06 16:18:49.973178

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa9a3b46fcd8'
down_revision: Union[str, Sequence[str], None] = '467c05fa4c34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # remove leftover schemas from the extensions that were removed previously
    op.execute("DROP SCHEMA IF EXISTS tiger CASCADE")
    op.execute("DROP SCHEMA IF EXISTS tiger_data CASCADE")
    op.execute("DROP SCHEMA IF EXISTS topology CASCADE")
    
    # create schemas needed to hold database tables
    op.execute("CREATE SCHEMA IF NOT EXISTS asset")
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")
    op.execute("CREATE SCHEMA IF NOT EXISTS identity")
    op.execute("CREATE SCHEMA IF NOT EXISTS operation")
    op.execute("CREATE SCHEMA IF NOT EXISTS ref")


def downgrade() -> None:
    """Downgrade schema."""
    #  not sure it is strictly necessary, but may as well put them back
    op.execute("CREATE SCHEMA IF NOT EXISTS tiger CASCADE")
    op.execute("CREATE SCHEMA IF NOT EXISTS tiger_data CASCADE")
    op.execute("CREATE SCHEMA IF NOT EXISTS topology CASCADE")
    
    # drop all schemas
    op.execute("DROP SCHEMA IF EXISTS asset")
    op.execute("DROP SCHEMA IF EXISTS audit")
    op.execute("DROP SCHEMA IF EXISTS identity")
    op.execute("DROP SCHEMA IF EXISTS operation")
    op.execute("DROP SCHEMA IF EXISTS ref")
