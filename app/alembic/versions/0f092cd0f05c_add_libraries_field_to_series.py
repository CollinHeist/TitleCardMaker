"""Add libraries field to Series table

Revision ID: 0f092cd0f05c
Revises: 0233f2608d72
Create Date: 2023-08-29 13:27:38.665600
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0f092cd0f05c'
down_revision = '0233f2608d72'
branch_labels = None
depends_on = None

# Models necessary for data migration
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Session

Base = declarative_base()

class Series(Base):
    __tablename__ = 'series'

    id = sa.Column(sa.Integer, primary_key=True)
    # Existing Columns for migrating
    emby_library_name = sa.Column(sa.String)
    jellyfin_library_name = sa.Column(sa.String)
    plex_library_name = sa.Column(sa.String)
    # New column
    libraries = sa.Column(MutableList.as_mutable(sa.JSON), default=[], nullable=False)


def upgrade() -> None:
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.alter_column('font_interword_spacing',
            existing_type=sa.INTEGER(),
            server_default=None,
            nullable=False
        )

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.alter_column('interword_spacing',
            existing_type=sa.INTEGER(),
            server_default=None,
            existing_nullable=False
        )

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('libraries', sa.JSON(), nullable=False))

    # Perform data migration
    session = Session(bind=op.get_bind())

    for series in session.query(Series):
        libraries = []
        for library, server in ((series.emby_library_name, 'Emby'),
                                (series.jellyfin_library_name, 'Jellyfin'),
                                (series.plex_library_name, 'Plex')):
            if library:
                libraries.append({
                    'media_server': server, 'interface_id': 0, 'name': library
                })
        series.libraries = libraries
        if libraries:
            print(f'Initialized Series[{series.id}].libraries = {libraries}')

    session.commit()

    # Drop unused Series library columns
    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.drop_column('plex_library_name')
        batch_op.drop_column('jellyfin_library_name')
        batch_op.drop_column('emby_library_name')


def downgrade() -> None:
    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('emby_library_name', sa.VARCHAR(), nullable=True))
        batch_op.add_column(sa.Column('jellyfin_library_name', sa.VARCHAR(), nullable=True))
        batch_op.add_column(sa.Column('plex_library_name', sa.VARCHAR(), nullable=True))

    # Reverse data migration
    session = Session(bind=op.get_bind())

    for series in session.query(Series):
        for library_data in series.libraries:
            if library_data['media_server'] == 'Emby':
                series.emby_library_name = library_data['name']
            if library_data['media_server'] == 'Jellyfin':
                series.jelyfin_library_name = library_data['name']
            if library_data['media_server'] == 'Plex':
                series.plex_library_name = library_data['name']

    session.commit()

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.drop_column('libraries')

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.alter_column('interword_spacing',
            existing_type=sa.INTEGER(),
            server_default=sa.text("'0'"),
            existing_nullable=False
        )

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.alter_column('font_interword_spacing',
            existing_type=sa.INTEGER(),
            server_default=sa.text("'0'"),
            nullable=True
        )
