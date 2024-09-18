"""Modify Font table:
- Remove delete_missing column

Revision ID: 248e35b3e455
Revises: 2c1f9a3de797
Create Date: 2024-07-08 22:09:28.805591
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from modules.Debug import contextualize
from modules.Debug2 import logger 

# Revision identifiers, used by Alembic.
revision = '248e35b3e455'
down_revision = '2c1f9a3de797'
branch_labels = None
depends_on = None


def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    with op.batch_alter_table('connection', schema=None) as batch_op:
        batch_op.alter_column('integrate_with_kometa',
            existing_type=sa.BOOLEAN(),
            server_default=None,
            existing_nullable=False
        )
        batch_op.alter_column('language_priority',
            existing_type=sqlite.JSON(),
            server_default=None,
            existing_nullable=False
        )
        batch_op.alter_column('episode_ordering',
            existing_type=sa.VARCHAR(),
            server_default=None,
            existing_nullable=False
        )
        batch_op.alter_column('include_movies',
            existing_type=sa.BOOLEAN(),
            server_default=None,
            existing_nullable=False
        )

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.drop_column('delete_missing')

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'delete_missing',
            sa.BOOLEAN(),
            nullable=False,
            server_default=sa.true(),
        ))

    with op.batch_alter_table('connection', schema=None) as batch_op:
        batch_op.alter_column('include_movies',
            existing_type=sa.BOOLEAN(),
            server_default=sa.text("'False'"),
            existing_nullable=False
        )
        batch_op.alter_column('episode_ordering',
            existing_type=sa.VARCHAR(),
            server_default=sa.text("'default'"),
            existing_nullable=False
        )
        batch_op.alter_column('language_priority',
            existing_type=sqlite.JSON(),
            server_default=sa.text("'[]'"),
            existing_nullable=False
        )
        batch_op.alter_column('integrate_with_kometa',
            existing_type=sa.BOOLEAN(),
            server_default=sa.text("'False'"),
            existing_nullable=False
        )

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
