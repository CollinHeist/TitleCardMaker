from yaml import safe_load, dump
from pathlib import Path

from modules.Debug import log
from modules.EpisodeInfo import EpisodeInfo
from modules.Title import Title

class DataFileInterface:
    """
    This class is used to interface with a show's data file. And can be used for
    reading from and writing to the files for the purpose of adding new or
    reading existing episode data.
    """

    """Default name for a data file of episode information"""
    GENERIC_DATA_FILE_NAME: str = 'data.yml'


    def __init__(self, data_file: Path) -> None:
        """
        Constructs a new instance of the interface for the specified data file.

        :param      data_file:  Path to the data file to interface with.
        """
        
        # Store the data file for future use
        self.file = data_file


    def __repr__(self) -> str:
        """Returns a unambiguous string representation of the object."""

        return f'<DataFileInterface data_file={self.file.resolve()}>'


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
        with self.file.open('r') as file_handle:
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
        Write the given YAML data to this interface's file. Created parent
        directories if they do not exist, and puts all data under 'data' key.

        :param      yaml:   YAML dictionary to write to file.
        """

        # Create parent directories if necessary
        self.file.parent.mkdir(parents=True, exist_ok=True)

        # Write updated data with this entry added
        with self.file.open('w') as file_handle:
            dump({'data': yaml}, file_handle, allow_unicode=True, width=100)


    def sort_and_write(self, yaml: dict) -> None:
        """
        Sort the given YAML and then write it to this interface's file. Sorting
        is done by season number, and then episode number, and then by info key.

        :param      yaml:   YAML dictionary to sort and write to file.
        """

        # Sort dictionary by season number
        sorted_yaml = {}
        for season in sorted(yaml, key=lambda k: int(k.split(' ')[-1])):
            # Sort each season by episode number
            sorted_yaml[season] = {}
            for episode in sorted(yaml[season]):
                # Sort each episode by key
                sorted_yaml[season][episode] = {}
                for key in sorted(yaml[season][episode]):
                    sorted_yaml[season][episode][key]=yaml[season][episode][key]
                    
        # Write newly sorted YAML
        self.__write_data(yaml)


    def read(self) -> dict:
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
                # If the 'title' key is missing (or no subkeys at all..) error
                if ('title' not in episode_data
                    or not isinstance(episode_data, dict)):
                    log.error(f'Season {season_number}, Episode {episode_number}'
                              f' of "{self.file.resolve()}" is missing title')
                    continue

                # Construct EpisodeInfo object for this entry
                episode_info = EpisodeInfo(
                    Title(episode_data.pop('title')),
                    season_number,
                    episode_number,
                    episode_data.pop('abs_number', None)
                )

                # Add any additional, unexpected keys from the YAML
                data = {'episode_info': episode_info}
                data.update(episode_data)
                
                yield data


    def read_entries_without_absolute(self) -> dict:
        """
        Read and yield all entries without absolute episode numbers.
        
        :returns:   Yields an iterable of dictionaries for entry without an 
                    absolute episode number. 
        """

        # Read yaml, returns {} if empty/DNE
        yaml = self.__read_data()

        # Iterate through entries, yielding if no absolute number
        for season, season_data in yaml.items():
            season_number = int(season.rsplit(' ', 1)[-1])

            # Iterate through each episode of this season
            for episode_number, episode_data in season_data.items():
                # Skip if this entry has an absolute number
                if 'abs_number' in episode_data:
                    continue

                # Create EpisodeInfo object for this entry
                episode_info = EpisodeInfo(
                    Title(episode_data.pop('title')),
                    season_number,
                    episode_number,
                )

                # Add any additional, unexpected keys from the YAML
                data = {'episode_info': episode_info}
                data.update(episode_data)

                yield data


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


    def add_many_entries(self, new_episodes: ['EpisodeInfo']) -> None:
        """
        Adds many entries at once. This only reads and writes from this 
        interface's file once.

        :param      new_episodes:   List of EpisodeInfo objects to write.
        """

        # Read yaml
        yaml = self.__read_data()

        for episode_info in new_episodes:
            # Indicate new episode to user
            log.info(f'Added {episode_info} to "{self.file.parent.name}"')

            # Create blank season data if this key doesn't exist
            season_key = f'Season {episode_info.season_number}'
            if season_key not in yaml:
                yaml[season_key] = {}

            # If this episde already exists, skip
            if episode_info.episode_number in yaml[season_key]:
                continue

            # Construct episode data
            yaml[season_key][episode_info.episode_number] = {
                'title': episode_info.title.title_yaml
            }

            # Add absolute number if given
            if episode_info.abs_number != None:
                yaml[season_key][episode_info.episode_number]['abs_number'] =\
                    episode_info.abs_number

        # Write updated yaml
        self.sort_and_write(yaml)

