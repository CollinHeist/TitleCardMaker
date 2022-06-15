from pathlib import Path

from num2words import num2words
from re import compile as re_compile

from modules.Debug import log
import modules.global_objects as global_objects
from modules.SeasonPoster import SeasonPoster

class SeasonPosterSet:
    """
    This class defines a set of SeasonPoster objects for a single show. This
    class is initialized with via the season poster config, and mainly wraps the
    SeasonPoster object directly.
    """

    """Compiled regex to identify percentage values"""
    __PERCENT_REGEX = re_compile(r'^-?\d+\.?\d*%$')
    __PERCENT_REGEX_POSITIVE = re_compile(r'^\d+\.?\d*%$')

    """Regex to identify season number from poster filenames"""
    __SEASON_NUMBER_REGEX = re_compile(r'^season(\d+).jpg$')

    __slots__ = ('valid', 'font_file', 'font_color', 'font_kerning','font_size',
                 'posters', '__source_directory', '__logo', '__media_directory')
    

    def __init__(self, episode_map: 'EpisodeMap', source_directory: Path,
                 media_directory: Path, poster_config: dict=None) -> None:
        """
        Construct a new instance of the set. This parses all YAML attributes,
        and looks for input poster images within the given source directory.
        
        :param      episode_map:        EpisodeMap containing season titles.
        :param      source_directory:   Base source directory to look for the
                                        logo and season files at.
        :param      media_directory:    Base media directory to create season
                                        posters within.
        :param      poster_config:      Config from the container series' YAML.
        """

        # Assign default attributes
        self.valid = True
        self.font_file = SeasonPoster.SEASON_TEXT_FONT
        self.font_color = SeasonPoster.SEASON_TEXT_COLOR
        self.font_kerning = 1.0
        self.font_size = 1.0

        # Future list of SeasonPoster objects
        self.posters = []

        # Get all paths for this set
        self.__source_directory = source_directory
        self.__logo = source_directory / 'logo.png'
        self.__media_directory = media_directory
        
        # If posters aren't enabled, skip rest of parsing
        poster_config = {} if poster_config is None else poster_config
        if (self.__media_directory is None
            or not poster_config.get('create', True)):
            return None

        #  Read the font specification
        self.__read_font(poster_config.get('font', {}))

        # Create SeasonPoster objects
        self.__prepare_posters(poster_config, episode_map)


    def __read_font(self, font_config: dict) -> None:
        """
        Read the given font config for this poster set.
        
        :param      font_config:    The specified font configuration to read.
        """

        # Exit if no config to parse
        if font_config == {}:
            return None

        if (file := font_config.get('file')) != None:
            if Path(file).exists():
                self.font_file = Path(file)
            else:
                log.error(f'Font file "{file}" is invalid, no font file found.')
                self.valid = False

        if (color := font_config.get('color')) != None:
            if (not isinstance(color, str)
                or not bool(match('^#[a-fA-F0-9]{6}$', color))):
                log.error(f'Font color "{color}" is invalid, specify as '
                          f'"#xxxxxx"')
            else:
                self.font_color = color

        if (kerning := font_config.get('kerning')) != None:
            if (not isinstance(kerning, str)
                or not bool(self.__PERCENT_REGEX.match(kerning))):
                log.error(f'Font kerning "{kerning}" is invalid, specify as "x%')
            else:
                self.font_kerning = float(kerning[:-1]) / 100.0

        if (size := font_config.get('size')) != None:
            if (not isinstance(size, str)
                or not bool(self.__PERCENT_REGEX_POSITIVE.match(size))):
                log.error(f'Font size "{size}" is invalid, specify as "x%"')
                self.valid = False
            else:
                self.font_size = float(size[:-1]) / 100.0


    def __prepare_posters(self, poster_config: dict,
                          episode_map: 'EpisodeMap') -> None:
        """
        Create SeasonPoster objects for all available season poster images,
        using the given config.
        
        :param      season_config:  The YAML config for this PosterSet.
        :param      episode_map:    EpisodeMap object containing custom defined
                                    season titles.
        """

        # Get all manually specified titles
        override_titles = poster_config.get('titles', {})
        specified_titles = episode_map.get_all_season_titles()

        # Get whether to spell or use digits for season numbers (default spell)
        spell = poster_config.get('spell_numbers', True)

        # Get all the season posters that exist in the source directory
        for poster_file in self.__source_directory.glob('season*.jpg'):
            # Skip files named season*.jpg that aren't numbered
            if self.__SEASON_NUMBER_REGEX.match(poster_file.name) is None:
                log.debug(f'Not creating season poster for '
                          f'"{poster_file.resolve()}"')
                continue

            # Get season number from the file
            season_number = int(self.__SEASON_NUMBER_REGEX.match(
                poster_file.name
            ).group(1))

            # Get destination file
            season_folder = global_objects.pp.get_season_folder(season_number)
            filename = f'Season{season_number}.jpg'
            destination = self.__media_directory / season_folder / filename

            # Get season title for this poster
            if (text := (specified_titles |override_titles).get(season_number)):
                season_text = text
            elif season_number == 0:
                season_text = 'Specials'
            elif spell:
                season_text = f'Season {num2words(season_number)}'
            else:
                season_text = f'Season {season_number}'

            # Create SeasonPoster list
            self.posters.append(SeasonPoster(
                source=poster_file,
                logo=self.__logo,
                destination=destination,
                season_text=season_text,
                font=self.font_file,
                font_color=self.font_color,
                font_size=self.font_size,
                font_kerning=self.font_kerning,
            ))


    def create(self) -> None:
        """Create all season posters within this set."""

        # Warn and exit if logo DNE
        if len(self.posters) > 1 and not self.__logo.exists():
            log.error(f'Cannot create season posters, logo file '
                      f'"{self.__logo.resolve()}" does not exist')

        # Go through each season poster within this set
        for poster in self.posters:
            # Skip if poster file already exists
            if poster.destination.exists():
                continue

            # Create season poster
            poster.create()

            # Log results
            if poster.destination.exists():
                log.debug(f'Created poster "{poster.destination.resolve()}"')
            else:
                log.debug(f'Could not create poster '
                          f'"{poster.destination.resolve()}"')
                poster.image_magick.print_command_history()

