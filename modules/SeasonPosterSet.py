from pathlib import Path
from typing import Any, Optional

from num2words import num2words
from re import compile as re_compile

from modules.Debug import log
import modules.global_objects as global_objects
from modules.SeasonPoster import SeasonPoster
from modules.YamlReader import YamlReader

class SeasonPosterSet(YamlReader):
    """
    This class defines a set of SeasonPoster objects for a single show.
    This class is initialized with via the season poster config, and
    mainly wraps the SeasonPoster object directly.
    """

    """Compiled regex to identify percentage values"""
    __PERCENT_REGEX = re_compile(r'^-?\d+\.?\d*%$')
    __PERCENT_REGEX_POSITIVE = re_compile(r'^\d+\.?\d*%$')

    """Regex to identify season number from poster filenames"""
    __SEASON_NUMBER_REGEX = re_compile(r'^season(\d+).jpg$')

    __slots__ = (
        'valid', 'font_file', 'font_color', 'font_kerning', 'posters',
        'font_size', '__source_directory', '__logo', 'has_posters',
        '__media_directory', 'logo_is_optional',
    )


    def __init__(self,
            episode_map: 'EpisodeMap', # type: ignore
            source_directory: Path,
            media_directory: Path,
            poster_config: Optional[dict[str, Any]] = None) -> None:
        """
        Construct a new instance of the set. This parses all YAML
        attributes, and looks for input poster images within the given
        source directory.

        Args:
            episode_map: EpisodeMap containing season titles.
            source_directory: Base source directory to look for the
                logo and season files at.
            media_directory: Base media directory to create season
                posters within.
            poster_config: Config from the container series' YAML.
        """

        # Initialize parent YamlReader
        poster_config = {} if poster_config is None else poster_config
        super().__init__(poster_config)

        # Assign default attributes
        self.font_color = SeasonPoster.SEASON_TEXT_COLOR
        self.font_file = SeasonPoster.SEASON_TEXT_FONT
        self.font_kerning = 1.0
        self.font_size = 1.0
        self.logo_is_optional = poster_config.get('omit_logo', False)

        # Future list of SeasonPoster objects
        self.posters = {}
        self.has_posters = False

        # Get all paths for this set
        self.__source_directory = source_directory
        self.__logo = source_directory / 'logo.png'
        self.__media_directory = media_directory

        # If posters aren't enabled, skip rest of parsing
        if media_directory is None or not poster_config.get('create', True):
            return None

        # Read the font specification
        self.__read_font()

        # Create SeasonPoster objects
        self.__prepare_posters(poster_config, episode_map)


    def __read_font(self) -> None:
        """
        Read this object's font config for this poster set, updating
        attributes and validity for each element.
        """

        # Exit if no config to parse
        if not self._is_specified('font'):
            return None

        if (file := self._get('font', 'file', type_=Path)) is not None:
            if file.exists():
                self.font_file = file
            else:
                log.error(f'Font file "{file}" is invalid, no font file found.')
                self.valid = False

        if (color := self._get('font', 'color',
                               type_=self.TYPE_LOWER_STR)) is not None:
            self.font_color = color

        if (kerning := self._get('font', 'kerning',
                                 type_=self.TYPE_LOWER_STR)) is not None:
            if bool(self.__PERCENT_REGEX.match(kerning)):
                self.font_kerning = float(kerning[:-1]) / 100.0
            else:
                log.error(f'Font kerning "{kerning}" is invalid, specify as "x%')
                self.valid = False

        if (size := self._get('font', 'size',
                              type_=self.TYPE_LOWER_STR)) is not None:
            if bool(self.__PERCENT_REGEX_POSITIVE.match(size)):
                self.font_size = float(size[:-1]) / 100.0
            else:
                log.error(f'Font size "{size}" is invalid, specify as "x%"')
                self.valid = False


    def __prepare_posters(self,
            poster_config: dict[str, Any],
            episode_map: 'EpisodeMap') -> None:
        """
        Create SeasonPoster objects for all available season poster
        images, using the given config.

        Args:
            season_config: The YAML config for this PosterSet.
            episode_map: EpisodeMap object containing custom defined
                season titles.
        """

        # Get all manually specified titles
        override_titles = poster_config.get('titles', {})
        specified_titles = episode_map.get_all_season_titles()

        # Get whether to spell or use digits for season numbers (default spell)
        spell = poster_config.get('spell_numbers', True)

        # Get whether to use top or bottom placement
        top_placement = poster_config.get('placement', 'bottom').lower() =='top'

        # Get whether to omit gradient and logo
        omit_gradient = poster_config.get('omit_gradient', False)
        omit_logo = poster_config.get('omit_logo', False)

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
            self.has_posters = True
            self.posters[season_number] = SeasonPoster(
                source=poster_file,
                destination=destination,
                logo=self.__logo,
                season_text=season_text,
                font=self.font_file,
                font_color=self.font_color,
                font_size=self.font_size,
                font_kerning=self.font_kerning,
                top_placement=top_placement,
                omit_gradient=omit_gradient,
                omit_logo=omit_logo,
            )


    def get_poster(self, season_number: int) -> Optional[Path]:
        """
        Get the path to the Poster from this set for the given season
        number.

        Args:
            season_number: Season number to get the poster of.

        Returns:
            Path to this set's poster for the given season. None if that
            poster does not exist.
        """

        # Return poster file if given season has poster that exists
        if ((poster := self.posters.get(season_number)) is not None
            and poster.destination.exists()):
            return poster.destination

        return None


    def create(self) -> None:
        """Create all season posters within this set."""

        # Warn and exit if logo DNE
        if (self.has_posters
            and (not self.logo_is_optional and not self.__logo.exists())):
            log.error(f'Cannot create season posters, logo file '
                      f'"{self.__logo.resolve()}" does not exist')
            return None

        # Go through each season poster within this set
        for poster in self.posters.values():
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

        return None