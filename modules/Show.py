from pathlib import Path

from tqdm import tqdm

from modules.DataFileInterface import DataFileInterface
from modules.Debug import log, TQDM_KWARGS
from modules.Episode import Episode
from modules.EpisodeMap import EpisodeMap
from modules.Font import Font
from modules.MultiEpisode import MultiEpisode
import modules.preferences as global_preferences
from modules.PlexInterface import PlexInterface
from modules.Profile import Profile
from modules.RemoteCardType import RemoteCardType
from modules.SeriesInfo import SeriesInfo
from modules.TitleCard import TitleCard
from modules.Title import Title
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

    __slots__ = ('preferences', '__library_map', 'series_info', 'valid',
                 'media_directory', 'card_class', 'episode_text_format',
                 'library_name', 'library', 'archive', 'sonarr_sync',
                 'sync_specials', 'tmdb_sync', 'hide_seasons','__episode_range',
                 '__season_map', 'title_language', 'font', 'source_directory',
                 'logo', 'backdrop', 'file_interface', 'profile', 'episodes')


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
        super().__init__(yaml_dict)

        # Get global PreferenceParser object
        self.preferences = global_preferences.pp
        
        # Parse arguments into attribures
        self.__library_map = library_map

        # Set this show's SeriesInfo object with blank year to start
        self.series_info = SeriesInfo(name, 0)

        # If year isn't given, skip completely
        if not (year := self['year']):
            log.error(f'Series "{name}" is missing the required "year"')
            self.valid = False
            return None

        # Year is given, parse and update year/full name of this show
        if not isinstance(year, int) or year < 0:
            log.error(f'Year "{year}" of series "{name}" is invalid')
            self.valid = False
            return None
            
        # Setup default values that can be overwritten by YAML
        self.valid = True
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
        self.style = self.preferences.style
        self.hide_seasons = False
        self.__episode_map = EpisodeMap()
        self.title_language = {}

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
        self.logo = self.source_directory / self.preferences.logo_filename
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


    def __copy__(self) -> 'Show':
        """
        Copy this Show object into a new (identical) Show.
        
        :returns:   A newly constructed Show object.
        """

        return Show(self.series_info.name, self._base_yaml, self.__library_map,
                    self.font._Font__font_map, self.source_directory.parent)


    def __parse_yaml(self):
        """
        Parse the show's YAML and update this object's attributes. Error on any
        invalid attributes and update this object's validity.
        """

        if (name := self['name']):
            self.series_info.update_name(name)

        if (library := self['library']):
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
                    if card_type in TitleCard.CARD_TYPES:
                        self.card_class = TitleCard.CARD_TYPES[card_type]
                        etf = self.card_class.EPISODE_TEXT_FORMAT
                        self.episode_text_format = etf
                    elif (remote_card_type := RemoteCardType(card_type)).valid:
                        self.card_class = remote_card_type.card_class
                        etf = self.card_class.EPISODE_TEXT_FORMAT
                        self.episode_text_format = etf
                    else:
                        log.error(f'Unknown card type "{card_type}" of series '
                                  f'{self}')
                        self.valid = False

        if (card_type := self['card_type']):
            # If known card type, set right away, otherwise check remote repo
            if card_type in TitleCard.CARD_TYPES:
                self.card_class = TitleCard.CARD_TYPES[card_type]
                self.episode_text_format = self.card_class.EPISODE_TEXT_FORMAT
            elif (remote_card_type := RemoteCardType(card_type)).valid:
                self.card_class = remote_card_type.card_class
                self.episode_text_format = self.card_class.EPISODE_TEXT_FORMAT
            else:
                log.error(f'Unknown card type "{card_type}" of series {self}')
                self.valid = False
            
        if (value := self['media_directory']):
            self.media_directory = Path(value)

        if self._is_specified('episode_text_format'):
            self.episode_text_format = self['episode_text_format']

        if self._is_specified('archive'):
            self.archive = bool(self['archive'])

        if self._is_specified('sonarr_sync'):
            self.sonarr_sync = bool(self['sonarr_sync'])

        if self._is_specified('sync_specials'):
            self.sync_specials = bool(self['sync_specials'])

        if self._is_specified('tmdb_sync'):
            self.tmdb_sync = bool(self['tmdb_sync'])

        if (value := self['watched_style']):
            match_value = str(value).lower()
            if match_value not in self.VALID_STYLES:
                log.error(f'Invalid watched style "{value}" in series {self}')
                self.valid = False
            else:
                self.watched_style = match_value

        if (value := self['unwatched_style']):
            match_value = str(value).lower()
            if match_value not in self.VALID_STYLES:
                log.error(f'Invalid unwatched style "{value}" in series {self}')
                self.valid = False
            else:
                self.unwatched_style = match_value

        if self._is_specified('seasons', 'hide'):
            self.hide_seasons = bool(self['seasons', 'hide'])

        if self['translation', 'language'] and self['translation', 'key']:
            if (key := self['translation', 'key']) in ('title', 'abs_number'):
                log.error(f'Cannot add translations under the key "{key}" in '
                          f'series {self}')
            else:
                self.title_language = self['translation']
                
        self.__episode_map = EpisodeMap(self['seasons'], self['episode_ranges'])
        self.valid &= self.__episode_map.valid


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

        # If no title language was specified, or TMDb syncing isn't enabled,skip
        if self.title_language == {} or not self.tmdb_sync:
            return None

        # Go through every episode and look for translations
        modified = False
        for _, episode in (pbar := tqdm(self.episodes.items(), **TQDM_KWARGS)):
            # If the key already exists, skip this episode
            if self.title_language['key'] in episode.extra_characteristics:
                continue

            # Update progress bar
            pbar.set_description(f'Checking {episode}')

            # Query TMDb for the title of this episode in the requested language
            language_title = tmdb_interface.get_episode_title(
                self.series_info,
                episode.episode_info,
                self.title_language['language'],
            )

            # If episode wasn't found, or the original title was returned, skip!
            if (language_title == None
                or language_title ==  episode.episode_info.title.full_title):
                continue

            # Adding translated title, log it
            log.debug(f'Adding "{language_title}" to '
                      f'"{self.title_language["key"]}" of {self}')

            # Modify data file entry with new title
            modified = True
            self.file_interface.add_data_to_entry(
                episode.episode_info,
                **{self.title_language['key']: language_title},
            )

        # If any translations were added, re-read source
        if modified:
            self.read_source()
            
            
    def select_source_images(self, plex_interface: PlexInterface=None,
                             tmdb_interface: 'TMDbInterface'=None) -> None:
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
        """
        
        # Update watched statuses via Plex
        if plex_interface != None and self.library != None:
            plex_interface.update_watched_statuses(
                self.library_name,
                self.series_info,
                self.episodes,
                self.watched_style,
                self.unwatched_style,
            )
        else:
            [episode.update_statuses(False, self.watched_style,
                                     self.unwatched_style)
             for _, episode in self.episodes.items()]
            
        # Get show styles
        watched_style = self.watched_style
        unwatched_style = self.unwatched_style

        # Go through all episodes and select source images
        download_backdrop = False
        for key, episode in self.episodes.items():
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
                found = episode.update_source(self.backdrop, downloadable=False)
                download_backdrop = True
            else:
                episode.blur = True

            # Override to backdrop if indicated by style, or manual image not found
            if (((episode.watched and watched_style == 'art')
                or (not episode.watched and unwatched_style == 'art'))
                and not found):
                episode.update_source(self.backdrop, downloadable=True)
                download_backdrop = True
            
        # Query TMDb for the backdrop if one does not exist
        if (download_backdrop and tmdb_interface and self.tmdb_sync
            and not self.backdrop.exists()):
            # Download background art 
            if (url := tmdb_interface.get_series_backdrop(self.series_info)):
                tmdb_interface.download_image(url, self.backdrop)


    def create_missing_title_cards(self,
                                   tmdb_interface: 'TMDbInterface'=None) ->None:
        """
        Creates any missing title cards for each episode of this show.

        :param      tmdb_interface:     Optional TMDbInterface to download any
                                        missing source images from.
        """

        # If the media directory is unspecified, exit
        if self.media_directory is None:
            return False

        # Go through each episode for this show
        for _, episode in (pbar := tqdm(self.episodes.items(), **TQDM_KWARGS)):
            # Update progress bar
            pbar.set_description(f'Creating {episode}')
            
            # Skip episodes without destination (do not create), or that exist
            if not episode.destination or episode.destination.exists():
                continue

            # If the title card source images doesn't exist and can query TMDb..
            if (self.tmdb_sync and tmdb_interface
                and episode.downloadable_source and not episode.source.exists()):
                # Query TMDbInterface for image
                image_url = tmdb_interface.get_source_image(
                    self.series_info,
                    episode.episode_info
                )

                # Skip this card if no image is returned
                if not image_url:
                    continue

                # Download the image
                tmdb_interface.download_image(image_url, episode.source)

            # Create a TitleCard object for this episode with Show's profile
            title_card = TitleCard(
                episode,
                self.profile,
                self.card_class.TITLE_CHARACTERISTICS,
                **episode.extra_characteristics,
            )

            # Skip if title is invalid for font
            if not self.font.validate_title(title_card.converted_title):
                log.warning(f'Invalid font for {episode} of {self}')
                continue

            # Source exists, create the title card
            title_card.create()


    def update_plex(self, plex_interface: PlexInterface) -> None:
        """
        Update the given PlexInterface with all title cards for all Episodes
        within this Show.

        :param      plex_interface: PlexInterface object to update.
        """

        # Skip if no library specified
        if self.library_name == None:
            return None

        # Update Plex
        plex_interface.set_title_cards_for_series(
            self.library_name,
            self.series_info,
            self.episodes,
        )

