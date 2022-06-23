from copy import copy
from pathlib import Path

from tqdm import tqdm

from modules.DataFileInterface import DataFileInterface
from modules.Debug import log, TQDM_KWARGS
from modules.Episode import Episode
from modules.EpisodeMap import EpisodeMap
from modules.Font import Font
from modules.MultiEpisode import MultiEpisode
import modules.global_objects as global_objects
from modules.PlexInterface import PlexInterface
from modules.Profile import Profile
from modules.RemoteCardType import RemoteCardType
from modules.SeasonPosterSet import SeasonPosterSet
from modules.SeriesInfo import SeriesInfo
from modules.TitleCard import TitleCard
from modules.Title import Title
from modules.WebInterface import WebInterface
from modules.YamlReader import YamlReader

class Show(YamlReader):
    """
    This class describes a show. A Show encapsulates the names and preferences
    with a complete series of episodes. Each object inherits many preferences 
    from the global `PreferenceParser` object, but manually specified attributes
    within the Show's YAML take precedence over the global enables, with the
    exception of Interface objects (such as Sonarr and TMDb).
    """
    
    """Valid card styles for a series"""
    VALID_STYLES = ('unique', 'art', 'blur')

    """Filename to the backdrop for a series"""
    BACKDROP_FILENAME = 'backdrop.jpg'

    __slots__ = ('preferences', 'valid', '__library_map', 'series_info',
                 'media_directory', 'card_class', 'episode_text_format',
                 'library_name', 'library', 'archive', 'sonarr_sync',
                 'sync_specials', 'tmdb_sync','watched_style','unwatched_style',
                 'hide_seasons','__episode_map', 'title_language', 'font',
                 'source_directory', 'logo', 'backdrop', 'file_interface',
                 'profile', 'episodes')


    def __init__(self, name: str, yaml_dict: dict, library_map: dict, 
                 font_map: dict, source_directory: Path) -> None:
        """
        Constructs a new instance of a Show object from the given YAML
        dictionary, library map, and referencing the base source directory. If
        the initialization fails to produce a 'valid' show object, the `valid`
        attribute is set to False.

        :param      name:               The name or title of the series.
        :param      yaml_dict:          YAML dictionary of the associated series
                                        as found in a card YAML file.
        :param      library_map:        Map of library titles to media
                                        directories.
        :param      font_map:           Map of font labels to custom font
                                        descriptions.
        :param      source_directory:   Base source directory this show should
                                        search for and place source images in.
        """

        # Initialize parent YamlReader object
        super().__init__(yaml_dict, log_function=log.error)

        # Get global PreferenceParser object
        self.preferences = global_objects.pp
        
        # Parse arguments into attribures
        self.__library_map = library_map

        # Set this show's SeriesInfo object with blank year to start
        self.series_info = SeriesInfo(name, 0)

        # If year isn't given, skip completely
        if (year := self._get('year', type_=int)) is None:
            log.error(f'Series "{name}" is missing the required "year"')
            self.valid = False
            return None
            
        # Setup default values that can be overwritten by YAML
        self.series_info = SeriesInfo(name, year)
        self.media_directory = None
        self.card_class = TitleCard.CARD_TYPES[self.preferences.card_type]
        self.episode_text_format = self.card_class.EPISODE_TEXT_FORMAT
        self.library_name = None
        self.library = None
        self.archive = self.preferences.create_archive
        self.sonarr_sync = self.preferences.use_sonarr
        self.sync_specials = self.preferences.sonarr_sync_specials
        self.tmdb_sync = self.preferences.use_tmdb
        self.watched_style = self.preferences.global_watched_style
        self.unwatched_style = self.preferences.global_unwatched_style
        self.hide_seasons = False
        self.__episode_map = EpisodeMap()
        self.title_languages = {}
        self.extras = {}

        # Set object attributes based off YAML and update validity
        self.__parse_yaml()
        self.font = Font(
            self._base_yaml.get('font', {}),
            font_map,
            self.card_class,
            self.series_info,
        )
        self.valid &= self.font.valid

        # Update derived attributes
        self.source_directory = source_directory / self.series_info.legal_path
        self.logo = self.source_directory / 'logo.png'
        self.backdrop = self.source_directory / self.BACKDROP_FILENAME

        # Create DataFileInterface fo this show
        self.file_interface = DataFileInterface(
            self.source_directory / DataFileInterface.GENERIC_DATA_FILE_NAME
        )

        # Create the profile for this show
        self.profile = Profile(
            self.font,
            self.hide_seasons,
            self.__episode_map,
            self.episode_text_format,
        )

        # Episode dictionary to be filled
        self.episodes = {}


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'"{self.series_info.full_name}"'


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object"""

        return f'<Show "{self.series_info}" with {len(self.episodes)} Episodes>'


    def _copy_with_modified_media_directory(self,
                                            media_directory: Path) -> 'Show':
        """
        Recreate this Show object with a modified media directory.

        :param      media_directory:    Media directory the returned Show object
                                        will utilize.
        
        :returns:   A newly constructed Show object.
        """

        # Modify base yaml to have overriden media_directory attribute
        modified_base = copy(self._base_yaml)
        modified_base['media_directory'] = str(media_directory.resolve())
        
        # Recreate Show object with modified YAML
        return Show(self.series_info.name, modified_base, self.__library_map,
                    self.font._Font__font_map, self.source_directory.parent)


    def __parse_card_type(self, card_type: str) -> None:
        """
        Read the card_type specification for this object. This first looks at
        the locally implemented types in the TitleCard class, then attempts to
        create a RemoteCardType from the specification. This can be either a
        local file to inject, or a GitHub-hosted remote file to download and
        inject. This updates the card_type, valid, and episode_text_format
        attributes of this object.
        
        :param      card_type:  The value of card_type to read/parse.
        """

        # If known card type, set right away, otherwise check remote repo
        if card_type in TitleCard.CARD_TYPES:
            self.card_class = TitleCard.CARD_TYPES[card_type]
        elif (remote_card_type := RemoteCardType(card_type)).valid:
            self.card_class = remote_card_type.card_class
        else:
            log.error(f'Invalid card type "{card_type}" of series {self}')
            self.valid = False

        # Update ETF
        self.episode_text_format = self.card_class.EPISODE_TEXT_FORMAT


    def __parse_yaml(self):
        """
        Parse the show's YAML and update this object's attributes. Error on any
        invalid attributes and update this object's validity.
        """

        if (name := self._get('name', type_=str)) is not None:
            self.series_info.update_name(name)

        if (library := self._get('library')) is not None:
            # If the given library isn't in libary map, invalid
            if not (this_library := self.__library_map.get(library)):
                log.error(f'Library "{library}" of series {self} is not found '
                          f'in libraries list')
                self.valid = False
            else:
                # Valid library, update library and media directory
                self.library_name = this_library.get('plex_name', library)
                self.library = Path(this_library['path'])
                self.media_directory = self.library /self.series_info.legal_path

                # If card type was specified for this library, set that
                if (card_type := this_library.get('card_type')):
                    self.__parse_card_type(card_type)

        if (card_type := self._get('card_type', type_=str)) is not None:
            self.__parse_card_type(card_type)
            
        if (value := self._get('media_directory', type_=Path)) is not None:
            self.media_directory = value

        if (value := self._get('episode_text_format', type_=str)) is not None:
            self.episode_text_format = value

        if (value := self._get('archive', type_=bool)) is not None:
            self.archive = value

        if (value := self._get('sonarr_sync', type_=bool)) is not None:
            self.sonarr_sync = value

        if (value := self._get('sync_specials', type_=bool)) is not None:
            self.sync_specials = value

        if (value := self._get('tmdb_sync', type_=bool)) is not None:
            self.tmdb_sync = value

        if (value := self._get('watched_style', type_=str)) is not None:
            if value not in self.VALID_STYLES:
                log.error(f'Invalid watched style "{value}" in series {self}')
                self.valid = False
            else:
                self.watched_style = value

        if (value := self._get('unwatched_style', type_=str)) is not None:
            if value not in self.VALID_STYLES:
                log.error(f'Invalid unwatched style "{value}" in series {self}')
                self.valid = False
            else:
                self.unwatched_style = value

        if self._is_specified('unwatched'):
            log.error(f'"unwatched" setting has been renamed "unwatched_style"')
            self.valid = False

        if (value := self._get('seasons', 'hide', type_=bool)) is not None:
            self.hide_seasons = value

        if (value := self._get('translation')) is not None:
            if isinstance(value, dict) and value.keys() == {'language', 'key'}:
                # Single translation
                self.title_languages = [value]
            elif isinstance(value, list):
                # List of translations
                if all(isinstance(t, dict) and t.keys() == {'language', 'key'}
                       for t in value):
                    self.title_languages = value
                else:
                    log.error(f'Invalid language translations in series {self}')
            else:
                log.error(f'Invalid language translations in series {self}')
                
        # Construct EpisodeMap on seasons/episode ranges specification
        self.__episode_map = EpisodeMap(
            self._get('seasons', type_=dict),
            self._get('episode_ranges', type_=dict)
        )

        # Update object validity with EpisodeMap validity
        self.valid &= self.__episode_map.valid

        # Read all extras
        if self._is_specified('extras'):
            self.extras = self._get('extras', type_=dict)


    def __get_destination(self, episode_info: 'EpisodeInfo') -> Path:
        """
        Get the destination filename for the given entry of a datafile.
        
        :param      episode_info:   EpisodeInfo for this episode.
        
        :returns:   Path for the full title card destination, and None if this
                    show has no media directory.
        """

        # If this entry should not be written to a media directory, return 
        if not self.media_directory:
            return None
        
        return TitleCard.get_output_filename(
            self.preferences.card_filename_format,
            self.series_info,
            episode_info,
            self.media_directory
        )


    def read_source(self) -> None:
        """
        Read the source file for this show, adding the associated Episode
        objects to this show's episodes dictionary.
        """

        # Reset episodes dictionary
        self.episodes = {}

        # Go through each entry in the file interface
        for entry in self.file_interface.read():
            # Create Episode object for this entry, store under key
            self.episodes[entry['episode_info'].key] = Episode(
                base_source=self.source_directory,
                destination=self.__get_destination(entry['episode_info']),
                card_class=self.card_class,
                **entry,
            )


    def find_multipart_episodes(self) -> None:
        """
        Find and create all the multipart episodes for this series. This adds
        MutliEpisode objects to this show's episodes dictionary.
        """

        # Set of episodes already mapped
        matched = set()

        # List of multipart episodes
        multiparts = []

        # Go through each episode to check if it can be made into a MultiEpisode
        for _, episode in self.episodes.items():
            # If this episode has already been used in MultiEpisode, skip
            if episode in matched:
                continue

            # Get the partless title for this episode, and match within season
            partless_title = episode.episode_info.title.get_partless_title()
            season_number = episode.episode_info.season_number

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


    def query_sonarr(self, sonarr_interface: 'SonarrInterface') -> None:
        """
        Query the provided SonarrInterface object, checking if the returned
        episodes exist in this show's associated source. All new entries are
        added to this object's DataFileInterface, the source is re-read, and
        episode ID's are set IF TMDb syncing is enabled.

        This method should only be called if Sonarr syncing is globally enabled.
        
        :param      sonarr_interface:   The SonarrInterface to query.
        """

        # Check if Sonarr is enabled for this show in partocular
        if not self.sonarr_sync:
            return None

        # Get list of EpisodeInfo objects from Sonarr
        all_episodes = sonarr_interface.get_all_episodes_for_series(
            self.series_info
        )

        # For each episode, check if the data matches any contained Episodes
        if all_episodes:
            # Filter out episodes that already exist
            new_episodes = list(filter(
                lambda e: e.key not in self.episodes,
                all_episodes,
            ))

            # Filter episodes that are specials if sync_specials is False
            if not self.sync_specials:
                new_episodes = list(filter(
                    lambda e: e.season_number != 0,
                    new_episodes,
                ))

            # If there are new episodes, add to the datafile, return True
            if new_episodes:
                self.file_interface.add_many_entries(new_episodes)
                self.read_source()

        # If TMDb syncing is enabled, set episode ID's for all episodes
        if self.tmdb_sync:
            all_episodes = list(ei for _, ei in self.episodes.items())
            sonarr_interface.set_all_episode_ids(self.series_info, all_episodes)


    def add_translations(self, tmdb_interface: 'TMDbInterface') -> None:
        """
        Add translated episode titles to the Episodes of this series. This 
        show's source file is re-read if any translations are added.
        
        :param      tmdb_interface: Interface to TMDb to query for translated
                                    episode titles.
        """

        # If no translations were specified, or TMDb syncing isn't enabled, skip
        if len(self.title_languages) == 0 or not self.tmdb_sync:
            return None

        # Go through every episode and look for translations
        modified = False
        for _, episode in (pbar := tqdm(self.episodes.items(), **TQDM_KWARGS)):
            # Get each translation for this series
            for translation in self.title_languages:
                # If the key already exists, skip this episode
                if translation['key'] in episode.extra_characteristics:
                    continue

                # Update progress bar
                pbar.set_description(f'Checking {episode}')

                # Query TMDb for the title of this episode in this language
                language_title = tmdb_interface.get_episode_title(
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
                          f'"{translation["key"]}" for {self}')

        # If any translations were added, re-read source
        if modified:
            self.read_source()


    def download_logo(self, tmdb_interface: 'TMDbInterface') -> None:
        """
        Download the logo for this series from TMDb. Any SVG logos are converted
        to PNG.
        
        :param      tmdb_interface: Interface to TMDb to download the logo from.
        """

        # If not syncing to TMDb, or logo already exists, exit
        if not self.tmdb_sync or self.logo.exists():
            return None

        # Download logo
        if (url := tmdb_interface.get_series_logo(self.series_info)):
            # SVG logos need to be converted first
            if url.endswith('.svg'):
                # Download .svgs to temporary location pre-conversion
                tmdb_interface.download_image(
                    url, self.card_class.TEMPORARY_SVG_FILE
                )

                # Convert temporary SVG to PNG at logo filepath
                self.card_class.convert_svg_to_png(
                    self.card_class.TEMPORARY_SVG_FILE,
                    self.logo,
                )
                log.debug(f'Converted logo for {self} from .svg to .png')
            else:
                tmdb_interface.download_image(url, self.logo)

            # Convert SVG to PNG
            log.debug(f'Downloaded logo for {self}')


    def __apply_styles(self, plex_interface: 'PlexInterface'=None,
                       select_only: Episode=None) -> bool:
        """
        Modify this series' Episode source images based on their watch statuses,
        and how that style applies to this show's un/watched styles. Return
        whether a backdrop should be downloaded.
        
        :param      plex_interface: Optional PlexInterface used to modify the
                                    Episode objects based on the watched status
                                    of. If not provided, episodes are assumed to
                                    all be unwatched (i.e. spoiler free).
        :param      select_only:    Optional Episode object. If provided, only
                                    this episode's style is applied.
        
        :returns:   Whether a backdrop should be downloaded or not.
        """

        # If no library, ignore styles
        if self.library is None:
            return False

        # Update watched statuses via Plex
        if plex_interface is None:
            # If no PlexInterface, assume all episodes are unwatched
            [episode.update_statuses(False, self.watched_style,
                                     self.unwatched_style)
             for _, episode in self.episodes.items()]
        else:
            episode_map = self.episodes
            if select_only:
                episode_map = {select_only.episode_info.key: select_only}

            plex_interface.update_watched_statuses(
                self.library_name,
                self.series_info,
                episode_map,
                self.watched_style,
                self.unwatched_style,
            )
            
        # Get show styles
        watched_style = self.watched_style
        unwatched_style = self.unwatched_style

        # Go through all episodes and select source images
        download_backdrop = False
        for key, episode in self.episodes.items():
            # If only selecting a specific episode, skip others
            if select_only is not None and episode is not select_only:
                continue
            
            # Try and get the manually specified source from the episode map
            manual_source = self.__episode_map.get_source(episode.episode_info)
            applies_to = self.__episode_map.get_applies_to(episode.episode_info)

            # Update source and blurring based on.. well, everything..
            found = True
            if ((applies_to == 'all' and unwatched_style == 'unique'
                 and watched_style != 'blur') or
                (applies_to == 'all' and unwatched_style == 'art'
                 and not (watched_style == 'blur' and episode.watched)) or
                (applies_to == 'all' and unwatched_style == 'blur'
                 and watched_style != 'blur' and episode.watched) or
                (applies_to == 'unwatched' and unwatched_style != 'blur'
                 and not episode.watched)):
                found = episode.update_source(manual_source, downloadable=False)
            elif ((applies_to == 'all') or
                (applies_to == 'unwatched' and unwatched_style == 'blur'
                 and not episode.watched)):
                episode.blur = True
                found = episode.update_source(manual_source, downloadable=False)
            elif watched_style == 'unique':
                continue
            elif watched_style == 'art':
                found = episode.update_source(self.backdrop, downloadable=True)
                download_backdrop = True
            else:
                episode.blur = True

            # Override to backdrop if indicated by style, or manual image DNE
            if (((episode.watched and watched_style == 'art')
                or (not episode.watched and unwatched_style == 'art'))
                and not found):
                episode.update_source(self.backdrop, downloadable=True)
                download_backdrop = True

        return download_backdrop
            
            
    def select_source_images(self, plex_interface: PlexInterface=None,
                             tmdb_interface: 'TMDbInterface'=None,
                             select_only: Episode=None) -> None:
        """
        Modify this series' Episode source images based on their watch statuses,
        and how that style applies to this show's un/watched styles. If a
        backdrop is required, and TMDb is enabled, then one is downloaded if it
        does not exist.
        
        :param      plex_interface: Optional PlexInterface used to modify the
                                    Episode objects based on the watched status
                                    of. If not provided, episodes are assumed to
                                    all be unwatched (i.e. spoiler free).
        :param      tmdb_interface: Optional TMDbInterface to query for a
                                    backdrop if one is needed and DNE.
        :param      select_only:    Optional Episode object. If provided, only
                                    this episode's source is selected.
        """

        # Modify Episodes watched/blur/source files based on plex status
        download_backdrop = self.__apply_styles(plex_interface,
                                                select_only=select_only)

        # Don't download source if this card type doesn't use unique images
        if not self.card_class.USES_UNIQUE_SOURCES:
            return None

        # Whether to always check TMDb or Plex
        always_check_tmdb = (self.preferences.use_tmdb and tmdb_interface
                             and self.tmdb_sync and self.preferences.check_tmdb)
        always_check_plex = (self.preferences.use_plex and plex_interface
            and self.library is not None and self.preferences.check_plex
            and plex_interface.has_series(self.library_name, self.series_info))

        # For each episode, query interfaces (in priority order) for source
        for _, episode in (pbar := tqdm(self.episodes.items(), **TQDM_KWARGS)):
            # If only selecting a specific episode, skip others
            if select_only is not None and episode is not select_only:
                continue
            
            # Skip this episode if not downloadable, or source exists
            if not episode.downloadable_source or episode.source.exists():
                continue

            # Update progress bar
            pbar.set_description(f'Selecting {episode}')

            # Check TMDb if this episode isn't permanently blacklisted
            if always_check_tmdb:
                blacklisted =  tmdb_interface.is_permanently_blacklisted(
                    self.series_info,
                    episode.episode_info,
                )
                check_tmdb = not blacklisted
            else:
                check_tmdb, blacklisted = False, False

            # Check Plex if enabled, provided, and valid relative to TMDb
            if always_check_plex:
                check_plex = (self.preferences.check_plex_before_tmdb
                              or blacklisted)
            else:
                check_plex = False

            # Go through each source interface indicated, try and get source
            for source_interface in self.preferences.source_priority:
                # Query either TMDb or Plex for the source image
                image_url = None
                if source_interface == 'tmdb' and check_tmdb:
                    image_url = tmdb_interface.get_source_image(
                        self.series_info,
                        episode.episode_info
                    )
                elif source_interface == 'plex' and check_plex:
                    image_url = plex_interface.get_source_image(
                        self.library_name,
                        self.series_info,
                        episode.episode_info,
                    )

                # If URL was returned by either interface, download
                if image_url is not None:
                    WebInterface.download_image(image_url, episode.source)
                    log.debug(f'Downloaded {episode.source.name} for {self} '
                              f'from {source_interface}')
                    break
        
        # Query TMDb for the backdrop if one does not exist and is needed
        if (download_backdrop and tmdb_interface and self.tmdb_sync
            and not self.backdrop.exists()):
            # Download background art 
            if (url := tmdb_interface.get_series_backdrop(self.series_info)):
                tmdb_interface.download_image(url, self.backdrop)


    def remake_card(self, episode_info: 'EpisodeInfo',
                    plex_interface: 'PlexInterface',
                    tmdb_interface: 'TMDbInterface'=None) -> None:
        """
        Remake the card associated with the given EpisodeInfo, updating the
        metadata within Plex.
        
        :param      episode_info:   EpisodeInfo corresponding to the Episode
                                    being updated. Matched by key.
        :param      plex_interface: The PlexInterface to utilize for watched
                                    status identification, source image
                                    gathering, and metadata refreshing.
        :param      tmdb_interface: Optional TMDbInterface to utilize for source
                                    gathering.
        """

        # If no episode of the given index (key) exists, nothing to remake, exit
        if (episode := self.episodes.get(episode_info.key)) is None:
            log.error(f'Episode {episode_info} not found in datafile')
            return None

        # Select proper source for this episode
        self.select_source_images(plex_interface, tmdb_interface,
                                  select_only=episode)

        # Exit if this card needs a source and it DNE
        if self.card_class.USES_UNIQUE_SOURCES and not episode.source.exists():
            log.error(f'Cannot remake card {episode.destination.resolve()} - no'
                      f'source image')
            return None

        # If card wasn't deleted, means watch status didn't change, exit
        if episode.destination.exists():
            log.debug(f'Not remaking card {episode.destination.resolve()}')
            return None

        # Create this card
        TitleCard(
            episode,
            self.profile,
            self.card_class.TITLE_CHARACTERISTICS,
            **self.extras,
            **episode.extra_characteristics,
        ).create()

        # Update Plex
        plex_interface.set_title_cards_for_series(
            self.library_name, self.series_info, {episode_info.key: episode}
        )


    def create_missing_title_cards(self) ->None:
        """Create any missing title cards for each episode of this show."""

        # If the media directory is unspecified, exit
        if self.media_directory is None:
            return False

        # Go through each episode for this show
        for _, episode in (pbar := tqdm(self.episodes.items(), **TQDM_KWARGS)):
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
            if not self.font.validate_title(title_card.converted_title):
                log.warning(f'Invalid font for {episode} of {self}')
                continue

            # Source exists, create the title card
            title_card.create()


    def create_season_posters(self) -> None:
        """Create season posters for this Show."""

        # Construct SeasonPosterSet and create posters
        poster_set = SeasonPosterSet(
            self.__episode_map,
            self.source_directory,
            self.media_directory,
            self._get('season_posters', type_=dict)
        )

        # Create all posters in the set (if specification was valid)
        if poster_set.valid:
            poster_set.create()


    def update_plex(self, plex_interface: PlexInterface) -> None:
        """
        Update the given PlexInterface with all title cards for all Episodes
        within this Show.

        :param      plex_interface: PlexInterface object to update.
        """

        # Skip if no library specified
        if self.library_name is None:
            return None

        # Update Plex
        plex_interface.set_title_cards_for_series(
            self.library_name,
            self.series_info,
            self.episodes,
        )

