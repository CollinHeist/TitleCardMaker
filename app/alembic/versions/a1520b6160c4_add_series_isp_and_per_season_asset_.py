"""Add Series ISP and per season asset support

Revision ID: a1520b6160c4
Revises: db6a1eda7d21
Create Date: 2024-09-23 09:45:44.623721
"""

from alembic import op
import sqlalchemy as sa

from modules.Debug import contextualize
from modules.Debug2 import logger 

# Revision identifiers, used by Alembic.
revision = 'a1520b6160c4'
down_revision = 'db6a1eda7d21'
branch_labels = None
depends_on = None


def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.alter_column('emby_id',
            existing_type=sa.INTEGER(),
            type_=sa.String(),
            existing_nullable=False
        )

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'use_per_season_assets',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ))
        batch_op.add_column(sa.Column(
            'image_source_priority',
            sa.JSON(),
            nullable=True,
            server_default=None,
        ))
        batch_op.alter_column('emby_id',
            existing_type=sa.INTEGER(),
            type_=sa.String(),
            existing_nullable=True,
        )

    with op.batch_alter_table('template', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'image_source_priority',
            sa.JSON(),
            nullable=True,
            server_default=None,
        ))

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('template', schema=None) as batch_op:
        batch_op.drop_column('image_source_priority')

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.alter_column('emby_id',
            existing_type=sa.String(),
            type_=sa.INTEGER(),
            existing_nullable=True
        )
        batch_op.drop_column('image_source_priority')
        batch_op.drop_column('use_per_season_assets')

    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.alter_column('emby_id',
            existing_type=sa.String(),
            type_=sa.INTEGER(),
            existing_nullable=False
        )

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
