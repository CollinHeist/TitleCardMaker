from pathlib import Path
from re import match

from modules.DataFileInterface import DataFileInterface
from modules.Debug import *
from modules.Episode import Episode
from modules.Profile import Profile
from modules.TitleCard import TitleCard

class Show:
    """
    This class describes a show. A Show is initialzied by a <show> XML element, and
    is given a base source and media path. The show then encapsulates those
    attributes, as well as permitting operations for this show's episodes.
    """

    def __init__(self, show_element: 'Element', source: Path, media: Path,
                 library_name: str=None) -> None:

        """
        Constructs a new instance.
        
        :param      show_element:   The show element to parse for creation details.

        :param      source:         The base source directory - source images will
                                    be searched in a subfolder for this show.

        :param      media:          The base media directory to place created title
                                    cards at.

        :param      library_name:   Name of the media libary within Plex.
        """

        # Parse <show name="..."> attribute
        self.name = show_element.attrib['name']

        # Parse <show year="..."> attribute
        self.year = int(show_element.attrib['year'])

        # Full name is name (year)
        self.full_name = f'{self.name} ({self.year})'

        # Parse <show season_count="..."> attribute
        self.season_count = int(show_element.attrib['seasons'])

        # Parse <show/season_map> element (if present)
        # Parse <season_map> tag (if present) - default is 1:Season 1, 2:Season 2, etc.
        self.season_map = {n: f'Season {n}' for n in range(1, self.season_count+1)}
        self.season_map.update({0: 'Specials'})

        for season in show_element.findall('season_map/'):
            self.season_map.update({
                int(season.attrib['number']): season.attrib['name']
            })

        # Parse <profile> tag (if present) into a Profile object
        self.profile = Profile(
            show_element.find('profile'),
            show_element.find('font'),
            self.season_map,
        )

        self.library = library_name if library_name else media.name
        self.source_directory = source / self.full_name
        self.media_directory = media / self.full_name

        # Create this show's interface to it's data file
        self.file_interface = DataFileInterface(
            self.source_directory / DataFileInterface.GENERIC_DATA_FILE_NAME
        )

        # A transparent logo for use by a `ShowSummary` object.
        self.logo = self.source_directory / 'logo.png'

        # Create empty set of Episode objects
        self.episodes = {}


    def __repr__(self) -> str:
        """
        Returns a unambiguous string representation of the object (for debug...).
        
        :returns:   String representation of the object.
        """

        return (
            f'<Show full_name={self.full_name}, season_map={self.season_map}'
            f', profile={self.profile}, episodes={self.episodes}>'
        )


    @staticmethod
    def strip_specials(text: str) -> str:
        """
        Remove all non A-Z characters from the given title.
        
        :param      text:   The title to strip of special characters.
        
        :returns:   The input `text` with all non A-Z characters removed.
        """

        return ''.join(filter(lambda c: match('[a-zA-Z0-9]', c), text))


    def _get_destination(self, data_row: dict) -> Path:
        """
        Get the destination filename for the given data row. The row's
        'season_number', and 'episode_number' keys are used.
        
        :param      data_row:   The data row returned from the file interface.
        
        :returns:   Path for the full title card destination
        """

        # Read from data row
        season_number = int(data_row['season_number'])
        episode_number = int(data_row['episode_number'])

        # Get the season folder corresponding to this episode's season
        season_folder = 'Specials' if season_number == 0 else f'Season {season_number}'

        # The standard plex filename for this episode
        filename = (
            f'{self.full_name} - S{season_number:02}E{episode_number:02}{TitleCard.OUTPUT_CARD_EXTENSION}'
        )

        return self.media_directory / season_folder / filename


    def read_source(self) -> None:
        """
        Read the source file for this show, creating the associated Episode
        objects.
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


    def check_sonarr_for_new_episodes(self,
                                      sonarr_interface: 'SonarrInterface') -> bool:
        """
        Query the provided SonarrInterface object, checking if the returned
        episodes exist in this show's associated source. All new entries are
        added to this object's DataFileInterface.
        
        :param      sonarr_interface:   The Sonarr interface to query.

        :returns:   Whether or not Sonarr returned any new episodes.
        """

        # Refresh data from file interface
        self.read_source()

        # Get dict of episode data from Sonarr
        try:
            all_episodes = sonarr_interface.get_all_episodes_for_series(self.name, self.year)
        except ValueError:
            error(f'Cannot find series "{self.full_name}" in Sonarr')
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

                info(f'Sonarr indicates new episode ({new_episode})')

                # Add entry to data file through interface
                self.file_interface.add_entry(**new_episode)

        # If new entries were added, re-parse source file
        if has_new:
            self.read_source()
            return True

        return False


    def create_missing_title_cards(self,
                                   database_interface: 'DatabaseInterface'=None) -> bool:
        """
        Creates any missing title cards for each episode of this show.

        :param      database_interface: Optional interface to TMDb for attempting
                                        to download any source images that are
                                        missing.

        :returns:   True if any new cards were created, false otherwise.
        """

        info(f'Processing Show "{self.full_name}"')
        created_new_cards = False

        # Go through each episode for this show
        for _, episode in self.episodes.items():
            try:
                title_card = TitleCard(episode, self.profile)
            except Exception as e:
                error(f'Error creating TitleCard ({e}) for episode ({episode})', 1)
                continue

            # If the title card source image doesn't exist, attempt to download it
            if not episode.source.exists():
                # Already queried the database, skip
                if not episode.in_database:
                    continue
                    
                # If a DatabaseInterface is provided, query for this episode's source image
                if database_interface:
                    image_url = database_interface.get_title_card_source_image(
                        self.name,
                        self.year,
                        episode.season_number,
                        episode.episode_number,
                        episode.abs_number,
                    )

                    if image_url is None:
                        episode.in_database = False
                        continue
                    else:
                        database_interface.download_image(image_url, episode.source)

            # Source exists, create the title card
            created_new_cards |= title_card.create()

        return created_new_cards



