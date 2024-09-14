"""redesign mpi schema

Revision ID: 773a9759734c
Revises: 
Create Date: 2024-09-11 15:34:14.163676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '773a9759734c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('mpi_person',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('internal_id', sa.Uuid(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('mpi_external_person',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('person_id', sa.Integer(), nullable=False),
    sa.Column('external_id', sa.String(length=255), nullable=False),
    sa.Column('source', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['person_id'], ['mpi_person.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('mpi_patient',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('person_id', sa.Integer(), nullable=False),
    sa.Column('data', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['person_id'], ['mpi_person.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('mpi_blocking_key',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=50), nullable=False),
    sa.Column('value', sa.String(length=50), nullable=False),
    sa.ForeignKeyConstraint(['patient_id'], ['mpi_patient.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mpi_blocking_key_key'), 'mpi_blocking_key', ['key'], unique=False)
    op.create_index(op.f('ix_mpi_blocking_key_value'), 'mpi_blocking_key', ['value'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_mpi_blocking_key_value'), table_name='mpi_blocking_key')
    op.drop_index(op.f('ix_mpi_blocking_key_key'), table_name='mpi_blocking_key')
    op.drop_table('mpi_blocking_key')
    op.drop_table('mpi_patient')
    op.drop_table('mpi_external_person')
    op.drop_table('mpi_person')
    # ### end Alembic commands ###
