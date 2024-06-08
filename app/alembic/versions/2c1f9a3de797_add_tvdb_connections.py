"""Add TVDb connections

Revision ID: 2c1f9a3de797
Revises: 1be1951acc40
Create Date: 2024-06-05 17:37:07.643057
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from modules.Debug import contextualize
from modules.Debug2 import logger 

# Revision identifiers, used by Alembic.
revision = '2c1f9a3de797'
down_revision = '1be1951acc40'
branch_labels = None
depends_on = None

# Models necessary for data migration
from os import environ
from pathlib import Path
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()

class Connection(Base):
    __tablename__ = 'connection'

    id = sa.Column(sa.Integer, primary_key=True)
    # Existing columns for migrating
    integrate_with_pmm = sa.Column(sa.Boolean)
    logo_language_priority = sa.Column(sa.JSON)
    # New column
    integrate_with_kometa = sa.Column(sa.Boolean, default=False)
    language_priority = sa.Column(sa.JSON, default={})

def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.alter_column('source_file',
            existing_type=sa.VARCHAR(),
            server_default=None,
            existing_nullable=False
        )

    with op.batch_alter_table('connection', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'integrate_with_kometa', sa.Boolean(), nullable=False,
            server_default=str(False),
        ))
        batch_op.add_column(sa.Column(
            'language_priority', sa.JSON(), nullable=False,
            server_default=str([]),
        ))
        batch_op.add_column(sa.Column(
            'episode_ordering', sa.String(), nullable=False,
            server_default='default',
        ))
        batch_op.add_column(sa.Column(
            'include_movies', sa.Boolean(), nullable=False,
            server_default=str(False),
        ))

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.alter_column('replacements_in',
            existing_type=sqlite.JSON(),
            server_default=None,
            existing_nullable=False
        )
        batch_op.alter_column('replacements_out',
            existing_type=sqlite.JSON(),
            server_default=None,
            existing_nullable=False
        )
        batch_op.alter_column('line_split_modifier',
            existing_type=sa.INTEGER(),
            server_default=None,
            existing_nullable=False
        )

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.alter_column('libraries',
            existing_type=sqlite.JSON(),
            server_default=None,
            existing_nullable=False
        )
        batch_op.alter_column('auto_split_title',
            existing_type=sa.BOOLEAN(),
            server_default=None,
            existing_nullable=False
        )

    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.alter_column('required_root_folders',
            existing_type=sqlite.JSON(),
            server_default=None,
            existing_nullable=False)


    # Perform data migrations
    session = Session(bind=op.get_bind())

    for connection in session.query(Connection):
        connection.integrate_with_kometa = connection.integrate_with_pmm
        connection.language_priority = connection.logo_language_priority

    # Remove old columns post-migration
    with op.batch_alter_table('connection', schema=None) as batch_op:
        batch_op.drop_column('integrate_with_pmm')
        batch_op.drop_column('logo_language_priority')

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.alter_column('required_root_folders',
               existing_type=sqlite.JSON(),
               server_default=sa.text("'[]'"),
               existing_nullable=False)

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.alter_column('auto_split_title',
               existing_type=sa.BOOLEAN(),
               server_default=sa.text("'True'"),
               existing_nullable=False)
        batch_op.alter_column('libraries',
               existing_type=sqlite.JSON(),
               server_default=sa.text("'[]'"),
               existing_nullable=False)

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.alter_column('line_split_modifier',
               existing_type=sa.INTEGER(),
               server_default=sa.text("'0'"),
               existing_nullable=False)
        batch_op.alter_column('replacements_out',
               existing_type=sqlite.JSON(),
               server_default=sa.text("'[]'"),
               existing_nullable=False)
        batch_op.alter_column('replacements_in',
               existing_type=sqlite.JSON(),
               server_default=sa.text("'[]'"),
               existing_nullable=False)

    with op.batch_alter_table('connection', schema=None) as batch_op:
        batch_op.add_column(sa.Column('logo_language_priority', sqlite.JSON(), nullable=False))
        batch_op.add_column(sa.Column('integrate_with_pmm', sa.BOOLEAN(), nullable=False))
        batch_op.drop_column('include_movies')
        batch_op.drop_column('episode_ordering')
        batch_op.drop_column('language_priority')
        batch_op.drop_column('integrate_with_kometa')

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.alter_column('source_file',
               existing_type=sa.VARCHAR(),
               server_default=sa.text("('')"),
               existing_nullable=False)

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
