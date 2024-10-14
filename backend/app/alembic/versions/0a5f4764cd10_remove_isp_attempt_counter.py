"""Modify Episode table
- Remove image_source_attempts column

Revision ID: 0a5f4764cd10
Revises: 248e35b3e455
Create Date: 2024-07-13 20:39:29.112032
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from modules.Debug import contextualize
from modules.Debug2 import logger 

# Revision identifiers, used by Alembic.
revision = '0a5f4764cd10'
down_revision = '248e35b3e455'
branch_labels = None
depends_on = None


def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.drop_column('image_source_attempts')

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'image_source_attempts',
            sqlite.JSON(),
            nullable=False
        ))

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
