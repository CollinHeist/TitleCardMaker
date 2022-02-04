from pathlib import Path
from re import match

from yaml import safe_load

from modules.DataFileInterface import DataFileInterface
from modules.Debug import *
from modules.Episode import Episode
import modules.preferences as global_preferences
from modules.Profile import Profile
from modules.TitleCard import TitleCard
from modules.StandardTitleCard import StandardTitleCard

class Show:
    """
    This class describes a show. A show encapsulates the names and preferences
    with a complete series of episodes. Each object inherits many preferences 
    from the global `PreferenceParser` object, but manually specified attributes
    within the Show's YAML take precedence over the global enables, with the
    exception of Interface objects (such as Sonarr and TMDb).
    """

    # FILENAME_FORMAT_HELP_STRING: str = (
    #     "Format String Options:\n"
    #     "  {show}      : The show's name\n"
    #     "  {year}      : The show's year\n"
    #     "  {full_name} : The show's full name - equivalent to {show} ({year})\n"
    #     "  {season}    : The episode's season number\n"
    #     "  {episode}   : The episode's episode number\n"
    #     "  {title}     : The episode title, as found in the source data file\n\n"
    #     "Example: ShowX, aired in 2022, Season 1 Episode 10 titled 'Pilot'\n"
    #     "  {show} - S{season:03} - {title}         -> ShowX - S001 - Pilot\n"
    #     "  {full_name} - S{season:02}E{episode:02} -> ShowX (2022) - S01E10\n"
    #     "  {show} {year} - S{season}E{episode}     -> ShowX 2022 - S1E10\n"
    # )

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
        self.name = name
        self.__yaml = yaml_dict
        self.__library_map = library_map

        # If year isn't given, skip completely
        if not self.__is_specified('year'):
            error(f'Series "{self.name}" is missing required "year"')
            self.valid = False
            return 

        # Year is given, parse and update year/full name of this show
        year = self.__yaml['year']
        if not match(r'^\d{4}$', str(year)):
            error(f'Year "{year}" of series "{self.name}" is invalid')
            self.valid = False
            return
        else:
            self.year = int(year)
            self.full_name = f'{self.name} ({self.year})'
        
        # Setup default values that can be overwritten by the YML
        self.library_name = None
        self.library = None
        self.source_directory = source_directory / self.full_name
        self.episode_text_format = 'EPISODE {episode_number}'
        self.archive = True
        self.sonarr_sync = True
        self.tmdb_sync = True
        self.font_color = StandardTitleCard.TITLE_DEFAULT_COLOR
        self.font_size = 1.0
        self.font = StandardTitleCard.TITLE_DEFAULT_FONT.resolve()
        self.font_case = 'upper'
        self.font_replacements = StandardTitleCard.DEFAULT_FONT_REPLACEMENTS
        self.hide_seasons = False
        self.__episode_range = {}
        self.__season_map = {n: f'Season {n}' for n in range(1, 1000)}
        self.__season_map[0] = 'Specials'

        # Modify object attributes based off YAML and update validity attribute
        self.valid = True
        self.__parse_yaml()

        # Update non YAML-able attributes for this show now that overwriting has occurred
        self.media_directory = self.library / self.full_name if self.library else None
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
        """
        Returns a unambiguous string representation of the object (for debug...).
        
        :returns:   String representation of the object.
        """

        return f'<Show "{self.full_name}" with {len(self.episodes)} Episodes>'


    def __parse_yaml(self):
        """
        Parse the show's YAML and update this object's attributes. Error on
        any invalid attributes and update `valid` attribute.
        
        :returns:   { description_of_the_return_value }
        """

        # Read all optional tags
        if self.__is_specified('name'):
            self.name = self.__yaml['name']

        if self.__is_specified('library'):
            value = self.__yaml['library']
            if value not in self.__library_map:
                error(f'Library "{value}" of series "{self.name}" is not found in libraries list')
                self.valid = False
            else:
                self.library_name = value
                self.library = Path(self.__library_map[value])

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
                error(f'Font color "{value}" of series "{self.name}" is invalid - specify as "#xxxxxx"')
                self.valid = False
            else:
                self.font_color = value

        if self.__is_specified('font', 'size'):
            value = self.__yaml['font']['size']
            if not bool(match('^\d+%$', value)):
                error(f'Font size "{value}" of series "{self.name}" is invalid - specify as "x%"')
                self.valid = False
            else:
                self.font_size = float(value[:-1]) / 100.0

        if self.__is_specified('font', 'file'):
            value = Path(self.__yaml['font']['file'])
            if not value.exists():
                error(f'Font file "{value}" of series "{self.name}" does not exist')
                self.valid = False
            else:
                self.font = value.resolve()
                self.font_replacements = {} # reset replacements if new font is given

        if self.__is_specified('font', 'case'):
            value = self.__yaml['font']['case'].lower()
            if value not in StandardTitleCard.CASE_FUNCTION_MAP:
                error(f'Font case "{value}" of series "{self.name}" is unrecognized')
                self.valid = False
            else:
                self.font_case = value

        if self.__is_specified('font', 'replacements'):
            if any(len(key) != 1 for key in self.__yaml['font']['replacements'].keys()):
                error(f'Font replacements of series "{self.name}" is invalid - must only be 1 character')
                self.valid = False
            else:
                self.font_replacements = self.__yaml['font']['replacements']

        if self.__is_specified('seasons', 'hide'):
            self.hide_seasons = bool(self.__yaml['seasons']['hide'])

        # Validate season map and episode range aren't specified at the same time
        if self.__is_specified('seasons') and self.__is_specified('episode_ranges'):
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
                    error(f'Episode range "{episode_range}" for series "{self.name}" '
                          f'is invalid - specify as "start-end"')
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
                                    the given attribute has attributes of its own.
        
        :returns:   True if specified, False otherwise.
        """

        current_level = self.__yaml
        for attribute in attributes:
            # If this level isn't even a dictionary, or the attribute doesn't exist
            if not isinstance(current_level, dict) or attribute not in current_level:
                return False

            if current_level[attribute] == None:
                return False

            # Move to the next level
            current_level = current_level[attribute]

        return True


    def _get_destination(self, data_row: dict) -> Path:
        """
        Get the destination filename for the given data row. The row's
        'season_number', and 'episode_number' keys are used.
        
        :param      data_row:   The data row returned from the file interface.
        
        :returns:   Path for the full title card destination
        """

        # If this show should not be written to a media directory, return 
        if not self.media_directory:
            return None

        # Read from data row
        try:
            season_number = int(data_row['season_number'])
            episode_number = int(data_row['episode_number'])
        except ValueError:
            error(f'Invalid season/episode number "{data_row["season_number"]},'
                  f' "{data_row["episode_number"]}"', 1)
            return None

        # Get the season folder corresponding to this episode's season
        if season_number == 0:
            season_folder = 'Specials'
        else:
            season_folder = f'Season {season_number}'

        # The standard plex filename for this episode
        # filename = preferences.card_filename_format.format(
        #     show=self.name, year=self.year, full_name=self.full_name,
        #     season=season_number, episode=episode_number,
        #     title=data_row['title'][0] + data_row['title'][1],
        # )
        # filename += TitleCard.OUTPUT_CARD_EXTENSION
        filename = (
            f'{self.full_name} - S{season_number:02}E{episode_number:02}'
            f'{TitleCard.OUTPUT_CARD_EXTENSION}'
        )

        return self.media_directory / season_folder / filename


    @staticmethod
    def strip_specials(text: str) -> str:
        """
        Remove all non A-Z characters from the given title.
        
        :param      text:   The title to strip of special characters.
        
        :returns:   The input `text` with all non A-Z characters removed.
        """

        return ''.join(filter(lambda c: match('[a-zA-Z0-9]', c), text)).lower()


    def read_source(self, sonarr_interface: 'SonarrInterface'=None) -> None:
        """
        Read the source file for this show, adding the associated Episode
        objects to this show's episodes dictionary.

        :param      sonarr_interface:   Optional SonarrInterface - currently
                                        not used.
        """

        for data_row in self.file_interface.read():
            key = f'{data_row["season_number"]}-{data_row["episode_number"]}'
            if key in self.episodes and self.episodes[key].matches(data_row):
                continue

            # Construct the file destination for Episode object building
            self.episodes[key] = Episode(
                base_source=self.source_directory,
                destination=self._get_destination(data_row),
                **data_row
            )

            # Attempt to use sonarr to figure out more accurate destination
            # if sonarr_interface and preferences.card_name_source == 'sonarr':
            #     episode_filename = sonarr_interface.get_episode_filename(
            #         self.name,
            #         self.year,
            #         episode.season_number,
            #         episode.episode_number,
            #     )

            #     # If the filename couldn't be gathered from Sonarr, None is returned
            #     if episode_filename:
            #         episode.destination = self.media_directory / episode_filename
            #     print('Sonarr found filename', episode.destination)

            # self.episodes[key] = episode


    def check_sonarr_for_new_episodes(self,
                                      sonarr_interface:'SonarrInterface')->bool:
        """
        Query the provided SonarrInterface object, checking if the returned
        episodes exist in this show's associated source. All new entries are
        added to this object's DataFileInterface.
        
        :param      sonarr_interface:   The Sonarr interface to query.

        :returns:   True if Sonarr returned any new episodes, False otherwise.
        """

        # This function is only called when sonarr is globally enabled
        if not self.sonarr_sync:
            return False

        # Refresh data from file interface
        self.read_source(sonarr_interface)

        # Get dict of episode data from Sonarr
        try:
            all_episodes = sonarr_interface.get_all_episodes_for_series(
                self.name, self.year
            )
        except ValueError:
            error(f'Cannot find series "{self.full_name}" in Sonarr', 1)
            return False

        # For each episode, check if the data matches any contained Episode objects
        has_new = False
        if all_episodes:
            for new_episode in all_episodes:
                # Compare against every Episode in this Show
                key = f'{new_episode["season_number"]}-{new_episode["episode_number"]}'
                if key in self.episodes and self.episodes[key].matches(new_episode):
                    continue

                # Construct data for new row
                has_new = True
                top, bottom = Episode.split_episode_title(new_episode.pop('title'))
                new_episode.update({'title_top': top, 'title_bottom': bottom})

                info(f'New episode for "{self.full_name}" '
                     f'S{new_episode["season_number"]:02}'
                     f'E{new_episode["episode_number"]:02}', 1)

                # Add entry to data file through interface
                self.file_interface.add_entry(**new_episode)

        # If new entries were added, re-parse source file
        if has_new:
            self.read_source()
            return True

        return False


    def create_missing_title_cards(self,
                                   tmdb_interface: 'TMDbInterface'=None) ->bool:
        """
        Creates any missing title cards for each episode of this show.

        :param      tmdb_interface: Optional interface to TMDb for attempting to
                                    download any source images that are missing.

        :returns:   True if any new cards were created, false otherwise.
        """

        # If the media directory is unspecified, then exit
        if self.media_directory is None:
            return False

        info(f'Creating Title Cards for Show "{self.full_name}"')

        # Go through each episode for this show
        created_new_cards = False
        for _, episode in self.episodes.items():
            # Skip episodes whose destination is None (don't create) or does exist
            if not episode.destination or episode.destination.exists():
                continue

            # Attempt to make a TitleCard object for this episode and profile
            try:
                title_card = TitleCard(episode, self.profile)
            except Exception as e:
                error(f'Error creating TitleCard ({e}) for episode ({episode})', 1)
                continue

            # If the title card source images doesn't exist..
            if not episode.source.exists():
                # Skip if cannot query database
                if not all((self.tmdb_sync, tmdb_interface)):
                    continue

                # Query database for image
                image_url = tmdb_interface.get_title_card_source_image(
                    self.name,
                    self.year,
                    episode.season_number,
                    episode.episode_number,
                    episode.abs_number,
                )

                # Skip if no image is returned
                if not image_url:
                    continue

                # Download the image
                tmdb_interface.download_image(image_url, episode.source)

            # Source exists, create the title card
            created_new_cards |= title_card.create()

        return created_new_cards

