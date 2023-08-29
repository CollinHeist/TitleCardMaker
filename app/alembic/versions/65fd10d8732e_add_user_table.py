"""Add User table

Revision ID: 65fd10d8732e
Revises: 693dd5aa47cd
Create Date: 2023-07-31 13:34:09.097230

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '65fd10d8732e'
down_revision = '693dd5aa47cd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_id'), ['id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_id'))

    op.drop_table('user')
