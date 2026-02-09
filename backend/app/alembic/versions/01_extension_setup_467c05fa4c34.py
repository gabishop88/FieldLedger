"""01 extension setup

Revision ID: 467c05fa4c34
Revises:
Create Date: 2025-10-06 16:04:46.765496

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '467c05fa4c34'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP EXTENSION IF EXISTS postgis_topology CASCADE;")
    op.execute("DROP EXTENSION IF EXISTS postgis_tiger_geocoder CASCADE;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;") # Extension for str similarity


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm CASCADE;")
