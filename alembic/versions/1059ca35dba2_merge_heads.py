"""merge heads

Revision ID: 1059ca35dba2
Revises: cf715dfc56c5, f1a2b3c4d5e6
Create Date: 2026-05-19 10:59:40.536593

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1059ca35dba2'
down_revision: Union[str, Sequence[str], None] = ('cf715dfc56c5', 'f1a2b3c4d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
