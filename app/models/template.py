from datetime import datetime
from pathlib import Path
from re import match as re_match
from typing import Any, Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import relationship

from app.database.session import Base

from modules.Debug import log

"""Format of all refrence dates for before and after operations"""
DATETIME_FORMAT = '%Y-%m-%d'

OPERATIONS = {
    'is true': lambda v, r: bool(v),
    'is false': lambda v, r: not bool(v),
    'is null': lambda v, r: v is None,
    'is not null': lambda v, r: v is not None,
    'equals': lambda v, r: str(v) == str(r),
    'does not equal': lambda v, r: str(v) != str(r),
    'starts with': lambda v, r: str(v).lower().startswith(str(r).lower()),
    'does not start with': lambda v, r: not str(v).lower().startswith(str(r).lower()),
    'ends with': lambda v, r: str(v).lower().endswith(str(r).lower()),
    'does not end with': lambda v, r: not str(v).lower().endswith(str(r).lower()),
    'contains': lambda v, r: r in v,
    'matches': lambda v, r: bool(re_match(r, v)),
    'does not match': lambda v, r: not bool(re_match(r, v)),
    'is less than': lambda v, r: float(v) < float(r),
    'is less than or equal': lambda v, r: float(v) <= float(r),
    'is greater than': lambda v, r: float(v) > float(r),
    'is greater than or equal': lambda v, r: float(v) >= float(r),
    'is before': lambda v, r: v < datetime.strptime(r, DATETIME_FORMAT),
    'is after': lambda v, r: v > datetime.strptime(r, DATETIME_FORMAT),
    'file exists': lambda v, r: Path(v).exists(),
}
ARGUMENT_KEYS = (
    'Series Name', 'Series Year', 'Number of Seasons',
    'Series Library Name (Emby)', 'Series Library Name (Jellyfin)',
    'Series Library Name (Plex)', 'Series Logo', 'Episode is Watched',
    'Season Number', 'Episode Number', 'Absolute Number', 'Episode Title',
    'Episode Title Length', 'Episode Airdate',
)

# Tables for many <-> many Template relationships

class SeriesTemplates(Base):
    __tablename__ = 'series_templates'

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('template.id'))
    series_id = Column(Integer, ForeignKey('series.id'))

class EpisodeTemplates(Base):
    __tablename__ = 'episode_templates'

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('template.id'))
    episode_id = Column(Integer, ForeignKey('episode.id'))

class SyncTemplates(Base):
    __tablename__ = 'sync_templates'

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('template.id'))
    sync_id = Column(Integer, ForeignKey('sync.id'))

# Template table
class Template(Base):
    __tablename__ = 'template'

    # Referencial arguments
    id = Column(Integer, primary_key=True, index=True)
    font_id = Column(Integer, ForeignKey('font.id'))
    font = relationship('Font', back_populates='templates')
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

    name = Column(String, nullable=False)
    filters = Column(MutableList.as_mutable(JSON), default=[], nullable=False)

    card_filename_format = Column(String, default=None)
    episode_data_source = Column(String, default=None)
    sync_specials = Column(Boolean, default=None)
    skip_localized_images = Column(Boolean, default=None)
    translations = Column(MutableList.as_mutable(JSON), default=None, nullable=False)

    card_type = Column(String, default=None)
    hide_season_text = Column(Boolean, default=None)
    season_titles = Column(MutableDict.as_mutable(JSON), default={}, nullable=False)
    hide_episode_text = Column(Boolean, default=None)
    episode_text_format = Column(String, default=None)
    unwatched_style = Column(String, default=None)
    watched_style = Column(String, default=None)

    extras = Column(MutableDict.as_mutable(JSON), default={}, nullable=False)

    @hybrid_property
    def log_str(self) -> str:
        return f'Template[{self.id}] "{self.name}"'

    @hybrid_property
    def card_properties(self) -> dict[str, Any]:
        return {
            'template_id': self.id,
            'template_name': self.name,
            'card_filename_format': self.card_filename_format,
            'font_id': self.font_id,
            'card_type': self.card_type,
            'hide_season_text': self.hide_season_text,
            'season_titles': self.season_titles,
            'hide_episode_text': self.hide_episode_text,
            'episode_text_format': self.episode_text_format,
            'unwatched_style': self.unwatched_style,
            'watched_style': self.watched_style,
            'extras': self.extras,
        }

    @hybrid_property
    def image_source_properties(self) -> dict[str, bool]:
        return {
            'skip_localized_images': self.skip_localized_images,
        }
    
    
    @hybrid_method
    def meets_filter_criteria(self,
            preferences: 'Preferences',
            series: 'Series',
            episode: Optional['Episode'] = None) -> bool:
        """
        Determine whether the given Series and Episode meet this
        Template's filter criteria.
        
        Args:
            series: Series whose arguments can be evaluated.
            episode: Episode whose arguments can be evaluated.
            
        Returns:
            True if the given objects meet all of Template's filter
            conditions, or if there are no filters. False otherwise.

        """

        # This Template has no filters, return True
        if len(self.filters) == 0:
            return True

        # Arguments for this Series and Episode
        SERIES_ARGUMENTS = {
            'Series Name': series.name,
            'Series Year': series.year,
            'Number of Seasons': series.number_of_seasons,
            'Series Library Name (Emby)': series.emby_library_name,
            'Series Library Name (Jellyfin)': series.jellyfin_library_name,
            'Series Library Name (Plex)': series.plex_library_name,
            'Series Logo': series.get_logo_file(preferences.source_directory),
        }
        if episode is None:
            ARGUMENTS = SERIES_ARGUMENTS
        else:
            ARGUMENTS = SERIES_ARGUMENTS | {
                'Episode is Watched': episode.watched,
                'Season Number': episode.season_number,
                'Episode Number': episode.episode_number,
                'Absolute Number': episode.absolute_number,
                'Episode Title': episode.title,
                'Episode Title Length': len(episode.title),
                'Episode Airdate': episode.airdate,
            }

        # Evaluate each condition of this Template's filter
        for condition in self.filters:
            # If operation and argument are valid, evalute condition
            if (condition['operation'] in OPERATIONS
                and condition['argument'] in ARGUMENTS):
                # Return False if the condition evalutes to False
                try:
                    meets_condition = OPERATIONS[condition['operation']](
                        ARGUMENTS[condition['argument']],
                        condition['reference'],
                    )
                except Exception as e:
                    log.exception(f'{series.log_str} {episode.log_str} '
                                  f'Condition evaluation raised an error', e)
                    return False
                if not meets_condition:
                    log.debug(f'{self.log_str} Does not satisfy Condition: [{ARGUMENTS[condition["argument"]]}] [{condition["operation"]}] [{condition["reference"]}]')
                    return False
            else:
                log.debug(f'{self.log_str} [{condition["argument"]}] [{condition["operation"]}] [{condition["reference"]}] is unevaluatable')
                continue

        return True