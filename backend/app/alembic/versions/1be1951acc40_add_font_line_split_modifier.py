"""Add Font line split modifier
Modify Font table
- Add Font.line_split_modifier column

Revision ID: 1be1951acc40
Revises: f1692007cf8a
Create Date: 2024-03-10 12:09:39.027360
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from modules.Debug import contextualize
from modules.Debug2 import logger 

# Revision identifiers, used by Alembic.
revision = '1be1951acc40'
down_revision = 'f1692007cf8a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'line_split_modifier',
            sa.Integer(),
            nullable=False,
            server_default=str(0),
        ))

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.drop_column('line_split_modifier')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
