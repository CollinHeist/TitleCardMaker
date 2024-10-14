"""
Modify Font table
- Add new file_name Column
- Remove file Column
- Perform data migration of existing Font filenames

Revision ID: 4d7cb48238be
Revises: 5861246a49f3
Create Date: 2023-09-11 20:20:14.124994
"""

from alembic import op
import sqlalchemy as sa

from modules.Debug import contextualize
from modules.Debug2 import logger

# revision identifiers, used by Alembic.
revision = '4d7cb48238be'
down_revision = '5861246a49f3'
branch_labels = None
depends_on = None

# Models necessary for data migration
from os import environ
from pathlib import Path
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()

class Font(Base):
    __tablename__ = 'font'

    id = sa.Column(sa.Integer, primary_key=True)
    # Existing columns for migrating
    file = sa.Column(sa.String)
    # New column
    file_name = sa.Column(sa.String, default=None)

IS_DOCKER = environ.get('TCM_IS_DOCKER', 'false').lower() == 'true'


def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.add_column(sa.Column('file_name', sa.String(), nullable=True))
        batch_op.alter_column('interword_spacing',
            existing_type=sa.INTEGER(),
            server_default=None,
            existing_nullable=False
        )

    # Perform data migration of file -> file_name
    session = Session(bind=op.get_bind())

    for font in session.query(Font):
        if font.file is None:
            continue

        font.file_name = Path(font.file).name
        print(f'Migrated Font[{font.id}].file_name = {font.file_name}')

    session.commit()

    # Drop unused file column
    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.drop_column('file')

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.add_column(sa.Column('file', sa.VARCHAR(), nullable=True))
        batch_op.alter_column('interword_spacing',
            existing_type=sa.INTEGER(),
            server_default=sa.text("'0'"),
            existing_nullable=False
        )

    # Perform data migration of file_name -> file
    session = Session(bind=op.get_bind())

    for font in session.query(Font):
        if font.file_name is None:
            continue

        font_directory = Path('./config/assets/fonts')
        if IS_DOCKER:
            font_directory = Path('/config/assets/fonts/')

        font.file = str((font_directory / str(font.id) / font.file_name).resolve())
        print(f'Unmigrated Font[{font.id}].file = {font.file}')

    session.commit()

    # Drop unused file_name column
    # Drop unused file column
    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.drop_column('file_name')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
