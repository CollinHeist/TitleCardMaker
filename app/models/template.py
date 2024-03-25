from datetime import datetime
from pathlib import Path
from re import match as re_match, sub as re_sub, IGNORECASE
from typing import Any, Callable, Literal, Optional, TypedDict, TYPE_CHECKING

from sqlalchemy import ForeignKey, JSON, func
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.schemas.connection import ServerName
from modules.Debug import log
from modules.FormatString import FormatString

if TYPE_CHECKING:
    from app.models.connection import Connection
    from app.models.episode import Episode
    from app.models.font import Font
    from app.models.preferences import Preferences
    from app.models.series import Series
    from app.models.sync import Sync


def regex_replace(pattern, replacement, string):
    """Perform a Regex replacement with the given arguments"""

    return re_sub(pattern, replacement, string, IGNORECASE)

"""Format of all refrence dates for before and after operations"""
DATETIME_FORMAT = '%Y-%m-%d'

"""
Dictionary of Operation keywords to the corresponding Operation function
"""
lower_str = lambda v: str(v).lower() # pylint: disable=unnecessary-lambda-assignment
OPERATIONS: dict[str, Callable[[Any, Any], bool]] = {
    'is true': lambda v, r: bool(v),
    'is false': lambda v, r: not bool(v),
    'is null': lambda v, r: v is None,
    'is not null': lambda v, r: v is not None,
    'equals': lambda v, r: str(v) == str(r),
    'does not equal': lambda v, r: str(v) != str(r),
    'starts with': lambda v, r: lower_str(v).startswith(lower_str(r)),
    'does not start with': lambda v, r: not lower_str(v).startswith(lower_str(r)),
    'ends with': lambda v, r: lower_str(v).endswith(lower_str(r)),
    'does not end with': lambda v, r: not lower_str(v).endswith(lower_str(r)),
    'contains': lambda v, r: r in v,
    'does not contain': lambda v, r: r not in v,
    'matches': lambda v, r: bool(re_match(r, v)),
    'does not match': lambda v, r: not bool(re_match(r, v)),
    'is less than': lambda v, r: float(v) < float(r),
    'is less than or equal': lambda v, r: float(v) <= float(r),
    'is greater than': lambda v, r: float(v) > float(r),
    'is greater than or equal': lambda v, r: float(v) >= float(r),
    'is before': lambda v, r: v < datetime.strptime(r, DATETIME_FORMAT),
    'is after': lambda v, r: v > datetime.strptime(r, DATETIME_FORMAT),
    'file exists': lambda v, r: Path(r).exists() if r is not None else Path(v).exists(),
}

"""Supported Argument keywords."""
ARGUMENT_KEYS = (
    'Series Name', 'Series Year', 'Number of Seasons', 'Series Library Names',
    'Series Logo', 'Episode Watched Status', 'Season Number', 'Episode Number',
    'Absolute Number', 'Episode Identifier', 'Episode Title',
    'Episode Title Length', 'Episode Airdate', 'Episode Extras',
    'Reference File',
)

"""
Tables for many <-> many Template relationships
"""
class SeriesTemplates(Base):
    """SQL Relationship table for Series:Template relationships"""

    __tablename__ = 'series_templates'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey('template.id'))
    series_id: Mapped[int] = mapped_column(ForeignKey('series.id'))
    order: Mapped[int]

    template: Mapped['Template'] = relationship(back_populates='_series')
    series: Mapped['Series'] = relationship(back_populates='_templates')

class EpisodeTemplates(Base):
    """SQL Relationship table for Episode:Template relationships"""

    __tablename__ = 'episode_templates'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey('template.id'))
    episode_id: Mapped[int] = mapped_column(ForeignKey('episode.id'))
    order: Mapped[int]

    template: Mapped['Template'] = relationship(back_populates='_episodes')
    episode: Mapped['Episode'] = relationship(back_populates='_templates')

class SyncTemplates(Base):
    """SQL Relationship table for Sync:Template relationships"""

    __tablename__ = 'sync_templates'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey('template.id'))
    sync_id: Mapped[int] = mapped_column(ForeignKey('sync.id'))
    order: Mapped[int]

    template: Mapped['Template'] = relationship(back_populates='_syncs')
    sync: Mapped['Sync'] = relationship(back_populates='_templates')


"""
Table for the Template SQL objects themselves.
"""
# pylint: disable=missing-class-docstring
class Filter(TypedDict):
    argument: Literal[ARGUMENT_KEYS]
    operation: Literal[tuple(OPERATIONS.keys())]
    reference: Optional[str]

class Library(TypedDict):
    interface: ServerName
    interface_id: int
    name: str
# pylint: enable=missing-class-docstring

class Template(Base):
    """
    SQL Table that defines a Template. This contains Filters, Card
    customizations, as well as relational objects to linked Episodes,
    Series, and Syncs.
    """

    __tablename__ = 'template'

    # Referencial arguments
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    data_source_id: Mapped[Optional[int]] = mapped_column(ForeignKey('connection.id'))
    font_id: Mapped[Optional[int]] = mapped_column(ForeignKey('font.id'))

    data_source: Mapped['Connection'] = relationship(back_populates='templates')
    font: Mapped['Font'] = relationship(back_populates='templates')

    _syncs: Mapped[list[SyncTemplates]] = relationship(
        SyncTemplates,
        back_populates='template',
        cascade='all, delete-orphan',
    )
    syncs: AssociationProxy[list['Sync']] = association_proxy('_syncs', 'sync')

    _series: Mapped[list[SeriesTemplates]] = relationship(
        SeriesTemplates,
        back_populates='template',
        cascade='all, delete-orphan',
    )
    series: AssociationProxy[list['Series']] = association_proxy('_series', 'series')

    _episodes: Mapped[list[EpisodeTemplates]] = relationship(
        EpisodeTemplates,
        back_populates='template',
        cascade='all, delete-orphan',
    )
    episodes: AssociationProxy[list['Episode']] = association_proxy('_episodes', 'episode')

    name: Mapped[str]
    filters: Mapped[list[Filter]] = mapped_column(
        MutableList.as_mutable(JSON),
        default=[],
    )

    card_filename_format: Mapped[Optional[str]]
    sync_specials: Mapped[Optional[bool]]
    skip_localized_images: Mapped[Optional[bool]]
    translations: Mapped[list[dict]] = mapped_column(
        MutableList.as_mutable(JSON),
        default=[],
    )

    card_type: Mapped[Optional[str]]
    hide_season_text: Mapped[Optional[bool]]
    season_titles: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default={},
    )
    hide_episode_text: Mapped[Optional[bool]]
    episode_text_format: Mapped[Optional[str]]
    unwatched_style: Mapped[Optional[str]]
    watched_style: Mapped[Optional[str]]

    extras: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default={},
    )


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return f'Template[{self.id}] "{self.name}"'


    @hybrid_property
    def sort_name(self) -> str:
        """
        The sort-friendly name of this Template.

        Returns:
            Sortable name. This is lowercase with any prefix a/an/the
            removed.
        """

        return regex_replace(r'^(a|an|the|\[\d+\])(\s)', '', self.name.lower())

    @sort_name.expression
    def sort_name(cls: 'Font'): # pylint: disable=no-self-argument
        """Class-expression of `sort_name` property."""

        return func.regex_replace(
            r'^(a|an|the|\[\d+\])(\s)', '', func.lower(cls.name)
        )


    @property
    def card_properties(self) -> dict[str, Any]:
        """Properties to utilize and merge in Title Card creation."""

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


    @property
    def export_properties(self) -> dict[str, Any]:
        """
        Properties to export in Blueprints that can be used in a
        NewTemplate model to recreate this object.
        """

        if self.season_titles is None:
            st_ranges, st_values = None, None
        else:
            st_ranges = list(self.season_titles.keys())
            st_values = list(self.season_titles.values())

        if self.extras is None:
            ex_ranges, ex_values = None, None
        else:
            ex_ranges = list(self.extras.keys())
            ex_values = list(self.extras.values())

        return {
            'name': self.name,
            'filters': self.filters,
            'card_type': self.card_type,
            'hide_season_text': self.hide_season_text,
            'season_title_ranges': st_ranges,
            'season_title_values': st_values,
            'hide_episode_text': self.hide_episode_text,
            'episode_text_format': self.episode_text_format,
            'translations': self.translations,
            'extra_keys': ex_ranges,
            'extra_values': ex_values,
            'skip_localized_images': self.skip_localized_images,
        }


    @property
    def image_source_properties(self) -> dict[str, bool]:
        """
        Properties to use in image source setting evaluations.

        Returns:
            Dictionary of properties.
        """

        return {
            'skip_localized_images': self.skip_localized_images,
        }


    def meets_filter_criteria(self,
            preferences: 'Preferences',
            series: 'Series',
            episode: Optional['Episode'] = None,
            library: Optional[Library] = None,
        ) -> bool:
        """
        Determine whether the given Series and Episode meet this
        Template's filter criteria.

        Args:
            series: Series whose arguments can be evaluated.
            episode: Episode whose arguments can be evaluated.
            library: Which library of the Series these criteria are
                being evaluated under.

        Returns:
            True if the given objects meet all of Template's filter
            conditions, or if there are no filters. False otherwise.
        """

        # This Template has no filters, return True
        if len(self.filters) == 0:
            return True

        # Arguments for this Series and Episode
        library_names = [library['name'] for library in series.libraries]
        SERIES_ARGUMENTS = {
            'Series Name': series.name,
            'Series Year': series.year,
            'Series Library Names': library_names,
            'Series Logo': series.get_logo_file(),
            'Number of Seasons': series.number_of_seasons,
            'Reference File': None,
        }
        if episode is None:
            ARGUMENTS = SERIES_ARGUMENTS
        else:
            ARGUMENTS = SERIES_ARGUMENTS | {
                'Season Number': episode.season_number,
                'Episode Number': episode.episode_number,
                'Absolute Number': episode.absolute_number,
                'Episode Identifier': f'S{episode.season_number:02}E{episode.episode_number:02}',
                'Episode Title': episode.title,
                'Episode Title Length': len(episode.title),
                'Episode Airdate': episode.airdate,
                'Episode Extras': episode.extras,
            }
            if library:
                ARGUMENTS['Episode Watched Status'] =episode.get_watched_status(
                    library['interface_id'], library['name'],
                )

        # Evaluate each condition of this Template's filter
        for condition in self.filters:
            # If operation and argument are valid, evalute condition
            operation = condition['operation']
            argument = condition['argument']
            if operation in OPERATIONS and argument in ARGUMENTS:
                # Attempt to treat reference as FormatString
                if (reference := condition['reference']) is not None:
                    try:
                        data = series.card_properties \
                            | episode.get_card_properties(library)
                        reference = FormatString(reference, data=data).result
                    except Exception:
                        pass

                # Return False if the condition evaluates to False
                try:
                    meets_condition = OPERATIONS[operation](
                        ARGUMENTS[argument],
                        reference,
                    )
                    if not meets_condition:
                        return False
                # Evaluation raised an error, log and return False
                except Exception:
                    log.exception(f'{episode} Condition evaluation raised an '
                                  f'error')
                    return False
            # Operation or Argument are invalid, log and skip
            else:
                log.trace(f'{self} [{argument}] [{operation}] '
                          f'[{condition["reference"]}] is unevaluatable')
                continue

        # All Filter criteria met
        return True
