"""Add model_json Card sa.Column
Modify Card table:
- Create new `model_json` Column
- Remove the hide_season_text, font_file, season_number, font_kerning, blur,
grayscale, extras, font_vertical_shift, episode_text, title_text, season_text,
hide_episode_text, absolute_number, font_stroke_width, font_interline_spacing,
font_interword_spacing, episode_number, font_size, and font_color columns.
- Performs a data migration on the `model_json` Column as a JSON serialization
of the Pydantic Card model associated with the given Card object.

Revision ID: caec4f618689
Revises: 25490125daaf
Create Date: 2023-10-29 17:47:41.469202

"""
from pathlib import Path
from alembic import op
import sqlalchemy as sa

from app.dependencies import get_preferences
from modules.CleanPath import CleanPath
from modules.Debug import contextualize

# revision identifiers, used by Alembic.
revision = 'caec4f618689'
down_revision = '25490125daaf'
branch_labels = None
depends_on = None

# Models necessary for data migration
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship, Session
from app.schemas.card_type import LocalCardTypeModels

Base = declarative_base()

class Card(Base):
    __tablename__ = 'card'

    # sa.Columns not being modified
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    series_id = sa.Column(sa.Integer, sa.ForeignKey('series.id'))
    series = relationship('Series', back_populates='cards')
    # episode_id = sa.Column(sa.Integer, sa.ForeignKey('episode.id'))
    source_file = sa.Column(sa.String, nullable=False)
    card_file = sa.Column(sa.String, nullable=False)
    filesize = sa.Column(sa.Integer)
    card_type = sa.Column(sa.String, nullable=False)
    # New sa.Column for migration
    model_json = sa.Column(MutableDict.as_mutable(sa.JSON), default={}, nullable=False)
    # Old sa.Columns for migration
    title_text = sa.Column(sa.String, nullable=False)
    season_text = sa.Column(sa.String, nullable=False)
    hide_season_text = sa.Column(sa.Boolean, nullable=False)
    episode_text = sa.Column(sa.String, nullable=False)
    hide_episode_text = sa.Column(sa.Boolean, nullable=False)
    font_file = sa.Column(sa.String, nullable=False)
    font_color = sa.Column(sa.String, nullable=False)
    font_size = sa.Column(sa.Float, nullable=False)
    font_kerning = sa.Column(sa.Float, nullable=False)
    font_stroke_width = sa.Column(sa.Float, nullable=False)
    font_interline_spacing = sa.Column(sa.Integer, nullable=False)
    font_interword_spacing = sa.Column(sa.Integer, nullable=False)
    font_vertical_shift = sa.Column(sa.Integer, nullable=False)
    blur = sa.Column(sa.Boolean, nullable=False)
    grayscale = sa.Column(sa.Boolean, nullable=False)
    extras = sa.Column(MutableDict.as_mutable(sa.JSON), default={}, nullable=False)
    season_number = sa.Column(sa.Integer, default=0, nullable=False)
    episode_number = sa.Column(sa.Integer, default=0, nullable=False)
    absolute_number = sa.Column(sa.Integer, default=0)

class Series(Base):
    __tablename__ = 'series'

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    name = sa.Column(sa.String, nullable=False)
    year = sa.Column(sa.Integer, nullable=False)
    cards = relationship(Card, back_populates='series')

def get_logo_file(series: Series, source_directory: Path) -> Path:
    return Path(source_directory) \
        / CleanPath.sanitize_name(f'{series.name} ({series.year})')[:254] \
        / 'logo.png'

def upgrade() -> None:
    log = contextualize()
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    # Add new column
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.add_column(sa.Column('model_json', sa.JSON(), server_default='{}', nullable=False))

    # Perform data migration
    session = Session(bind=op.get_bind())
    preferences = get_preferences()

    # Initialize model_json for each Card
    for card in session.query(Card).all():
        if card.card_type not in LocalCardTypeModels:
            log.warning(f'Cannot initialize Card[{card.id}].model_json - deleting Card')
            session.delete(card)
            continue

        # Get logo file if not present
        if 'logo_file' in card.extras:
            logo_file = Path(card.extras.pop('logo_file'))
        else:
            logo_file = get_logo_file(card.series, preferences.source_directory)

        # Get Pydantic model for this card type, initialize
        try:
            card_model = LocalCardTypeModels[card.card_type](
                **(card.extras | card.__dict__),
                logo_file=logo_file,
            )
        except Exception as exc:
            log.warning(f'Cannot initialize Card[{card.id}].model_json - deleting Card')
            log.debug(f'Exception: {exc}')
            session.delete(card)
            continue

        # Write this model into model_json column
        # Convert any Path objects into their string equivalents
        card.model_json = {
            key: str(val)
            for key, val in
            card_model.dict(exclude_defaults=True).items()
        }

    # Commit changes
    session.commit()

    # Remove unused columns
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_column('hide_season_text')
        batch_op.drop_column('font_file')
        batch_op.drop_column('season_number')
        batch_op.drop_column('font_kerning')
        batch_op.drop_column('blur')
        batch_op.drop_column('grayscale')
        batch_op.drop_column('extras')
        batch_op.drop_column('font_vertical_shift')
        batch_op.drop_column('episode_text')
        batch_op.drop_column('title_text')
        batch_op.drop_column('season_text')
        batch_op.drop_column('hide_episode_text')
        batch_op.drop_column('absolute_number')
        batch_op.drop_column('font_stroke_width')
        batch_op.drop_column('font_interline_spacing')
        batch_op.drop_column('font_interword_spacing')
        batch_op.drop_column('episode_number')
        batch_op.drop_column('font_size')
        batch_op.drop_column('font_color')

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize()
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')
    log.error(f'Card schema is not backwards compatible')

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_column('model_json')
        batch_op.add_column(sa.Column('font_color', sa.VARCHAR(), nullable=False))
        batch_op.add_column(sa.Column('font_size', sa.FLOAT(), nullable=False))
        batch_op.add_column(sa.Column('episode_number', sa.INTEGER(), nullable=False))
        batch_op.add_column(sa.Column('font_interword_spacing', sa.INTEGER(), nullable=False))
        batch_op.add_column(sa.Column('font_interline_spacing', sa.INTEGER(), nullable=False))
        batch_op.add_column(sa.Column('font_stroke_width', sa.FLOAT(), nullable=False))
        batch_op.add_column(sa.Column('absolute_number', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('hide_episode_text', sa.BOOLEAN(), nullable=False))
        batch_op.add_column(sa.Column('season_text', sa.VARCHAR(), nullable=False))
        batch_op.add_column(sa.Column('title_text', sa.VARCHAR(), nullable=False))
        batch_op.add_column(sa.Column('episode_text', sa.VARCHAR(), nullable=False))
        batch_op.add_column(sa.Column('font_vertical_shift', sa.INTEGER(), nullable=False))
        batch_op.add_column(sa.Column('extras', sa.JSON(), nullable=False))
        batch_op.add_column(sa.Column('grayscale', sa.BOOLEAN(), nullable=False))
        batch_op.add_column(sa.Column('blur', sa.BOOLEAN(), nullable=False))
        batch_op.add_column(sa.Column('font_kerning', sa.FLOAT(), nullable=False))
        batch_op.add_column(sa.Column('season_number', sa.INTEGER(), nullable=False))
        batch_op.add_column(sa.Column('font_file', sa.VARCHAR(), nullable=False))
        batch_op.add_column(sa.Column('hide_season_text', sa.BOOLEAN(), nullable=False))

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
