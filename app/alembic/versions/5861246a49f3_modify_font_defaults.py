"""
Modify Card table:
- Change nullable/server default of font_interword_spacing Column
Modify Font table:
- Change nullable/server default of interword_spacing Column

Revision ID: 5861246a49f3
Revises: 0233f2608d72
Create Date: 2023-08-25 11:15:00.667339

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5861246a49f3'
down_revision = '0233f2608d72'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.alter_column('font_interword_spacing',
            existing_type=sa.INTEGER(),
            server_default=None,
            nullable=False,
        )

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.alter_column('interword_spacing',
            existing_type=sa.INTEGER(),
            server_default=sa.text("'0'"),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.alter_column('interword_spacing',
            existing_type=sa.INTEGER(),
            server_default=sa.text("'0'"),
            existing_nullable=False,
        )

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.alter_column('font_interword_spacing',
            existing_type=sa.INTEGER(),
            server_default=sa.text("'0'"),
            nullable=True,
        )
