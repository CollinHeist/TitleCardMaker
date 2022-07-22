from yaml import safe_load, dump
from pathlib import Path

from modules.Debug import log
from modules.EpisodeInfo import EpisodeInfo
import modules.global_objects as global_objects
from modules.Title import Title

class DataFileInterface:
    """
    This class is used to interface with a show's data file. And can be used for
    reading from and writing to the files for the purpose of adding new or
    reading existing episode data.
    """

    """Default name for a data file of episode information"""
    GENERIC_DATA_FILE_NAME = 'data.yml'


    def __init__(self, series_info: 'SeriesInfo', data_file: Path) -> None:
        """
        Constructs a new instance of the interface for the specified data file.
        This also creates the parent directories for the data file if they do
        not exist.

        :param      data_file:  Path to the data file to interface with.
        """
        
        # Store the SeriesInfo and data file
        self.series_info = series_info
        self.file = data_file

        # Create parent directories if necessary
        if not self.file.exists():
            data_file.parent.mkdir(parents=True, exist_ok=True)


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return (f'<DataFileInterface series_info={self.series_info}, '
                f'file={self.file.resolve()}>')


    def __read_data(self) -> dict:
        """
        Read this interface's data from file. Returns an empty dictionary if the
        file does not exist, is misformatted, or if 'data' key is missing.
        
        :returns:   Contents under 'data' key of this interface's file.
        """

        # If the file DNE, return empty dictionary
        if not self.file.exists():
            return {}

        # Read file 
        with self.file.open('r', encoding='utf-8') as file_handle:
            try:
                yaml = safe_load(file_handle)
            except Exception as e:
                log.error(f'Error reading datafile:\n{e}\n')
                return {}

        # If the top-level key is not 'data', error and return empty dictionary
        if 'data' not in yaml:
            log.error(f'Datafile "{self.file.resolve()}" missing "data" key')
            return {}

        return yaml['data']


    def __write_data(self, yaml: dict) -> None:
        """
        Write the given YAML data to this interface's file. This puts all data
        under the 'data' key.

        :param      yaml:   YAML dictionary to write to file.
        """

        # Write updated data with this entry added
        with self.file.open('w', encoding='utf-8') as file_handle:
            dump({'data': yaml}, file_handle, allow_unicode=True, width=100)


    def read(self) -> tuple[dict, set]:
        """
        Read the data file for this object, yielding each valid row.
        
        :returns:   Yields a dictionary for each entry in this datafile. The
                    dictionary has a key 'episode_info' with an EpisodeInfo
                    object, and arbitrary keys for all other data found within
                    the entry's YAML.
        """

        # Read yaml, returns {} if empty/DNE
        yaml = self.__read_data()

        # Iterate through each season
        for season, season_data in yaml.items():
            season_number = int(season.rsplit(' ', 1)[-1])

            # Iterate through each episode of this season
            for episode_number, episode_data in season_data.items():
                # If title is missing (or no subkeys at all..) error
                if (not isinstance(episode_data, dict)
                    or ('title' not in episode_data and
                        'preferred_title' not in episode_data)):
                    log.error(f'S{season_number:02}E{episode_number:02} of the '
                              f'{self.series_info} datafile is missing a title')
                    continue

                # Get existing keys for this episode
                given_keys = set(episode_data)

                # If translated title is available, prefer that
                original_title = episode_data.pop('title', None)
                title = episode_data.get('preferred_title', original_title)

                # Ensure Title can be created
                try:
                    title_obj = Title(title, original_title=original_title)
                    log.debug(f'Created {title_obj}')
                except Exception:
                    log.error(f'Title for S{season_number:02}E'
                              f'{episode_number:02} of the {self.series_info} '
                              f'datafile is invalid')
                    continue
                
                # Construct EpisodeInfo object for this entry
                episode_info = global_objects.info_set.get_episode_info(
                    self.series_info,
                    title_obj,
                    season_number,
                    episode_number,
                    episode_data.pop('abs_number', None),
                    tvdb_id=episode_data.pop('tvdb_id', None),
                    imdb_id=episode_data.pop('imdb_id', None),
                )

                # Add any additional, unexpected keys from the YAML
                data = {'episode_info': episode_info}
                data.update(episode_data)
                
                yield data, given_keys


    def add_data_to_entry(self, episode_info: EpisodeInfo,
                          **new_data: dict) -> None:
        """
        Add any generic data to the YAML entry associated with this EpisodeInfo.
        
        :param      episode_info:   Episode Info to add to YAML.
        :param      new_data:       Generic new data to write.
        """

        yaml = self.__read_data()

        # Verify this entry already exists, warn and exit if not
        season_key = f'Season {episode_info.season_number}'
        if (season_key not in yaml
            or episode_info.episode_number not in yaml[season_key]):
            log.error(f'Cannot add data to entry for {episode_info} in '
                      f'"{self.file.resolve()}" - entry does not exist')
            return None

        # Add new data
        yaml[season_key][episode_info.episode_number].update(new_data)

        # Write updated data
        self.__write_data(yaml)


    def add_many_entries(self, new_episodes: list['EpisodeInfo']) -> None:
        """
        Adds many entries at once. An episode is only added if an episode of
        that index does not already exist. This only reads and writes from this 
        interface's file once.

        :param      new_episodes:   List of EpisodeInfo objects to write.
        """

        # If no new episodes are being added, exit
        if len(new_episodes) == 0:
            return None

        # Read yaml
        yaml = self.__read_data()

        # Go through each episode to possibly add to file
        added = {'count': 0, 'info': None}
        for episode_info in new_episodes:
            # Create blank season data if this key doesn't exist
            season_key = f'Season {episode_info.season_number}'
            if season_key not in yaml:
                yaml[season_key] = {}

            # If this episde already exists, skip
            if episode_info.episode_number in yaml[season_key]:
                continue

            # Construct episode data
            added = {'count': added['count'] + 1, 'info': episode_info}
            yaml[season_key][episode_info.episode_number] = {
                'title': episode_info.title.title_yaml
            }

            # Add absolute number if given
            if episode_info.abs_number is not None:
                yaml[season_key][episode_info.episode_number]['abs_number'] =\
                    episode_info.abs_number

        # If nothing was added, exit
        if (count := added['count']) == 0:
            return None
        
        # Log add operations to user
        if count > 1:
            log.info(f'Added {count} episodes to "{self.file.parent.name}"')
        else:
            log.info(f'Added {added["info"]} to "{self.file.parent.name}"')

        # Write updated yaml
        self.__write_data(yaml)

