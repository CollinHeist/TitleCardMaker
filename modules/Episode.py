from pathlib import Path
from typing import Optional, Union

from modules.BaseCardType import BaseCardType
from modules.CleanPath import CleanPath
from modules.Debug import log
from modules.EpisodeInfo import EpisodeInfo
from modules.StyleSet import StyleSet
from modules.TitleCard import TitleCard

class Episode:
    """
    This class defines an episode of a series that has a corresponding
    Title Card. An Episode encapsulates some EpisodeInfo, as well as
    attributes that map that info to a source and destination file.
    """

    __slots__ = (
        'episode_info', 'card_class', '_base_source', 'source', 'destination',
        'downloadable_source', 'extra_characteristics', 'given_keys', 'watched',
        'blur', 'grayscale', 'spoil_type', 
    )


    def __init__(self,
            episode_info: EpisodeInfo,
            card_class: BaseCardType,
            base_source: Path,
            destination: Path,
            given_keys: set[str],
            **extras: dict
        ) -> None:
        """
        Construct a new instance of an Episode.

        Args:
            episode_info: Episode info for this episode.
            base_source: The base source directory to look for source
                images within.
            destination: The destination for the title card associated
                with this Episode.
            given_keys: Set of keys present in the initialization of
                this Episode.
            extras: Additional characteristics to pass to the creation
                of the TitleCard from this Episode.
        """

        # Set object attributes
        self.episode_info = episode_info
        self.card_class = card_class

        # Set source/destination paths
        self._base_source = base_source
        source_name = (f's{episode_info.season_number}'
                       f'e{episode_info.episode_number}'
                       f'{TitleCard.INPUT_CARD_EXTENSION}')
        self.source = base_source / source_name
        self.destination = destination
        self.downloadable_source = True

        # Store given keys and extra characteristics
        self.given_keys = given_keys
        self.extra_characteristics = extras

        # Episodes are watched, not blurred, and spoiled - until updated
        self.watched = False
        self.blur = False
        self.grayscale = False
        self.spoil_type = StyleSet.DEFAULT_SPOIL_TYPE


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'Episode {self.episode_info}'


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object"""

        attrs = ', '.join(f'{attr}={getattr(self, attr)}'
                          for attr in self.__slots__)

        return f'<Episode {attrs}>'


    @property
    def characteristics(self) -> dict:
        """
        Get the characteristics of this object for formatting.

        Returns:
            Dictionary of characteristics that define this object. Keys
            are the start/end indices of the range, and the extra
            characteristics of the first episode.
        """

        return self.episode_info.characteristics | self.extra_characteristics


    def key_is_specified(self, key: str) -> bool:
        """
        Return whether the given key was present in the initialization
        for this Episode, i.e. whether the key can be added to the
        datafile.

        Args:
            key: The key being checked.

        Returns:
            Whether the given key was specified in the initialization of
            this Episode.
        """

        return key in self.given_keys


    def update_statuses(self, watched: bool, style_set: StyleSet) -> None:
        """
        Update the statuses of this Episode. In particular the watched
        status and un/watched styles.

        Args:
            watched: New watched status for this Episode.
            style_set: StyleSet object to assign spoil type with.
        """

        self.watched = watched
        self.spoil_type = style_set.effective_spoil_type(watched)


    def update_source(self,
            new_source: Union[Path, str, None],
            *,
            downloadable: bool,
        ) -> bool:
        """
        Update the source image for this Episode, as well as the
        downloadable flag for the source.

        Args:
            new_source: New source file. If source the path is taken
                as-is; if string, then the file is looked for within
                this Episode's base source directory - if that file DNE
                then it's taken as a Path and converted; if None,
                nothing happens.
            downloadable: (Keyword) Whether the new source is
                downloadable or not.

        Returns:
            True if a new non-None source was provided, False otherwise.
        """

        # If no actual new source was provided, return
        if new_source is None:
            return False

        # Update source path based on input (Path/str of filename in source,etc)
        if isinstance(new_source, Path):
            self.source = new_source
        elif (self._base_source / new_source).exists():
            self.source = self._base_source / new_source
        else:
            self.source = CleanPath(new_source).sanitize()

        # Set the downloadable flag for the new source
        self.downloadable_source = downloadable

        return True


    def delete_card(self, *, reason: Optional[str] = None) -> bool:
        """
        Delete the title card for this Episode.

        Args:
            reason: (Keyword) String to log why the card is being
                deleted.

        Returns:
            True if card was deleted, False otherwise.
        """

        # No destination, nothing to delete
        if self.destination is None:
            return False

        # Destination exists, delete and return True
        if self.destination.exists():
            self.destination.unlink()

            # Log deletion 
            message = f'Deleted "{self.destination.resolve()}"'
            if reason is not None:
                message += f' [{reason}]'
            log.debug(message)

            return True

        return False