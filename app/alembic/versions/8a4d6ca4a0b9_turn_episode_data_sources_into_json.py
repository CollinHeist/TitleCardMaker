"""Turn Episode data sources into JSON

Revision ID: 8a4d6ca4a0b9
Revises: 086e95b52b9d
Create Date: 2023-09-07 15:23:48.308563

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '8a4d6ca4a0b9'
down_revision = '086e95b52b9d'
branch_labels = None
depends_on = None

# Models necessary for data migration
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session

Base = declarative_base()
class Series(Base):
    __tablename__ = 'series'

    id = sa.Column(sa.Integer, primary_key=True)
    # Existing Columns for migrating
    episode_data_source = sa.Column(sa.String)
    # New column
    data_source = sa.Column(MutableDict.as_mutable(sa.JSON), default=None)

class Template(Base):
    __tablename__ = 'template'

    id = sa.Column(sa.Integer, primary_key=True)
    # Existing Columns for migrating
    episode_data_source = sa.Column(sa.String)
    # New column
    data_source = sa.Column(MutableDict.as_mutable(sa.JSON), default=None)


def upgrade() -> None:
    # Add new data_source columns
    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('data_source', sa.JSON(), nullable=True))

    with op.batch_alter_table('template', schema=None) as batch_op:
        batch_op.add_column(sa.Column('data_source', sa.JSON(), nullable=True))

    # Migrate episode_data_source -> data_source columns
    session = Session(bind=op.get_bind())

    for series in session.query(Series):
        if series.episode_data_source is not None:
            data_source = {
                'media_server': series.episode_data_source, 'interface_id': 0
            }
            series.data_source = data_source
            print(f'Initialized Series[{series.id}].data_source = {data_source}')
    for template in session.query(Template):
        if template.episode_data_source is not None:
            data_source = {
                'media_server': template.episode_data_source, 'interface_id': 0
            }
            template.data_source = data_source
            print(f'Initialized Template[{template.id}].data_source = {data_source}')

    session.commit()

    # Drop old episode_data_source columns
    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.drop_column('episode_data_source')

    with op.batch_alter_table('template', schema=None) as batch_op:
        batch_op.drop_column('episode_data_source')


def downgrade() -> None:
    # Add old columns
    with op.batch_alter_table('template', schema=None) as batch_op:
        batch_op.add_column(sa.Column('episode_data_source', sa.VARCHAR(), nullable=True))

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('episode_data_source', sa.VARCHAR(), nullable=True))

    # Reverse data migration
    session = Session(bind=op.get_bind())

    for series in session.query(Series):
        if series.data_source is not None:
            series.episode_data_source = series.data_source['media_server']
    for template in session.query(Template):
        if template.data_source is not None:
            template.episode_data_source = template.data_source['media_server']

    session.commit()

    # Remove new columns
    with op.batch_alter_table('template', schema=None) as batch_op:
        batch_op.drop_column('data_source')

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.drop_column('data_source')