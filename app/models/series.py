from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, JSON
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.dependencies import get_preferences
from app.models.template import SeriesTemplates

from modules.CleanPath import CleanPath
from modules.Debug import log
from modules.SeriesInfo import SeriesInfo

INTERNAL_ASSET_DIRECTORY = Path(__file__).parent.parent / 'assets'

class Series(Base):
    __tablename__ = 'series'

    # Referencial arguments
    id = Column(Integer, primary_key=True)
    font_id = Column(Integer, ForeignKey('font.id'))
    font = relationship('Font', back_populates='series')
    sync_id = Column(Integer, ForeignKey('sync.id'), default=None)
    sync = relationship('Sync', back_populates='series')
    cards = relationship('Card', back_populates='series')
    loaded = relationship('Loaded', back_populates='series')
    episodes = relationship('Episode', back_populates='series')
    templates = relationship(
        'Template',
        secondary=SeriesTemplates.__table__,
        back_populates='series'
    )

    # Required arguments
    name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    monitored = Column(Boolean, default=True, nullable=False)
    poster_file = Column(
        String,
        default=str(INTERNAL_ASSET_DIRECTORY/'placeholder.jpg')
    )
    poster_url = Column(String, default='/internal_assets/placeholder.jpg')

    # Series config arguments
    directory = Column(String, default=None)
    emby_library_name = Column(String, default=None)
    jellyfin_library_name = Column(String, default=None)
    plex_library_name = Column(String, default=None)
    card_filename_format = Column(String, default=None)
    episode_data_source = Column(String, default=None)
    sync_specials = Column(Boolean, default=None)
    skip_localized_images = Column(Boolean, default=None)
    translations = Column(JSON, default=None)
    match_titles = Column(Boolean, default=True, nullable=False)

    # Database arguments
    emby_id = Column(Integer, default=None)
    imdb_id = Column(String, default=None)
    jellyfin_id = Column(String, default=None)
    sonarr_id = Column(String, default=None)
    tmdb_id = Column(Integer, default=None)
    tvdb_id = Column(Integer, default=None)
    tvrage_id = Column(Integer, default=None)

    # Font arguments
    font_color = Column(String, default=None)
    font_title_case = Column(String, default=None)
    font_size = Column(Float, default=None)
    font_kerning = Column(Float, default=None)
    font_stroke_width = Column(Float, default=None)
    font_interline_spacing = Column(Integer, default=None)
    font_vertical_shift = Column(Integer, default=None)

    # Card arguments
    card_type = Column(String, default=None)
    hide_season_text = Column(Boolean, default=None)
    season_titles = Column(JSON, default=None)
    hide_episode_text = Column(Boolean, default=None)
    episode_text_format = Column(String, default=None)
    unwatched_style = Column(String, default=None)
    watched_style = Column(String, default=None)
    extras = Column(JSON, default=None)

    # Columns from relationships
    @hybrid_property
    def episode_ids(self) -> list[int]:
        return [episode.id for episode in self.episodes]

    @hybrid_property
    def template_ids(self) -> list[int]:
        return [template.id for template in self.templates]

    @hybrid_property
    def full_name(self) -> str:
        return f'{self.name} ({self.year})'
    
    @hybrid_property
    def small_poster_url(self) -> str:
        return f'/assets/{self.id}/poster-750.jpg'
    
    @hybrid_property
    def number_of_seasons(self) -> int:
        return len(set(episode.season_number for episode in self.episodes))

    @hybrid_property
    def path_safe_name(self) -> str:
        return str(CleanPath.sanitize_name(self.full_name))
    
    @hybrid_property
    def card_directory(self) -> Path:
        directory = self.path_safe_name if self.directory is None else self.directory
        return CleanPath(get_preferences().card_directory) / directory

    @hybrid_property
    def source_directory(self) -> str:
        return str(CleanPath(get_preferences().source_directory) / self.path_safe_name)

    @hybrid_property
    def log_str(self) -> str:
        return f'Series[{self.id}] "{self.full_name}"'

    @hybrid_property
    def card_properties(self) -> dict[str, Any]:
        return {
            'series_name': self.name,
            'series_full_name': self.full_name,
            'year': self.year,
            'card_filename_format': self.card_filename_format,
            'font_color': self.font_color,
            'font_title_case': self.font_title_case,
            'font_size': self.font_size,
            'font_kerning': self.font_kerning,
            'font_stroke_width': self.font_stroke_width,
            'font_interline_spacing': self.font_interline_spacing,
            'font_vertical_shift': self.font_vertical_shift,
            'directory': self.directory,
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
            # 'image_source_priority': self.image_source_priority,
            'skip_localized_images': self.skip_localized_images,
        }

    @hybrid_property
    def as_series_info(self) -> SeriesInfo:
        return SeriesInfo(
            name=self.name,
            year=self.year,
            emby_id=self.emby_id,
            imdb_id=self.imdb_id,
            jellyfin_id=self.jellyfin_id,
            sonarr_id=self.sonarr_id,
            tmdb_id=self.tmdb_id,
            tvdb_id=self.tvdb_id,
            tvrage_id=self.tvrage_id,
        )


    @hybrid_method
    def get_logo_file(self, source_base: str) -> Path:
        """
        Get the logo file for this series.

        Args:
            source_base: Base source directory.

        Returns:
            Path to the logo file that corresponds to this series' under
            the given base source directory.
        """

        return Path(source_base) / self.path_safe_name / 'logo.png'


    @hybrid_method
    def get_series_backdrop(self, source_base: str) -> Path:
        """
        Get the backdrop file for this series.

        Args:
            source_base: Base source directory.

        Returns:
            Path to the backdrop file that corresponds to this series'
            under the given base source directory.
        """

        return Path(source_base) / self.path_safe_name / 'backdrop.jpg'