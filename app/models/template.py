from typing import Any

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy import PickleType

from app.database.session import Base

CONDITIONS = {
    'is true': lambda v, r: bool(v),
    'is false': lambda v, r: not bool(v),
    'is null': lambda v, r: v is None,
    'equals': lambda v, r: v == r,
    'does not equal': lambda v, r: v != r,
    'starts with': lambda v, r: str(v).startswith(str(r)),
    'ends with': lambda v, r: str(v).endswith(str(r)),
    'is less than': lambda v, r: v < r,
    'is less than or equal': lambda v, r: v <= r,
    'is greater than': lambda v, r: v > r,
    'is greater than or equal': lambda v, r: v >= r,
    'is before': lambda v, r: v < r,
    'is after': lambda v, r: v > r,
}

class Template(Base):
    __tablename__ = 'template'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    card_filename_format = Column(String, default=None)
    episode_data_source = Column(String, default=None)
    sync_specials = Column(Boolean, default=None)
    skip_localized_images = Column(Boolean, default=None)
    translations = Column(MutableList.as_mutable(PickleType), default=[], nullable=False)

    font_id = Column(Integer, ForeignKey('font.id'))
    card_type = Column(String, default=None)
    hide_season_text = Column(Boolean, default=None)
    season_titles = Column(MutableDict.as_mutable(PickleType), default={}, nullable=False)
    hide_episode_text = Column(Boolean, default=None)
    episode_text_format = Column(String, default=None)
    unwatched_style = Column(String, default=None)
    watched_style = Column(String, default=None)
    extras = Column(MutableDict.as_mutable(PickleType), default={}, nullable=False)

    @hybrid_property
    def log_str(self) -> str:
        return f'Template[{self.id}] {self.name}'

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
    def image_source_properties(self) -> dict[str, Any]:
        return {
            'skip_localized_images': self.skip_localized_images,
        }
    
    @hybrid_method
    def meets_filter_critera(self, series: 'Series', episode: 'Episode') -> bool:
        """
        Determine whether the given Series and Episode meet this Template's filter
        criteria.
        
        Args:
            series: Series whose arguments can be evaluated.
            episode: Episode whose arguments can be evaluated.
            
        Returns:
            True if the given objects meet this Template's critera, or if there are
            no filters. False otherwise.
        """
        
        if len(self.filters) == 0:
            return True
        
        ARGUMENTS = {
            'series_name': series.name,
            'series_year': series.year,
            'is_watched': episode.watched,
            'season_number': episode.season_number,
            'episode_number': episode.episode_number,
            'absolute_number': episode.absolute_number,
            'episode_title': episode.title,
            'episode_title_length': len(episode.title),
            'episode_airdate': episode.airdate,
        }
        
        return all(
            OPERATIONS[operator](ARGUMENTS[argument], reference)
            for argument, operator, reference in self.filters
            if (operator in OPERATIONS and argument in ARGUMENTS)
        )
