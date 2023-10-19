"""Add explicit ordering to all many-to-many Template associations.

Revision ID: 25490125daaf
Revises: 4d7cb48238be
Create Date: 2023-10-13 16:32:20.795747
"""

from alembic import op
import sqlalchemy as sa

from modules.Debug import contextualize

# revision identifiers, used by Alembic.
revision = '25490125daaf'
down_revision = '4d7cb48238be'
branch_labels = None
depends_on = None

# Models necessary for data migration
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship

Base = declarative_base()

class SeriesTemplates(Base):
    __tablename__ = 'series_templates'

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    template_id = sa.Column(sa.Integer, sa.ForeignKey('template.id'))
    series_id = sa.Column(sa.Integer, sa.ForeignKey('series.id'))
    order = sa.Column(sa.Integer)

class EpisodeTemplates(Base):
    __tablename__ = 'episode_templates'

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    template_id = sa.Column(sa.Integer, sa.ForeignKey('template.id'))
    episode_id = sa.Column(sa.Integer, sa.ForeignKey('episode.id'))
    order = sa.Column(sa.Integer)

class SyncTemplates(Base):
    __tablename__ = 'sync_templates'

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    template_id = sa.Column(sa.Integer, sa.ForeignKey('template.id'))
    sync_id = sa.Column(sa.Integer, sa.ForeignKey('sync.id'))
    order = sa.Column(sa.Integer)

class Series(Base):
    __tablename__ = 'series'

    # Referencial arguments
    id = sa.Column(sa.Integer, primary_key=True)
    templates = relationship(
        'Template',
        secondary=SeriesTemplates.__table__,
        back_populates='series',
        order_by='SeriesTemplates.order',
    )

class Episode(Base):
    __tablename__ = 'episode'

    # Referencial arguments
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    templates = relationship(
        'Template',
        secondary=EpisodeTemplates.__table__,
        back_populates='episodes'
    )

class Sync(Base):
    __tablename__ = 'sync'

    # Referencial arguments
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    templates = relationship(
        'Template',
        secondary=SyncTemplates.__table__,
        back_populates='syncs'
    )

class Template(Base):
    __tablename__ = 'template'

    # Referencial arguments
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    syncs = relationship(
        'Sync',
        secondary=SyncTemplates.__table__,
        back_populates='templates'
    )
    series = relationship(
        'Series',
        secondary=SeriesTemplates.__table__,
        back_populates='templates'
    )
    episodes = relationship(
        'Episode',
        secondary=EpisodeTemplates.__table__,
        back_populates='templates'
    )



def upgrade() -> None:
    log = contextualize()
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    with op.batch_alter_table('episode_templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('order', sa.Integer(), nullable=True))

    with op.batch_alter_table('series_templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('order', sa.Integer(), nullable=True))

    with op.batch_alter_table('sync_templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('order', sa.Integer(), nullable=True))

    # Perform data migration
    session = Session(bind=op.get_bind())

    # Add order to all existing associations
    for series in session.query(Series).all():
        for index, template in enumerate(series.templates):
            association = session.query(SeriesTemplates)\
                .filter_by(template_id=template.id,
                           series_id=series.id)\
                .first()
            if association:
                association.order = index
        if series.templates:
            log.debug(f'Migrated Series[{series.id}] Template orders')
    for episode in session.query(Episode).all():
        for index, template in enumerate(episode.templates):
            association = session.query(EpisodeTemplates)\
                .filter_by(template_id=template.id,
                           episode_id=episode.id)\
                .first()
            if association:
                association.order = index
        if episode.templates:
            log.debug(f'Migrated Episode[{episode.id}] Template orders')
    for sync in session.query(Sync).all():
        for index, template in enumerate(sync.templates):
            association = session.query(SyncTemplates)\
                .filter_by(template_id=template.id,
                           sync_id=sync.id)\
                .first()
            if association:
                association.order = index
        if sync.templates:
            log.debug(f'Migrated Sync[{sync.id}] Template order')

    # Commit changes
    session.commit()

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize()
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('sync_templates', schema=None) as batch_op:
        batch_op.drop_column('order')

    with op.batch_alter_table('series_templates', schema=None) as batch_op:
        batch_op.drop_column('order')

    with op.batch_alter_table('episode_templates', schema=None) as batch_op:
        batch_op.drop_column('order')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
