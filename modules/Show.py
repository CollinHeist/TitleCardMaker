from copy import copy
from pathlib import Path
from typing import Literal, Optional

from tqdm import tqdm

from modules.CleanPath import CleanPath
from modules.DataFileInterface import DataFileInterface
from modules.Debug import log, TQDM_KWARGS
from modules.EmbyInterface import EmbyInterface
from modules.Episode import Episode
from modules.EpisodeInfo import EpisodeInfo
from modules.EpisodeMap import EpisodeMap
from modules.Font import Font
import modules.global_objects as global_objects
from modules.JellyfinInterface import JellyfinInterface
from modules.MultiEpisode import MultiEpisode
from modules.PlexInterface import PlexInterface
from modules.Profile import Profile
from modules.SeasonPosterSet import SeasonPosterSet
from modules.SeriesInfo import SeriesInfo
from modules.SonarrInterface import SonarrInterface
from modules.StyleSet import StyleSet
from modules.TitleCard import TitleCard
from modules.Title import Title
from modules.TMDbInterface import TMDbInterface
from modules.WebInterface import WebInterface
from modules.YamlReader import YamlReader

MediaServer = Literal['emby', 'jellyfin', 'plex']

class Show(YamlReader):
    """
    This class describes a show. A Show encapsulates the names and
    preferences with a complete series of episodes. Each object inherits
    many preferences  from the global `PreferenceParser` object, but
    manually specified attributes within the Show's YAML take priority
    over the global values.
    """

    """Filename to the backdrop for a series"""
    BACKDROP_FILENAME = 'backdrop.jpg'

    __slots__ = (
        'preferences', 'info_set', 'series_info', 'card_filename_format',
        'card_class', 'episode_text_format', 'library_name', 'library',
        'media_directory', 'archive', 'archive_name', 'archive_all_variations',
        'episode_data_source', 'refresh_titles', 'sonarr_sync', 'sync_specials',
        'tmdb_sync', 'tmdb_skip_localized_images', 'style_set', 'hide_seasons',
        'title_languages', 'extras', '__episode_map', 'font','source_directory',
        'logo', 'backdrop', 'file_interface', 'profile', 'season_poster_set',
        'episodes', 'emby_interface', 'jellyfin_interface', 'plex_interface',
        'sonarr_interface', 'tmdb_interface', '__is_archive', 'media_server',
        'image_source_priority',
    )

    def __init__(self,
            name: str,
            yaml_dict: dict,
            source_directory: Path,
            preferences: 'PreferenceParser', # type: ignore
        ) -> None:
        """
        Constructs a new instance of a Show object from the given YAML
        dictionary, library map, and referencing the base source
        directory. If the initialization fails to produce a 'valid' show
        object, the valid attribute is set to False.

        Args:
            name: The name/title of the series.
            yaml_dict: YAML dictionary of the associated series as found
                in the series YAML file.
            source_directory: Base source directory this show should
                search for and place source images in.
            preferences: PreferenceParser object this object's default
                attributes are derived from.
        """

        # Initialize parent YamlReader object
        super().__init__(yaml_dict, log_function=log.error)

        # Get global objects
        self.preferences = preferences
        self.info_set = global_objects.info_set

        # Set this show's SeriesInfo object with blank year to start
        self.series_info = SeriesInfo(name, 0)
        try:
            self.series_info = self.info_set.get_series_info(
                self._get('name', type_=str, default=name),
                self._get('year', type_=int)
            )
        except Exception as e:
            log.exception(f'Series "{name}" is missing the required "year"', e)
            self.valid = False
            return None

        # Setup default values that may be overwritten by YAML
        self.card_filename_format = preferences.card_filename_format
        self.card_class = preferences.card_class
        self.episode_text_format = self.card_class.EPISODE_TEXT_FORMAT
        self.library_name = None
        self.library = None
        self.media_directory = None
        self.media_server: MediaServer = preferences.default_media_server
        self.image_source_priority = preferences.image_source_priority
        self.archive = preferences.create_archive
        self.archive_name = None
        self.archive_all_variations = preferences.archive_all_variations
        self.episode_data_source = preferences.episode_data_source
        self.refresh_titles = True
        self.sonarr_sync = preferences.use_sonarr
        self.sync_specials = preferences.sync_specials
        self.tmdb_sync = preferences.use_tmdb
        self.tmdb_skip_localized_images = preferences.tmdb_skip_localized_images
        self.hide_seasons = False
        self.title_languages = {}
        self.extras = {}
        if self.media_server == 'emby':
            self.style_set = copy(preferences.emby_style_set)
        elif self.media_server == 'jellyfin':
            self.style_set = copy(preferences.jellyfin_style_set)
        elif self.media_server == 'plex':
            self.style_set = copy(preferences.plex_style_set)
        else:
            self.style_set = StyleSet()
        self.__parse_yaml()

        # Update StyleSet
        if self._is_specified('watched_style'):
            self.style_set.update_watched_style(
                self._get('watched_style', type_=str)
            )
        if self._is_specified('unwatched_style'):
            self.style_set.update_unwatched_style(
                self._get('unwatched_style', type_=str)
            )
        self.valid &= self.style_set.valid

        # Construct EpisodeMap on seasons/episode ranges specification
        self.__episode_map = EpisodeMap(
            self._get('seasons', type_=dict),
            self._get('episode_ranges', type_=dict)
        )
        self.valid &= self.__episode_map.valid

        # Create Font object, update validity
        self.font = Font(
            self._base_yaml.get('font', {}), self.card_class, self.series_info,
        )
        self.valid &= self.font.valid

        # Update derived (and not adjustable) attributes
        self.source_directory =source_directory/self.series_info.full_clean_name
        self.logo = self.source_directory / 'logo.png'
        self.backdrop = self.source_directory / self.BACKDROP_FILENAME

        # Create DataFileInterface for this show
        self.file_interface = DataFileInterface(
            self.series_info,
            self.source_directory / DataFileInterface.GENERIC_DATA_FILE_NAME
        )

        # Create the profile
        self.profile = Profile(
            self.series_info,
            self.font,
            self.hide_seasons,
            self.__episode_map,
            self.episode_text_format,
        )

        # Create the SeasonPosterSet
        self.season_poster_set = SeasonPosterSet(
            self.__episode_map,
            self.source_directory,
            self.media_directory,
            self._get('season_posters'),
        )

        # Attributes to be filled/modified later
        self.episodes: dict[str, Episode] = {}
        self.emby_interface = None
        self.jellyfin_interface = None
        self.plex_interface = None
        self.sonarr_interface = None
        self.tmdb_interface = None
        self.__is_archive = False


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'"{self.series_info.full_name}"'


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object"""

        return f'<Show "{self.series_info}" with {len(self.episodes)} Episodes>'


    def _make_archive(self, media_directory: Path) -> 'Show':
        """
        Recreate this Show object as an archive.

        Args:
            media_directory: Media directory the returned Show object
                will utilize.

        Returns:
            A newly constructed Show object with a modified
            'media_directory' and 'watched_style' attributes.
        """

        # Modify base yaml to have overritten media_directory
        modified_base = copy(self._base_yaml)
        modified_base['media_directory'] = str(media_directory.resolve())

        # Set watched_style to archive style (if set)
        if (value := self._get('archive_style', type_=str)) is not None:
            modified_base['watched_style'] = value

        # Recreate Show object with modified YAML
        show = Show(
            self.series_info.full_name, modified_base,
            self.source_directory.parent,
            self.preferences
        )
        show.__is_archive = True

        return show


    def __parse_yaml(self):
        """
        Parse the Show's YAML and update this object's attributes. Error
        on any invalid attributes.
        """

        if (value := self._get('library', type_=dict)) is not None:
            self.library_name = value['name']
            self.library = value['path']
            self.media_directory = self.library/self.series_info.full_clean_name
            self.media_server = value['media_server']

        if (value := self._get('media_directory', type_=str)) is not None:
            self.media_directory = CleanPath(value).sanitize()

        if (value := self._get('filename_format', type_=str)) is not None:
            if TitleCard.validate_card_format_string(value):
                self.card_filename_format = value
            else:
                self.valid = False

        if (value := self._get('emby_id', type_=int)) is not None:
            emby_id = value if '-' in str(value) else f'0-{value}'
            self.info_set.set_emby_id(self.series_info, emby_id)

        if (value := self._get('imdb_id', type_=str)) is not None:
            self.info_set.set_imdb_id(self.series_info, value)

        if (value := self._get('jellyfin_id', type_=str)) is not None:
            self.info_set.set_jellyfin_id(self.series_info, value)

        if (value := self._get('sonarr_id', type_=int)) is not None:
            sonarr_id = value if '-' in str(value) else f'0-{value}'
            self.info_set.set_sonarr_id(self.series_info, sonarr_id)

        if (value := self._get('tmdb_id', type_=int)) is not None:
            self.info_set.set_tmdb_id(self.series_info, value)

        if (value := self._get('tvdb_id', type_=int)) is not None:
            self.info_set.set_tvdb_id(self.series_info, value)
        
        if (value := self._get('tvrage_id', type_=int)) is not None:
            self.info_set.set_tvrage_id(self.series_info, value)

        if (value := self._get('card_type', type_=str)) is not None:
            self._parse_card_type(value)
            self.episode_text_format = self.card_class.EPISODE_TEXT_FORMAT

        if (value := self._get('episode_text_format', type_=str)) is not None:
            self.episode_text_format = value

        if (value := self._get('archive', type_=bool)) is not None:
            self.archive = value

        if (value :=self._get('archive_all_variations',type_=bool)) is not None:
            self.archive_all_variations = value

        if (value := self._get('archive_name', type_=str)) is not None:
            self.archive_name = value
            self.archive_all_variations = False

        if (value := self._get('episode_data_source',
                               type_=self.TYPE_LOWER_STR)) is not None:
            if value in self.preferences.VALID_EPISODE_DATA_SOURCES:
                self.episode_data_source = value
            else:
                log.error(f'Invalid episode data source "{value}" in series '
                          f'{self}')
                self.valid = False

        if (value := self._get('image_source_priority',
                               type_=self.TYPE_LOWER_STR)) is not None:
            if (sources := self.preferences.parse_image_source_priority(value)):
                self.image_source_priority = sources
            else:
                log.error(f'Image source priority "{value}" is invalid')
                self.valid = False

        if (value := self._get('refresh_titles', type_=bool)) is not None:
            self.refresh_titles = value
            self.series_info.match_titles = value

        if (value := self._get('sonarr_sync', type_=bool)) is not None:
            self.sonarr_sync = value

        if (value := self._get('sync_specials', type_=bool)) is not None:
            self.sync_specials = value

        if (value := self._get('tmdb_sync', type_=bool)) is not None:
            self.tmdb_sync = value

        if (value := self._get('tmdb_skip_localized_images',
                               type_=bool)) is not None:
            self.tmdb_skip_localized_images = value

        if (value := self._get('seasons', 'hide', type_=bool)) is not None:
            self.hide_seasons = value

        if (value := self._get('translation')) is not None:
            # Single translation
            if isinstance(value, dict) and value.keys() == {'language', 'key'}:
                self.title_languages = [value]
            # List of translations
            elif isinstance(value, list):
                if all(isinstance(t, dict) and t.keys() == {'language', 'key'}
                       for t in value):
                    self.title_languages = value
                else:
                    log.error(f'Invalid language translations in series {self}')
            else:
                log.error(f'Invalid language translations in series {self}')

        # Read all extras
        if self._is_specified('extras'):
            self.extras = self._get('extras', type_=dict)


    def assign_interfaces(self,
            emby_interface: Optional[EmbyInterface] = None,
            jellyfin_interface: Optional[JellyfinInterface] = None,
            plex_interface: Optional[PlexInterface] = None,
            sonarr_interfaces: list[SonarrInterface] = [],
            tmdb_interface: Optional[TMDbInterface] = None) -> None:
        """
        Assign the given interfaces to attributes of this object for
        later use.

        Args:
            emby_interface: Optional EmbyInterface to store if required
                by this show.
            jellyfin_interface: Optional JellyfinInterface to store if
                required by this show.
            plex_interface: Optional PlexInterface to store if required
                by this show.
            sonarr_interface: Any number of optional SonarrInterfaces to
                store if required. Only the interface containing this
                series will be stored.
            tmdb_interface: Optional TMDbInterface to store if required
                by this show.
        """

        # If Emby is required, and an interface was provided, assign
        if (self.media_server == 'emby' and self.library is not None
            and emby_interface is not None):
            self.emby_interface = emby_interface

        # If Jellyfin is required, and an interface was provided, assign
        if (self.media_server == 'jellyfin' and self.library is not None
            and jellyfin_interface is not None):
            self.jellyfin_interface = jellyfin_interface

        # If Plex is required, and an interface was provided, assign
        if (self.media_server == 'plex' and self.library is not None
            and plex_interface is not None):
            self.plex_interface = plex_interface

        # If Sonarr is enabled, and any interfaces are provided, assign
        if self.sonarr_sync and len(sonarr_interfaces) > 0:
            # Only one interface, assign immediately
            if len(sonarr_interfaces) == 1:
                self.sonarr_interface = sonarr_interfaces[0]
            # Multiple interfaces, interface ID was manually specified
            elif (index := self._get('sonarr_server_id',type_=int)) is not None:
                if index > len(sonarr_interfaces)-1:
                    log.error(f'No Sonarr server associated with ID {index}')
                    self.valid = False
                else:
                    self.sonarr_interface = sonarr_interfaces[index]
            # Multiple interfaces, associated interface must be determined
            else:
                for interface in sonarr_interfaces:
                    if interface.has_series(self.series_info):
                        self.sonarr_interface = interface
                        break

            # If no interface determined, error
            if self.sonarr_interface is None:
                log.warning(f'Cannot find {self} on any Sonarr servers')

        # If TMDb is required, and an interface was provided, assign
        if self.tmdb_sync and tmdb_interface is not None:
            self.tmdb_interface = tmdb_interface


    def set_series_ids(self) -> None:
        """Set the series ID's for this show."""

        # Temporary function to set series ID's
        def set_emby():
            if self.emby_interface:
                self.emby_interface.set_series_ids(
                    self.library_name, self.series_info
                )
        def set_jellyfin():
            if self.jellyfin_interface:
                self.jellyfin_interface.set_series_ids(
                    self.library_name, self.series_info
                )
        def set_plex():
            if self.plex_interface:
                self.plex_interface.set_series_ids(
                    self.library_name, self.series_info
                )
        def set_sonarr():
            if self.sonarr_interface:
                self.sonarr_interface.set_series_ids(self.series_info)
        def set_tmdb():
            if self.tmdb_interface:
                self.tmdb_interface.set_series_ids(self.series_info)

        # Identify interface order for ID gathering based on primary episode
        # data source
        interface_orders = {
            'emby':     [set_emby, set_sonarr, set_tmdb, set_plex, set_jellyfin],
            'jellyfin': [set_jellyfin, set_sonarr, set_tmdb, set_plex, set_emby],
            'sonarr':   [set_sonarr, set_plex, set_emby, set_jellyfin, set_tmdb],
            'plex':     [set_plex, set_sonarr, set_tmdb, set_emby, set_jellyfin],
            'tmdb':     [set_tmdb, set_sonarr, set_plex, set_emby, set_jellyfin],
        }

        # Go through each interface and load ID's from it
        for interface_function in interface_orders[self.episode_data_source]:
            interface_function()


    def __get_destination(self, episode_info: EpisodeInfo) -> Optional[Path]:
        """
        Get the destination filename for the given entry of a datafile.

        Args:
            episode_info: EpisodeInfo for this episode.

        Returns:
            Path for the full title card destination, and None if this
            show has no media directory.
        """

        # If this entry should not be written to a media directory, return 
        if not self.media_directory:
            return None

        return TitleCard.get_output_filename(
            self.card_filename_format,
            self.series_info,
            episode_info,
            self.media_directory
        )


    def read_source(self) -> None:
        """
        Read the source file for this show, adding the associated
        Episode objects to this show's episodes dictionary.
        """

        # Reset episodes dictionary
        self.episodes = {}

        # Go through each entry in the file interface
        for entry, given_keys in self.file_interface.read():
            # Create Episode object for this entry, store under key
            self.episodes[entry['episode_info'].key] = Episode(
                base_source=self.source_directory,
                destination=self.__get_destination(entry['episode_info']),
                card_class=self.card_class,
                given_keys=given_keys,
                **entry,
            )


    def add_new_episodes(self) -> None:
        """
        Query the provided interfaces, checking for any new episodes
        exist in that interface. All new entries are added to this
        object's datafile, and an Episode object is created.
        """

        # Get episodes from indicated data source
        if self.episode_data_source == 'emby' and self.emby_interface:
            all_episodes =self.emby_interface.get_all_episodes(self.series_info)
        elif self.episode_data_source == 'jellyfin' and self.jellyfin_interface:
            all_episodes = self.jellyfin_interface.get_all_episodes(
                self.series_info
            )
        elif self.episode_data_source == 'plex' and self.plex_interface:
            all_episodes = self.plex_interface.get_all_episodes(
                self.library_name, self.series_info
            )
        elif self.episode_data_source == 'sonarr' and self.sonarr_interface:
            all_episodes = self.sonarr_interface.get_all_episodes(
                self.series_info
            )
        elif self.episode_data_source == 'tmdb' and self.tmdb_interface:
            all_episodes =self.tmdb_interface.get_all_episodes(self.series_info)
        else:
            log.warning(f'Cannot source episodes for {self} from '
                        f'{self.episode_data_source}')
            return None

        # No episodes found by data source
        if not all_episodes:
            log.info(f'{self.episode_data_source} has no episodes for {self}')
            return None

        # Inner function to filter episodes
        def include_episode(episode: Episode) -> bool:
            # Exclude if special and not syncing specials
            if not self.sync_specials and episode.season_number == 0:
                return False

            # If episode is not new, include if title needs refreshed
            if (existing_ep := self.episodes.get(episode.key)) is not None:
                if (self.refresh_titles and not
                    existing_ep.episode_info.title.matches(episode.title)):
                    existing_ep.delete_card(reason='updating title')
                    return True
                return False

            return True

        # Apply filter formula to list of Episodes from data source
        new_episodes = tuple(filter(include_episode, all_episodes))
        if len(new_episodes) == 0:
            return None

        # If any new episodes remain, add to datafile and create Episode object
        self.file_interface.add_many_entries(new_episodes)
        self.read_source()


    def set_episode_ids(self) -> None:
        """
        Set episode ID's for all Episodes within this Show, using the
        given interfaces. Only episodes whose card is not present or
        still need translations are updated.
        """

        # Exit if primary data source doesn't have an interface
        if not getattr(self, f'{self.episode_data_source}_interface'):
            return None

        # Filter episodes needing ID's - i.e. missing card or translation
        def episode_needs_id(episode) -> bool:
            # Episodes with all ID's or no card do not need ID's
            if episode.episode_info.has_all_ids or episode.destination is None:
                return False
            # Emby and Jellyfin require per-Episode ID's to match content
            if self.media_server in ('emby', 'jellyfin'):
                return True
            # Missing card, requires ID's for potential matching
            if not episode.destination.exists():
                return True
            # Missing translations, requires ID's for potential matching
            for translation in self.title_languages:
                if not episode.key_is_specified(translation['key']):
                    return True
            # All content is present, not Emby/Jellyfin, no ID's required
            return False

        # Apply filter of only those needing ID's, get only EpisodeInfo objects
        infos = list(
            ep.episode_info for ep in 
            filter(episode_needs_id, self.episodes.values())
        )

        # If no episodes need ID's, exit
        if not infos:
            return None

        # Temporary function to set episode ID's
        def set_ids(interface, episode_infos):
            interface_obj = getattr(self, f'{interface}_interface', None)
            if interface_obj is not None:
                interface_obj.set_episode_ids(
                    library_name=self.library_name,
                    series_info=self.series_info,
                    episode_infos=episode_infos,
                )

        # Identify interface order for ID gathering based on primary episode
        # data source
        interface_orders = {
            'emby':     ['emby', 'sonarr', 'tmdb'],
            'jellyfin': ['jellyfin', 'sonarr', 'tmdb'],
            'sonarr':   ['sonarr', 'plex', 'emby', 'jellyfin', 'tmdb'],
            'plex':     ['plex', 'sonarr', 'tmdb'],
            'tmdb':     ['tmdb', 'sonarr', 'plex', 'emby', 'jellyfin'],
        }

        # Go through each interface and load ID's from it
        for interface in interface_orders[self.episode_data_source]:
            set_ids(interface, infos)

        return None


    def add_translations(self) -> None:
        """
        Add translated episode titles to the Episodes of this series.
        This  show's source file is re-read if any translations are
        added.
        """

        # If no translations were specified, or TMDb syncing isn't enabled, skip
        if not self.tmdb_interface or len(self.title_languages) == 0:
            return None

        # Go through every episode and look for translations
        modified = False
        for episode in (pbar := tqdm(self.episodes.values(), **TQDM_KWARGS)):
            # Get each translation for this series
            for translation in self.title_languages:
                # If the key already exists, skip this episode
                if episode.key_is_specified(translation['key']):
                    continue

                # Update progress bar
                pbar.set_description(f'Checking {episode}')

                # Query TMDb for the title of this episode in this language
                language_title = self.tmdb_interface.get_episode_title(
                    self.series_info,
                    episode.episode_info,
                    translation['language'],
                )

                # If episode wasn't found, or original title was returned, skip
                if (language_title is None
                    or language_title == episode.episode_info.title.full_title):
                    continue

                # Modify data file entry with new title
                modified = True
                self.file_interface.add_data_to_entry(
                    episode.episode_info,
                    **{translation['key']: language_title},
                )

                # Adding translated title, log it
                log.debug(f'Added "{language_title}" to '
                          f'"{translation["key"]}" for {self} {episode}')

                # Delete old card
                episode.delete_card(reason='adding translation')

        # If any translations were added, re-read source
        if modified:
            self.read_source()


    def download_logo(self) -> None:
        """
        Download the logo for this series from TMDb. Any SVG logos are
        converted to PNG.
        """

        # If not syncing to TMDb, or logo already exists, exit
        if not self.tmdb_interface or self.logo.exists():
            return None

        # Download logo
        if (url := self.tmdb_interface.get_series_logo(self.series_info)):
            # SVG logos need to be converted first
            if url.endswith('.svg'):
                # Download .svgs to temporary location pre-conversion
                success = self.tmdb_interface.download_image(
                    url, self.card_class.TEMPORARY_SVG_FILE
                )

                # If failed to download, skip
                if not success:
                    return None

                # Convert temporary SVG to PNG at logo filepath
                logo = self.card_class.convert_svg_to_png(
                    self.card_class.TEMPORARY_SVG_FILE, self.logo,
                )
                if logo is None:
                    log.warning(f'SVG to PNG conversion failed for {self}')
                else:
                    log.debug(f'Converted logo for {self} from .svg to .png')
            else:
                self.tmdb_interface.download_image(url, self.logo)

            # Log to user
            if self.logo.exists():
                log.debug(f'Downloaded logo for {self}')


    def __apply_styles(self, select_only: Optional[Episode] = None) -> bool:
        """
        Modify this series' Episode source images based on their watch
        statuses, and how that style applies to this show's un/watched
        styles.

        Args:
            select_only: Optional Episode object. If provided, only this
                episode's style is applied.

        Returns:
            Whether a backdrop should be downloaded or not.
        """

        # Get appropiate MediaServer interface
        media_interface = {
            None: None,
            'emby': self.emby_interface,
            'jellyfin': self.jellyfin_interface,
            'plex': self.plex_interface
        }[self.media_server]

        # If this is an archive, assume all episodes are watched
        if self.__is_archive:
            [episode.update_statuses(True, self.style_set)
             for _, episode in self.episodes.items()]
        # If no MediaServer interface, assume all episodes are unwatched
        elif media_interface is None:
            [episode.update_statuses(False, self.style_set)
             for _, episode in self.episodes.items()]
        # Update watch statuses from Plex
        else:
            episode_map = self.episodes
            if select_only:
                episode_map = {select_only.episode_info.key: select_only}

            media_interface.update_watched_statuses(
                self.library_name, self.series_info, episode_map, self.style_set
            )

        # Go through all episodes and select source images
        download_backdrop = False
        for episode in self.episodes.values():
            # If only selecting a specific episode, skip others
            if select_only is not None and episode is not select_only:
                continue

            # Get the manually specified source from the episode map
            manual_source = self.__episode_map.get_source(episode.episode_info)
            applies_to = self.__episode_map.get_applies_to(episode.episode_info)

            # Default source if the effective style is art
            if self.style_set.effective_style_is_art(episode.watched):
                download_backdrop = True
                episode.update_source(self.backdrop, downloadable=False)

            # Override source if applies to all, or unwatched if ep is unwatched
            if (applies_to == 'all' or 
                (applies_to == 'unwatched' and not episode.watched)):
                episode.update_source(manual_source, downloadable=False)

            # Apply styles if indicated
            if self.style_set.effective_style_is_blur(episode.watched):
                episode.blur = True
            if self.style_set.effective_style_is_grayscale(episode.watched):
                episode.grayscale = True

        return download_backdrop


    def select_source_images(self,
            select_only: Optional[Episode] = None) -> None:
        """
        Modify this series' Episode source images based on their watch
        statuses, and how that style applies to this show's un/watched
        styles. If a backdrop is required, and TMDb is enabled, then one
        is downloaded if it does not exist.

        Args:
            select_only: Optional Episode object. If provided, only this
                episode's source is selected.
        """

        # Modify Episodes watched/blur/source files based on plex status
        download_backdrop = self.__apply_styles(select_only=select_only)

        # Don't download sources if this card type doesn't use unique images
        if not self.card_class.USES_UNIQUE_SOURCES:
            return None

        # Query TMDb for the backdrop if one does not exist and is needed
        if (download_backdrop and self.tmdb_interface
            and not self.backdrop.exists()):
            url = self.tmdb_interface.get_series_backdrop(
                self.series_info,
                skip_localized_images=self.tmdb_skip_localized_images
            )
            if url:
                self.tmdb_interface.download_image(url, self.backdrop)
                log.debug(f'Downloaded backdrop for {self} from tmdb')

        # Whether to always check each interface
        always_check_emby = (
            bool(self.emby_interface)
            and ('emby' in self.image_source_priority)
            and self.emby_interface.has_series(self.series_info))
        always_check_jellyfin = (
            bool(self.jellyfin_interface)
            and ('jellyfin' in self.image_source_priority)
            and self.jellyfin_interface.has_series(self.series_info))
        always_check_tmdb = (
            bool(self.tmdb_interface)
            and ('tmdb' in self.image_source_priority))
        always_check_plex = (
            bool(self.plex_interface)
            and ('plex' in self.image_source_priority) 
            and self.plex_interface.has_series(self.library_name,
                                               self.series_info))

        # For each episode, query interfaces (in priority order) for source
        for episode in (pbar := tqdm(self.episodes.values(), **TQDM_KWARGS)):
            # If only selecting a specific episode, skip others
            if select_only is not None and episode is not select_only:
                continue

            # Skip this episode if not downloadable, or source exists
            if not episode.downloadable_source or episode.source.exists():
                continue

            # Update progress bar
            pbar.set_description(f'Selecting {episode}')

            # Whether to check this interface for this episode
            check_emby = always_check_emby
            check_jellyfin = always_check_jellyfin
            check_plex = always_check_plex
            check_tmdb = (
                always_check_tmdb and not
                self.tmdb_interface.is_permanently_blacklisted(
                    self.series_info, episode.episode_info
                )
            )
            
            # Go through each source interface indicated, try and get source
            for source_interface in self.image_source_priority:
                image = None
                if source_interface == 'emby' and check_emby:
                    image = self.emby_interface.get_source_image(
                        episode.episode_info
                    )
                elif source_interface == 'jellyfin' and check_jellyfin:
                    image = self.jellyfin_interface.get_source_image(
                        episode.episode_info
                    )
                elif source_interface == 'plex' and check_plex:
                    image = self.plex_interface.get_source_image(
                        self.library_name,
                        self.series_info,
                        episode.episode_info,
                    )
                elif source_interface == 'tmdb' and check_tmdb:
                    image = self.tmdb_interface.get_source_image(
                        self.series_info,
                        episode.episode_info,
                        skip_localized_images=self.tmdb_skip_localized_images,
                    )
                    # Exit loop or continue depending on permanent blacklist status
                    if not image:
                        pb = self.tmdb_interface.is_permanently_blacklisted(
                            self.series_info, episode.episode_info
                        )
                        if pb: continue
                        else:  break

                # Attempt to download image, log and exit if successful
                if image and WebInterface.download_image(image, episode.source):
                    log.debug(f'Downloaded {episode.source.name} for {self} '
                              f'from {source_interface}')
                    break
            
        return None


    def find_multipart_episodes(self) -> None:
        """
        Find and create all the multipart episodes for this series. This
        adds MultiEpisode objects to this Show's episodes dictionary.
        """

        # Go through each episode to check if it can be made into a MultiEpisode
        matched = set()
        multiparts = []
        for episode in self.episodes.values():
            # If this episode has already been used in MultiEpisode, skip
            if episode in matched:
                continue

            # Get the partless title for this episode, and match within season
            partless_title = episode.episode_info.title.get_partless_title()

            # Sublist of all matching episodes
            matching_episodes = [episode]

            # Check if the next sequential episode is a multiparter
            next_key = episode.episode_info + 1
            while next_key in self.episodes:
                # Get the next episode
                next_episode = self.episodes[next_key]
                next_title =next_episode.episode_info.title.get_partless_title()

                # If this next episode's partless title matches, add to list
                if partless_title == next_title:
                    matching_episodes.append(next_episode)
                else:
                    break

                # Move to next episode
                next_key = next_episode.episode_info + 1

            # If there are matching episodes, add to multiparts list
            if len(matching_episodes) > 1:
                # Create a MultiEpisode object for these episodes and new title
                multi = MultiEpisode(matching_episodes, Title(partless_title))

                destination = None
                if self.media_directory:
                    # Get the output filename for this multiepisode card
                    destination = TitleCard.get_multi_output_filename(
                        self.preferences.card_filename_format,
                        self.series_info,
                        multi,
                        self.media_directory,
                    )
                    multi.set_destination(destination)

                # Add MultiEpisode to list
                multiparts.append(multi)
                matched.update(set(matching_episodes))

        # Add all MultiEpisode objects to this show's episode dictionary
        for mp in multiparts:
            self.episodes[f'0{mp.season_number}-{mp.episode_start}'] = mp


    def create_missing_title_cards(self) -> None:
        """Create any missing title cards for each episode."""

        # If the media directory is unspecified, exit
        if self.media_directory is None:
            return None

        # See if these cards need to be deleted/updated for new config
        if global_objects.show_record_keeper.is_updated(self):
            log.info(f'Detected new YAML for {self} - deleting old cards')
            for episode in self.episodes.values():
                episode.delete_card(reason='new config')

        # Go through each episode for this show
        for episode in (pbar := tqdm(self.episodes.values(), **TQDM_KWARGS)):
            # Skip episodes without a destination or that already exist
            if not episode.destination or episode.destination.exists():
                continue

            # Skip episodes without souce that need them
            if (self.card_class.USES_UNIQUE_SOURCES
                and not episode.source.exists()):
                continue

            # Update progress bar
            pbar.set_description(f'Creating {episode}')

            # Create a TitleCard object for this episode with Show's profile
            title_card = TitleCard(
                episode,
                self.profile,
                self.card_class.TITLE_CHARACTERISTICS,
                **self.extras,
                **episode.extra_characteristics,
            )

            # Skip if title is invalid for font
            title_card.converted_title, valid = self.font.validate_title(
                title_card.converted_title
            )
            if not valid:
                log.warning(f'Invalid font for {episode} of {self}')
                continue

            # Source exists, create the title card
            title_card.create()

        # Update record keeeper
        global_objects.show_record_keeper.add_config(self)


    def create_season_posters(self) -> None:
        """Create season posters for this Show."""

        # Create all posters in the set (if specification was valid)
        if self.season_poster_set.valid:
            self.season_poster_set.create()


    def update_media_server(self) -> None:
        """
        Update this show's media server with all title cards and season
        posters for all Episodes associated with this show.
        """

        # Get appropriate MediaServer interface
        media_interface = {
            None: None,
            'emby': self.emby_interface,
            'jellyfin': self.jellyfin_interface,
            'plex': self.plex_interface
        }[self.media_server]

        # Exit if no valid media interface
        if not media_interface:
            return None

        # Set title cards and season posters in media interface
        media_interface.set_title_cards(
            self.library_name, self.series_info, self.episodes,
        )

        media_interface.set_season_posters(
            self.library_name, self.series_info, self.season_poster_set,
        )

        return None