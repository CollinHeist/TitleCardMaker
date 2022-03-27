from copy import deepcopy
from pathlib import Path
from re import match

from tqdm import tqdm

from modules.CardType import CardType
from modules.DataFileInterface import DataFileInterface
from modules.Debug import log
from modules.Episode import Episode
from modules.EpisodeInfo import EpisodeInfo
from modules.Font import Font
import modules.preferences as global_preferences
from modules.MultiEpisode import MultiEpisode
from modules.Profile import Profile
from modules.SeriesInfo import SeriesInfo
from modules.TitleCard import TitleCard
from modules.Title import Title

class Show:
    """
    This class describes a show. A show encapsulates the names and preferences
    with a complete series of episodes. Each object inherits many preferences 
    from the global `PreferenceParser` object, but manually specified attributes
    within the Show's YAML take precedence over the global enables, with the
    exception of Interface objects (such as Sonarr and TMDb).
    """


    def __init__(self, name: str, yaml_dict: dict, library_map: dict,
                 source_directory: Path) -> None:
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
        :param      source_directory:   Base source directory this show should
                                        search for and place source images. Can
                                        be overwritten by YAML tag.
        """

        self.preferences = global_preferences.pp
        
        # Parse arguments into attribures
        self.__yaml = yaml_dict
        self.__library_map = library_map

        # Set this show's SeriesInfo object with blank year to start
        self.series_info = SeriesInfo(name, 0)

        # If year isn't given, skip completely
        if not self.__is_specified('year'):
            log.error(f'Series "{name}" is missing the required "year"')
            self.valid = False
            return None

        # Year is given, parse and update year/full name of this show
        if not match(r'^\d{4}$', str(year := self.__yaml['year'])):
            log.error(f'Year "{year}" of series "{name}" is invalid')
            self.valid = False
            return None

        # Setup default values that can be overwritten by YAML
        self.series_info = SeriesInfo(name, year)
        self.card_class = TitleCard.CARD_TYPES[self.preferences.card_type]
        self.library_name = None
        self.library = None
        self.archive = True
        self.sonarr_sync = True
        self.tmdb_sync = True
        self.hide_seasons = False
        self.__episode_range = {}
        self.__season_map = {n: f'Season {n}' for n in range(1, 1000)}
        self.__season_map[0] = 'Specials'
        self.title_language = {}

        # Set object attributes based off YAML and update validity attribute
        self.__parse_yaml()
        self.font = Font(
            self.__yaml.get('font', {}),
            self.card_class,
            self.series_info
        )
        self.valid = self.font.valid

        # Update derived attributes
        self.episode_text_format = self.card_class.EPISODE_TEXT_FORMAT
        self.source_directory = source_directory / self.series_info.full_name
        self.logo = self.source_directory / self.preferences.logo_filename
        self.file_interface = DataFileInterface(
            self.source_directory / DataFileInterface.GENERIC_DATA_FILE_NAME
        )

        # If no library given, keep media directory as None
        self.media_directory = None
        if self.library:
            self.media_directory = self.library / self.series_info.full_name

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

        # Read all optional attributes
        if self.__is_specified('name'):
            self.series_info.update_name(self.__yaml['name'])

        if self.__is_specified('library'):
            if (library := self.__yaml['library']) not in self.__library_map:
                log.error(f'Library "{library}" of series {self} is not found '
                          f'in libraries list')
                self.valid = False
            else:
                self.library_name = library
                self.library = Path(self.__library_map[library]['path'])

                # If card type was specified for this library, set that
                if 'card_type' in self.__library_map[library]:
                    card_type = self.__library_map[library]['card_type']
                    if card_type not in TitleCard.CARD_TYPES:
                        log.error(f'Unknown card type "{card_type}" of series '
                                  f'{self}')
                        self.valid = False
                    else:
                        self.card_class = TitleCard.CARD_TYPES[card_type]

        if self.__is_specified('card_type'):
            if (value := self.__yaml['card_type']) not in TitleCard.CARD_TYPES:
                log.error(f'Unknown card type "{value}" of series {self}')
                self.valid = False
            else:
                self.card_class = TitleCard.CARD_TYPES[value]

        if self.__is_specified('source_directory'):
            self.source_directory = Path(self.__yaml['source_directory'])

        if self.__is_specified('episode_text_format'):  
            self.episode_text_format = self.__yaml['episode_text_format']

        if self.__is_specified('archive'):
            self.archive = bool(self.__yaml['archive'])

        if self.__is_specified('sonarr_sync'):
            self.sonarr_sync = bool(self.__yaml['sonarr_sync'])

        if self.__is_specified('tmdb_sync'):
            self.tmdb_sync = bool(self.__yaml['tmdb_sync'])

        if self.__is_specified('seasons', 'hide'):
            self.hide_seasons = bool(self.__yaml['seasons']['hide'])

        if (self.__is_specified('translation', 'language')
            and self.__is_specified('translation', 'key')):
            self.title_language = self.__yaml['translation']

        # Validate season map & episode range aren't specified at the same time
        if (self.__is_specified('seasons')
            and self.__is_specified('episode_ranges')):
            seasons = self.__yaml['seasons']
            if any(isinstance(key, int) for key in seasons.keys()):
                log.warning(f'Cannot specify season titles with both "seasons" '
                            f'and "episode_ranges" in series {self}')
                self.valid = False

        # Validate season title map
        if self.__is_specified('seasons'):
            for tag in self.__yaml['seasons']:
                if isinstance(tag, int):
                    self.__season_map[tag] = self.__yaml['seasons'][tag]

        # Validate episode range map
        if self.__is_specified('episode_ranges'):
            for episode_range in self.__yaml['episode_ranges']:
                # If the range cannot be parsed, then error and skip
                try:
                    start, end = map(int, episode_range.split('-'))
                except:
                    log.error(f'Episode range "{episode_range}" of series '
                              f'{self} is invalid - specify as "start-end"')
                    self.valid = False
                    continue

                # Assign this season title to each episde in the given range
                this_title = self.__yaml['episode_ranges'][episode_range]
                for episode_number in range(start, end+1):
                    self.__episode_range[episode_number] = this_title
        

    def __is_specified(self, *attributes: tuple) -> bool:
        """
        Determines whether the given attribute/sub-attribute has been manually 
        specified in the show's YAML.
        
        :param      attributes: Any number of attributes to check for. Each
                                subsequent argument is checked for as a sub-
                                attribute of the prior one.
        
        :returns:   True if specified, False otherwise.
        """

        current_level = self.__yaml
        for attr in attributes:
            # If this level isn't even a dictionary, or the attribute DNE, FALSE
            if not isinstance(current_level, dict) or attr not in current_level:
                return False

            if current_level[attr] == None:
                return False

            # Move to the next level
            current_level = current_level[attr]

        return True


    def __get_destination(self, episode_info: EpisodeInfo) -> Path:
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


    def check_sonarr_for_new_episodes(self,
                                      sonarr_interface:'SonarrInterface')->bool:
        """
        Query the provided SonarrInterface object, checking if the returned
        episodes exist in this show's associated source. All new entries are
        added to this object's DataFileInterface. This method should only be
        called if Sonarr syncing is globally enabled.
        
        :param      sonarr_interface:   The Sonarr interface to query.

        :returns:   True if Sonarr returned any new episodes, False otherwise.
        """

        # Check if Sonarr is enabled for this show in partocular
        if not self.sonarr_sync:
            return False

        # Get list of EpisodeInfo objects from Sonarr
        all_episodes = sonarr_interface.get_all_episodes_for_series(
            self.series_info
        )

        # For each episode, check if the data matches any contained Episodes
        has_new = False
        if all_episodes:
            # Filter out episodes that already exist
            new_episodes = list(filter(
                lambda e: e.key not in self.episodes,
                all_episodes,
            ))

            # Add all new entries to the datafile
            self.file_interface.add_many_entries(new_episodes)

        # If new entries were added, re-parse source file
        if has_new:
            self.read_source()
            return True

        return False


    def add_translations(self, tmdb_interface: 'TMDbInterface') -> bool:
        """
        Add translated episode titles to the Episodes of this series.
        
        :param      tmdb_interface: Interface to TMDb to query for translated
                                    episode titles.

        :returns:   True if any translations were added, False otherwise.
        """

        # If no title language was specified, or TMDb syncing isn't enabled,skip
        if self.title_language == {} or not self.tmdb_sync:
            return False

        modified = False
        # Go through every episode and look for translations
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

            # Adding data, log it
            log.debug(f'Adding "{language_title}" to '
                      f'"{self.title_language["key"]}" of {self}')

            # Modify data file entry with new title
            modified = True
            self.file_interface.add_data_to_entry(
                episode.episode_info,
                **{self.title_language['key']: language_title},
            )

        return modified


    def create_missing_title_cards(self, tmdb_interface: 'TMDbInterface'=None,
                              sonarr_interface: 'SonarrInterface'=None) -> bool:
        """
        Creates any missing title cards for each episode of this show.

        :param      tmdb_interface:     Optional interface to TMDb to download
                                        any missing source images.
        :param      sonarr_interface:   Optional interface to Sonarr to get
                                        episode and series ID's before querying
                                        TMDb.

        :returns:   True if any new cards were created, False otherwise.
        """

        # If the media directory is unspecified, then exit
        if self.media_directory is None:
            return False
            
        # If TMDb syncing is enabled, and a valid TMDb and Sonarr Interface were
        # provided, get all episode ID's for this series
        if self.tmdb_sync and tmdb_interface and sonarr_interface:
            all_episodes = list(ei for _, ei in self.episodes.items())
            sonarr_interface.set_all_episode_ids(self.series_info, all_episodes)

        # Go through each episode for this show
        created_new_cards = False
        for _, episode in (pbar := tqdm(self.episodes.items(), leave=False)):
            # Update progress bar
            pbar.set_description(f'Creating {episode}')
            
            # Skip episodes whose destination is None (don't create) or does exist
            if not episode.destination or episode.destination.exists():
                continue

            # Attempt to make a TitleCard object for this episode and profile
            # passing any extra characteristics from the episode along
            title_card = TitleCard(
                episode,
                self.profile,
                self.card_class.TITLE_CHARACTERISTICS,
                **episode.extra_characteristics,
            )

            # If the title card source images doesn't exist..
            if not episode.source.exists():
                # Skip if cannot query database
                if not self.tmdb_sync or not tmdb_interface:
                    continue

                # Query database for image
                image_url = tmdb_interface.get_source_image(
                    self.series_info,
                    episode.episode_info
                )

                # Skip if no image is returned
                if not image_url:
                    continue

                # Download the image
                tmdb_interface.download_image(image_url, episode.source)

            # Source exists, create the title card
            created_new_cards |= title_card.create()

        return created_new_cards

