"""Add Snapshot Table

Revision ID: 48872195483e
Revises: 5318f59eadbf
Create Date: 2023-11-21 15:40:38.510224

"""
from alembic import op
import sqlalchemy as sa

from modules.Debug import contextualize
from modules.Debug2 import logger

# revision identifiers, used by Alembic.
revision = '48872195483e'
down_revision = '5318f59eadbf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    op.create_table('snapshot',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('blueprints', sa.Integer(), nullable=False),
        sa.Column('cards', sa.Integer(), nullable=False),
        sa.Column('episodes', sa.Integer(), nullable=False),
        sa.Column('fonts', sa.Integer(), nullable=False),
        sa.Column('loaded', sa.Integer(), nullable=False),
        sa.Column('series', sa.Integer(), nullable=False),
        sa.Column('syncs', sa.Integer(), nullable=False),
        sa.Column('templates', sa.Integer(), nullable=False),
        sa.Column('users', sa.Integer(), nullable=False),
        sa.Column('filesize', sa.Integer(), nullable=False),
        sa.Column('cards_created', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('snapshot', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_snapshot_id'), ['id'], unique=False)

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('snapshot', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_snapshot_id'))

    op.drop_table('snapshot')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
