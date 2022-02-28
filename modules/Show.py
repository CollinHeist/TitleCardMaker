from pathlib import Path
from re import match

from tqdm import tqdm
from yaml import safe_load

from modules.CardType import CardType
from modules.DataFileInterface import DataFileInterface
from modules.Debug import info, warn, error
from modules.Episode import Episode
from modules.EpisodeInfo import EpisodeInfo
import modules.preferences as global_preferences
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
        
        # Parse arguments given by the creator of this object
        self.__yaml = yaml_dict
        self.__library_map = library_map

        # If year isn't given, skip completely
        if not self.__is_specified('year'):
            error(f'Series "{name}" is missing required "year"')
            self.valid = False
            return 

        # Year is given, parse and update year/full name of this show
        year = self.__yaml['year']
        if not match(r'^\d{4}$', str(year)):
            error(f'Year "{year}" of series "{name}" is invalid')
            self.valid = False
            return

        # Set this show's SeriesInfo object
        self.series_info = SeriesInfo(name, year)
        
        # Setup default values that can be overwritten by the YML
        self.library_name = None
        self.library = None
        self.card_class = TitleCard.CARD_TYPES[self.preferences.card_type]
        self.source_directory = source_directory / self.series_info.full_name
        self.episode_text_format = 'EPISODE {episode_number}'
        self.archive = True
        self.sonarr_sync = True
        self.tmdb_sync = True
        self.font_color = self.card_class.TITLE_COLOR
        self.font_size = 1.0
        self.font = self.card_class.TITLE_FONT
        self.font_case = self.card_class.DEFAULT_FONT_CASE
        self.font_replacements = self.card_class.FONT_REPLACEMENTS
        self.hide_seasons = False
        self.__episode_range = {}
        self.__season_map = {n: f'Season {n}' for n in range(1, 1000)}
        self.__season_map[0] = 'Specials'
        self.title_language = {}

        # Modify object attributes based off YAML and update validity attribute
        self.valid = True
        self.__parse_yaml()

        # Update non YAML-able attributes for this show now that overwriting has occurred
        self.media_directory = None
        if self.library:
            self.media_directory = self.library / self.series_info.full_name
        self.logo = self.source_directory / self.preferences.logo_filename
        self.file_interface = DataFileInterface(
            self.source_directory / DataFileInterface.GENERIC_DATA_FILE_NAME
        )

        # Assign the profile for this show
        self.profile = Profile(
            self.font_color,
            self.font_size,
            self.font,
            self.font_case,
            self.font_replacements,
            self.hide_seasons,
            self.__season_map,
            self.__episode_range,
            'range' if self.__episode_range != {} else 'map',
            self.episode_text_format,
        )

        # Episode dictionary to be filled
        self.episodes = {}


    def __repr__(self) -> str:
        """Returns a unambiguous string representation of the object"""

        return f'<Show "{self.series_info}" with {len(self.episodes)} Episodes>'


    def __parse_yaml(self):
        """
        Parse the show's YAML and update this object's attributes. Error on any
        invalid attributes and update `valid` attribute.
        """

        # Read all optional tags
        if self.__is_specified('name'):
            self.series_info.update_name(self.__yaml['name'])

        if self.__is_specified('library'):
            value = self.__yaml['library']
            if value not in self.__library_map:
                error(f'Library "{value}" of series "{self.name}" is not found '
                      f'in libraries list')
                self.valid = False
            else:
                self.library_name = value
                self.library = Path(self.__library_map[value])

        if self.__is_specified('card_type'):
            value = self.__yaml['card_type']
            if value not in TitleCard.CARD_TYPES:
                error(f'Card type "{value}" of series "{self.name}" is unknown,'
                      f' ensure any custom card classes are added to the '
                      f'CARD_TYPES dictionary of the TitleCard class')
                self.valid = False
            else:
                self.card_class = TitleCard.CARD_TYPES[value]

        if self.__is_specified('source'):
            self.source_directory = Path(self.__yaml['source'])

        if self.__is_specified('episode_text_format'):  
            self.episode_text_format = self.__yaml['episode_text_format']

        if self.__is_specified('archive'):
            self.archive = bool(self.__yaml['archive'])

        if self.__is_specified('sonarr_sync'):
            self.sonarr_sync = bool(self.__yaml['sonarr_sync'])

        if self.__is_specified('tmdb_sync'):
            self.tmdb_sync = bool(self.__yaml['tmdb_sync'])

        if self.__is_specified('source_directory'):
            self.source_directory = Path(self.__yaml['source_directory'])

        if self.__is_specified('font', 'color'):
            value = self.__yaml['font']['color']
            if not bool(match('^#[a-fA-F0-9]{6}$', value)):
                error(f'Font color "{value}" of series "{self.name}" is invalid'
                      f' - specify as "#xxxxxx"')
                self.valid = False
            else:
                self.font_color = value

        if self.__is_specified('font', 'size'):
            value = self.__yaml['font']['size']
            if not bool(match('^\d+%$', value)):
                error(f'Font size "{value}" of series "{self.name}" is invalid '
                      f'- specify as "x%"')
                self.valid = False
            else:
                self.font_size = float(value[:-1]) / 100.0

        if self.__is_specified('font', 'file'):
            value = Path(self.__yaml['font']['file'])
            if not value.exists():
                error(f'Font file "{value}" of series "{self.name}" not found')
                self.valid = False
            else:
                self.font = str(value.resolve())
                self.font_replacements = {} # Reset for manually specified font

        if self.__is_specified('font', 'case'):
            value = self.__yaml['font']['case'].lower()
            if value not in self.card_class.CASE_FUNCTION_MAP:
                error(f'Font case "{value}" of series "{self.name}" is unrecognized')
                self.valid = False
            else:
                self.font_case = value

        if self.__is_specified('font', 'replacements'):
            if any(len(key) != 1 for key in self.__yaml['font']['replacements'].keys()):
                error(f'Font replacements of series "{self.name}" is invalid - '
                      f'must only be 1 character')
                self.valid = False
            else:
                self.font_replacements = self.__yaml['font']['replacements']

        if self.__is_specified('seasons', 'hide'):
            self.hide_seasons = bool(self.__yaml['seasons']['hide'])

        # Validate season map and episode range aren't specified at the same time
        if (self.__is_specified('seasons')
            and self.__is_specified('episode_ranges')):
            if any(isinstance(key, int) for key in self.__yaml['seasons'].keys()):
                error(f'Cannot specify season titles with both "seasons" and '
                      f'"episode_ranges"')
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
                    error(f'Episode range "{episode_range}" for series "'
                          f'{self.name}" is invalid - specify as "start-end"')
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
        
        :param      attribute:      The attribute to check for.
        :param      sub_attribute:  The sub attribute to check for. Necessary if
                                    the given attribute has attributes of its
                                    own.
        
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


    def create_missing_title_cards(self, tmdb_interface: 'TMDbInterface'=None,
                              sonarr_interface: 'SonarrInterface'=None) -> bool:
        """
        Creates any missing title cards for each episode of this show.

        :param      tmdb_interface: Optional interface to TMDb to download any
                                    source images that are missing.

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

