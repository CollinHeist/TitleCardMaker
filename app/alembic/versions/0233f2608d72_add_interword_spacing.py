"""
Modify Font table:
- Add interword_spacing column (default 0)
- Remove validate_characters column (unused)
- Explicitly make some columns non-nullable
Modify Series table:
- Add interword_spacing column (default None)
Modify Episode table:
- Add interword_spacing column (default None)

Revision ID: 0233f2608d72
Revises: 65fd10d8732e
Create Date: 2023-08-18 11:10:19.833668

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0233f2608d72'
down_revision = '65fd10d8732e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'interword_spacing',
            sa.Integer(),
            nullable=False,
            server_default=str(0),
        ))
        batch_op.alter_column('name', existing_type=sa.VARCHAR(), nullable=False)
        batch_op.alter_column('interline_spacing', existing_type=sa.INTEGER(), nullable=False)
        batch_op.alter_column('kerning', existing_type=sa.FLOAT(), nullable=False)
        batch_op.alter_column('size', existing_type=sa.FLOAT(), nullable=False)
        batch_op.alter_column('vertical_shift', existing_type=sa.INTEGER(), nullable=False)
        batch_op.drop_column('validate_characters')

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('font_interword_spacing', sa.Integer(), nullable=True))

    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.add_column(sa.Column('font_interword_spacing', sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.drop_column('font_interword_spacing')

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.drop_column('font_interword_spacing')

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.add_column(sa.Column('validate_characters', sa.BOOLEAN(), nullable=True))
        batch_op.alter_column('vertical_shift', existing_type=sa.INTEGER(), nullable=True)
        batch_op.alter_column('size', existing_type=sa.FLOAT(), nullable=True)
        batch_op.alter_column('kerning', existing_type=sa.FLOAT(), nullable=True)
        batch_op.alter_column('interline_spacing', existing_type=sa.INTEGER(), nullable=True)
        batch_op.alter_column('name', existing_type=sa.VARCHAR(), nullable=True)
        batch_op.drop_column('interword_spacing')

