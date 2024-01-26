"""Separate Font replacements
Modify Font table
- Remove replacements column
- Create new replacements_in and replacements_out columns

Revision ID: 3122c0553b1e
Revises: b99ce3bfdfbd
Create Date: 2024-01-24 18:33:29.692652
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from modules.Debug import contextualize
from modules.Debug2 import logger

# revision identifiers, used by Alembic.
revision = '3122c0553b1e'
down_revision = 'b99ce3bfdfbd'
branch_labels = None
depends_on = None


# Models necessary for data migration
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()

class Font(Base):
    __tablename__ = 'font'

    # Referencial arguments
    id = sa.Column(sa.Integer, primary_key=True)
    # Old Column for migration
    replacements = sa.Column(sa.JSON)
    # New columns
    replacements_in = sa.Column(sa.JSON)
    replacements_out = sa.Column(sa.JSON)

def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    # Add new column
    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'replacements_in', sa.JSON(), nullable=False,
            server_default=sa.text("'[]'")
        ))
        batch_op.add_column(sa.Column(
            'replacements_out', sa.JSON(), nullable=False,
            server_default=sa.text("'[]'"),
        ))

    # Perform data migration
    session = Session(bind=op.get_bind())

    # Turn dictionary into separate lists
    for font in session.query(Font).all():
        font.replacements_in = list(font.replacements.keys())
        font.replacements_out = list(font.replacements.values())
        if font.replacements_in:
            log.debug(f'Migrated Font[{font.id}].replacements_in = {font.replacements_in}')
            log.debug(f'Migrated Font[{font.id}].replacements_out = {font.replacements_out}')

    # Commit changes
    session.commit()

    # Delete old column
    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.drop_column('replacements')

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')
    log.critical(f'SQL schema is not backwards compatible, Font replacements will be reset')

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.add_column(sa.Column('replacements', sqlite.JSON(), nullable=True))
        batch_op.drop_column('replacements_out')
        batch_op.drop_column('replacements_in')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
