"""Add Sync Interface ID

Revision ID: 086e95b52b9d
Revises: 0f092cd0f05c
Create Date: 2023-09-07 12:02:20.003251

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '086e95b52b9d'
down_revision = '0f092cd0f05c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'interface_id', sa.Integer(), nullable=False, server_default=str(0),
        ))


def downgrade() -> None:
    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.drop_column('interface_id')
