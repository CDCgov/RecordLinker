"""empty message

Revision ID: 591a56cee781
Revises: 0c90faa0378f, 64ed9566f189
Create Date: 2024-09-25 14:56:42.211982

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '591a56cee781'
down_revision: Union[str, None] = ('0c90faa0378f', '64ed9566f189')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
