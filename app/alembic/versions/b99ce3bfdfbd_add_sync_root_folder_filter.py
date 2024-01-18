"""Add Sync root folder filter

Revision ID: b99ce3bfdfbd
Revises: 32ef3d4633ce
Create Date: 2024-01-17 19:11:53.744532

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from modules.Debug import contextualize

# revision identifiers, used by Alembic.
revision = 'b99ce3bfdfbd'
down_revision = '32ef3d4633ce'
branch_labels = None
depends_on = None


def upgrade() -> None:
    log = contextualize()
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('required_root_folders', sa.JSON(), nullable=False,
            server_default=sa.text("'[]'")),
        )

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize()
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.drop_column('required_root_folders')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
