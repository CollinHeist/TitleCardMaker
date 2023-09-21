"""Create Connections Table

Revision ID: 6e1c7bf45cdc
Revises: 8a4d6ca4a0b9
Create Date: 2023-09-19 13:57:55.912386

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6e1c7bf45cdc'
down_revision = '8a4d6ca4a0b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    print(f'Updating to SQL Revision[{revision}]..')
    op.create_table('connection',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('interface', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('api_key', sa.String(), nullable=False),
        sa.Column('use_ssl', sa.Boolean(), nullable=False),
        sa.Column('downloaded_only', sa.Boolean(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('filesize_limit', sa.String(), nullable=True),
        sa.Column('integrate_with_pmm', sa.Boolean(), nullable=False),
        sa.Column('libraries', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('connection', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_connection_id'), ['id'], unique=False)

    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.alter_column('interface_id',
            existing_type=sa.INTEGER(),
            server_default=None,
            existing_nullable=False
        )
    print(f'Updated to SQL Revision[{revision}]')


def downgrade() -> None:
    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.alter_column('interface_id',
            existing_type=sa.INTEGER(),
            server_default=sa.text("'0'"),
            existing_nullable=False,
        )

    with op.batch_alter_table('connection', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_connection_id'))

    op.drop_table('connection')
