"""Separate Font replacements; migrate cardinal and ordinal formatting
Modify Font table
- Remove replacements column
- Create new replacements_in and replacements_out columns
Modify Series and Template tables
- Convert "old" style cardinal and ordinal specifications to new style

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

    id = sa.Column(sa.Integer, primary_key=True)
    # Old Column for migration
    replacements = sa.Column(sa.JSON)
    # New columns
    replacements_in = sa.Column(sa.JSON)
    replacements_out = sa.Column(sa.JSON)

class Series(Base):
    __tablename__ = 'series'

    id = sa.Column(sa.Integer, primary_key=True)
    episode_text_format = sa.Column(sa.String)
    season_titles = sa.Column(sa.JSON)

class Template(Base):
    __tablename__ = 'template'

    id = sa.Column(sa.Integer, primary_key=True)
    episode_text_format = sa.Column(sa.String)
    season_titles = sa.Column(sa.JSON)

_conversions = {
    '{season_number_cardinal}': '{to_cardinal(season_number)}',
    '{season_number_ordinal}': '{to_ordinal(season_number)}',
    '{season_number_cardinal_title}': '{titlecase(to_cardinal(season_number))}',
    '{season_number_ordinal_title}': '{titlecase(to_ordinal(season_number))}',
    '{episode_number_cardinal}': '{to_cardinal(episode_number)}',
    '{episode_number_ordinal}': '{to_ordinal(episode_number)}',
    '{episode_number_cardinal_title}': '{titlecase(to_cardinal(episode_number))}',
    '{episode_number_ordinal_title}': '{titlecase(to_ordinal(episode_number))}',
    '{absolute_number_cardinal}': '{to_cardinal(absolute_number)}',
    '{absolute_number_ordinal}': '{to_ordinal(absolute_number)}',
    '{absolute_number_cardinal_title}': '{titlecase(to_cardinal(absolute_number))}',
    '{absolute_number_ordinal_title}': '{titlecase(to_ordinal(absolute_number))}',
    '{absolute_episode_number_cardinal}': '{to_cardinal(absolute_episode_number)}',
    '{absolute_episode_number_ordinal}': '{to_ordinal(absolute_episode_number)}',
    '{absolute_episode_number_cardinal_title}': '{titlecase(to_cardinal(absolute_episode_number))}',
    '{absolute_episode_number_ordinal_title}': '{titlecase(to_ordinal(absolute_episode_number))}',
}


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

    # Modify Series+Template cardinal and ordinal values
    for obj in session.query(Series).all() + session.query(Template).all():
        if isinstance((_old := obj.episode_text_format), str):
            for rin, rout in _conversions.items():
                obj.episode_text_format = obj.episode_text_format.replace(
                    rin, rout,
                )
            if _old != obj.episode_text_format:
                log.debug(f'Migrated {obj.__tablename__}[{obj.id}]'
                          f'.episode_text_format = {obj.episode_text_format}')
        if isinstance(obj.season_titles, dict):
            for k, v in obj.season_titles.items():
                for rin, rout in _conversions.items():
                    obj.season_titles[k] = obj.season_titles[k].replace(rin, rout)
                if v != obj.season_titles[k]:
                    log.debug(f'Migrated {obj.__tablename__}[{obj.id}]'
                              f'.season_titles = {obj.season_titles}')

    # Commit changes
    session.commit()

    # Delete old column
    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.drop_column('replacements')

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'replacements', sqlite.JSON(), nullable=True
        ))

    # Perform data un-migration
    session = Session(bind=op.get_bind())

    for font in session.query(Font).all():
        font.replacements = dict(zip(font.replacements_in, font.replacements_out))
        if font.replacements:
            log.debug(f'Un-migrated Font[{font.id}].replacements = {font.replacements}')

    # Commit changes
    session.commit()

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.drop_column('replacements_out')
        batch_op.drop_column('replacements_in')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
