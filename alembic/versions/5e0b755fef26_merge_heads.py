"""merge heads

Revision ID: 5e0b755fef26
Revises: ee2ce40085da, 5cdff4a59924
Create Date: 2025-06-16 18:42:34.044368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e0b755fef26'
down_revision: Union[str, None] = ('ee2ce40085da', '5cdff4a59924')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
