"""Add Card Source File column

Revision ID: 32ef3d4633ce
Revises: 48872195483e
Create Date: 2024-01-15 00:34:08.115550

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from modules.Debug import contextualize

# revision identifiers, used by Alembic.
revision = '32ef3d4633ce'
down_revision = '48872195483e'
branch_labels = None
depends_on = None


# Models necessary for data migration
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, Session, relationship
from app.database.session import PreferencesLocal
from app.dependencies import get_preferences
from modules.CleanPath import CleanPath

Base = declarative_base()

class Card(Base):
    __tablename__ = 'card'

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    # Existing columns
    episode_id = sa.Column(sa.Integer, sa.ForeignKey('episode.id'))
    episode = relationship('Episode', back_populates='cards')
    # New Column(s)
    source_file = sa.Column(sa.String)

class Episode(Base):
    __tablename__ = 'episode'

    id = sa.Column(sa.Integer, primary_key=True)
    cards = relationship('Card', back_populates='episode')
    season_number = sa.Column(sa.Integer)
    episode_number = sa.Column(sa.Integer)


def upgrade() -> None:
    log = contextualize()
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'source_file', sa.String(), nullable=False, server_default='',
        ))

    # Perform data migration
    session = Session(bind=op.get_bind())

    # Initialize with default source_file
    for card in session.query(Card).all():
        card.source_file = f's{card.episode.season_number}e{card.episode.episode_number}.jpg'
    log.debug(f'Initialized Card.source_file with default values')
    # Commit changes
    session.commit()

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize()
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_column('source_file')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
