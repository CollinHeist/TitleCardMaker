from pathlib import Path
from re import match

from tqdm import tqdm

from modules.DataFileInterface import DataFileInterface
from modules.Debug import log
from modules.Episode import Episode
from modules.Font import Font
from modules.MultiEpisode import MultiEpisode
import modules.preferences as global_preferences
from modules.Profile import Profile
from modules.SeriesInfo import SeriesInfo
from modules.TitleCard import TitleCard
from modules.Title import Title
from modules.YamlReader import YamlReader

class Show(YamlReader):
    """
    This class describes a show. A show encapsulates the names and preferences
    with a complete series of episodes. Each object inherits many preferences 
    from the global `PreferenceParser` object, but manually specified attributes
    within the Show's YAML take precedence over the global enables, with the
    exception of Interface objects (such as Sonarr and TMDb).
    """


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
                                        search for and place source images.
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
        if not match(r'^\d{4}$', str(year)):
            log.error(f'Year "{year}" of series "{name}" is invalid')
            self.valid = False
            return None

        # Setup default values that can be overwritten by YAML
        self.series_info = SeriesInfo(name, year)
        self.media_directory = None
        self.card_class = TitleCard.CARD_TYPES[self.preferences.card_type]
        self.episode_text_format = self.card_class.EPISODE_TEXT_FORMAT
        self.library_name = None
        self.library = None
        self.archive = True
        self.sonarr_sync = True
        self.sync_specials = self.preferences.sonarr_sync_specials
        self.tmdb_sync = True
        self.hide_seasons = False
        self.__episode_range = {}
        self.__season_map = {n: f'Season {n}' for n in range(1, 1000)}
        self.__season_map[0] = 'Specials'
        self.title_language = {}

        # Set object attributes based off YAML and update validity
        self.__parse_yaml()
        self.font = Font(
            self._base_yaml.get('font', {}),
            font_map,
            self.card_class,
            self.series_info,
        )
        self.valid = self.font.valid

        # Update derived attributes
        self.source_directory = source_directory / self.series_info.full_name
        self.logo = self.source_directory / self.preferences.logo_filename

        # Create DataFileInterface fo this show
        self.file_interface = DataFileInterface(
            self.source_directory / DataFileInterface.GENERIC_DATA_FILE_NAME
        )

        # Create the profile for this show
        self.profile = Profile(
            self.font,
            self.hide_seasons,
            self.__season_map,
            self.__episode_range,
            'range' if self.__episode_range != {} else 'map',
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


    def __parse_yaml(self):
        """
        Parse the show's YAML and update this object's attributes. Error on any
        invalid attributes and update this object's validity.
        """

        if (name := self['name']):
            self.series_info.update_name(name)

        if (library := self['library']):
            # If the given library isn't in libary map, invalid
            if library not in self.__library_map:
                log.error(f'Library "{library}" of series {self} is not found '
                          f'in libraries list')
                self.valid = False
            else:
                # Valid library, update library and media directory
                self.library_name = library
                self.library = Path(self.__library_map[library]['path'])
                self.media_directory = self.library / self.series_info.full_name

                # If card type was specified for this library, set that
                if 'card_type' in self.__library_map[library]:
                    card_type = self.__library_map[library]['card_type']
                    if card_type not in TitleCard.CARD_TYPES:
                        log.error(f'Unknown card type "{card_type}" of series '
                                  f'{self}')
                        self.valid = False
                    else:
                        self.card_class = TitleCard.CARD_TYPES[card_type]
                        etf = self.card_class.EPISODE_TEXT_FORMAT
                        self.episode_text_format = etf

        if (card_type := self['card_type']):
            if card_type not in TitleCard.CARD_TYPES:
                log.error(f'Unknown card type "{card_type}" of series {self}')
                self.valid = False
            else:
                self.card_class = TitleCard.CARD_TYPES[card_type]
                self.episode_text_format = self.card_class.EPISODE_TEXT_FORMAT

        if (value := self['media_directory']):
            self.media_directory = Path(value)

        if (value := self['episode_text_format']):
            self.episode_text_format = value

        if (value := self['archive']):
            self.archive = bool(value)

        if (value := self['sonarr_sync']):
            self.sonarr_sync = bool(value)

        if (value := self['sync_specials']):
            self.sync_specials = bool(value)

        if (value := self['tmdb_sync']):
            self.tmdb_sync = bool(value)

        if (value := self['seasons', 'hide']):
            self.hide_seasons = bool(value)

        if self['translation', 'language'] and self['translation', 'key']:
            if (key := self['translation', 'key']) in ('title', 'abs_number'):
                log.error(f'Cannot add translations under the key "{key}" in '
                          f'series {self}')
            else:
                self.title_language = self['translation']

        # Validate season map & episode range aren't specified at the same time
        if (seasons := self['seasons']) and self['episode_ranges']:
            if any(isinstance(key, int) for key in seasons.keys()):
                log.warning(f'Cannot specify season titles with both "seasons" '
                            f'and "episode_ranges" in series {self}')
                self.valid = False

        # Validate season title map
        if (seasons := self['seasons']):
            for tag in seasons:
                if isinstance(tag, int):
                    self.__season_map[tag] = self['seasons', tag]

        # Validate episode range map
        if (episode_ranges := self['episode_ranges']):
            for episode_range in episode_ranges:
                # If the range cannot be parsed, then error and skip
                try:
                    start, end = map(int, episode_range.split('-'))
                except:
                    log.error(f'Episode range "{episode_range}" of series '
                              f'{self} is invalid - specify as "start-end"')
                    self.valid = False
                    continue

                # Assign this season title to each episde in the given range
                this_title = episode_ranges[episode_range]
                for episode_number in range(start, end+1):
                    self.__episode_range[episode_number] = this_title


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
        for _, episode in (pbar := tqdm(self.episodes.items(), leave=False)):
            # Update progress bar
            pbar.set_description(f'Checking {episode}')

            # If the key already exists, skip this episode
            if self.title_language['key'] in episode.extra_characteristics:
                continue

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


    def create_missing_title_cards(self,
                                   tmdb_interface: 'TMDbInterface'=None) ->bool:
        """
        Creates any missing title cards for each episode of this show.

        :param      tmdb_interface:     Optional TMDbInterface to download any
                                        missing source images from.

        :returns:   True if any new cards were created, False otherwise.
        """

        # If the media directory is unspecified, exit
        if self.media_directory is None:
            return False

        # Go through each episode for this show
        created_new_cards = False
        for _, episode in (pbar := tqdm(self.episodes.items(), leave=False)):
            # Update progress bar
            pbar.set_description(f'Creating {episode}')
            
            # Skip episodes without destination (do not create), or that exist
            if not episode.destination or episode.destination.exists():
                continue

            # If the title card source images doesn't exist and can query TMDb..
            if (not episode.source.exists()
                and self.tmdb_sync and tmdb_interface):
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
            created_new_cards |= title_card.create()

        return created_new_cards

