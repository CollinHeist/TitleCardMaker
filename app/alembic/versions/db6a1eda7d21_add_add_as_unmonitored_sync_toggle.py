"""
Revise Sync table:
- Add add_as_unmonitored Column

Revision ID: db6a1eda7d21
Revises: 84971838f3fc
Create Date: 2024-08-09 15:57:51.273732
"""

from alembic import op
import sqlalchemy as sa

from modules.Debug import contextualize
from modules.Debug2 import logger 

# Revision identifiers, used by Alembic.
revision = 'db6a1eda7d21'
down_revision = '84971838f3fc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'add_as_unmonitored',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ))

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.drop_column('add_as_unmonitored')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
