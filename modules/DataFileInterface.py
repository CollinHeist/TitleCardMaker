from yaml import safe_load, dump
from pathlib import Path

from modules.Debug import info, warn, error
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
                error(f'Error reading datafile:\n{e}\n')
                return {}

        # If the top-level key is not 'data', error and return empty dictionary
        if 'data' not in yaml:
            error(f'Datafile "{self.file.resolve()}" missing "data" key')
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
            dump({'data': yaml}, file_handle)


    def read(self) -> dict:
        """
        Read the data file for this object, yielding each (valid) row.
        
        :returns:   Yields from each row in the data file as a dictionary. The
                    keys are 'title', 'season_number', 'episode_number', and
                    'abs_number' (if present).
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
                    error(f'Season {season_number}, Episode {episode_number} of'
                          f' "{self.file.resolve()}" is missing title')
                    continue

                # Construct data dictionary of this object
                data = {
                    'title': Title(episode_data.pop('title')),
                    'season_number': season_number,
                    'episode_number': episode_number,
                }

                # Add any additional, unexpected keys from the YAML
                data.update(episode_data)

                yield data


    def read_entries_without_absolute(self) -> dict:
        """
        Read and yield all entries without absolute episode numbers.
        
        :returns:   Yields an iterable of dictionaries for entry without an 
                    absolute episode number. The keys are 'title',
                    'season_number', and 'episode_number'.
        """

        # Read yaml, returns {} if empty/DNE
        yaml = self.__read_data()

        # Iterate through entries, yielding if no absolute number
        for season, season_data in yaml.items():
            season_number = int(season.rsplit(' ', 1)[-1])

            # Iterate through each episode of this season
            for episode_number, episode_data in season_data.items():
                if 'abs_number' not in episode_data:
                    yield {
                        'title': Title(episode_data['title']),
                        'season_number': season_number,
                        'episode_number': episode_number,
                    }


    def modify_entry(self, title: Title, season_number: int,
                     episode_number: int, abs_number: int=None) -> None:
        """
        Modify the entry found under the given season+episode number to the
        specified information. If the entry does not exist, a new entry is NOT
        created.

        :param      title:          Title of the entry
        :param      season_number:  Season number of the entry.
        :param      episode_number: Episode number of the entry.
        :param      abs_number:     Absolute episode number of the entry.
        """

        # Read yaml, returns {} if empty/DNE
        yaml = self.__read_data()

        # Verify this entry already exists, warn and exit if not
        season_key = f'Season {season_number}'
        if (season_key not in yaml or 
            episode_number not in yaml[season_key]):
            warn(f'Cannot modify entry for Season {season_number}, Episode ',
                 f'{episode_number} in "{self.file.resolve()}" - entry does not'
                 f' exist')
            return None

        # Update this entry with the new title(s)
        yaml[season_key][episode_number]= {'title': title.title_yaml}
        if abs_number != None:
            yaml[season_key][episode_number]['abs_number'] = abs_number

        # Write updated data
        self.__write_data(yaml)


    def add_entry(self, title: Title, season_number: int,
                  episode_number: int, abs_number: int=None) -> None:
        """
        Add the info provided to this object's data file. If the specified
        season+episode number already exists, that data is NOT overwritten.

        :param      title_top:      Title of the entry being added.
        :param      season_number:  Season number of the entry being added.
        :param      episode_number: Episode number of the entry being added.
        :param      abs_number:     The absolute episode number of the entry.
        """

        # Read yaml, returns {} if empty/DNE
        yaml = self.__read_data()

        # Create blank season data under this key if it doesn't already exist
        season_key = f'Season {season_number}'
        if season_key not in yaml:
            yaml[season_key] = {}

        # If this episode already exists for this season, warn and exit
        if episode_number in yaml[season_key]:
            warn(f'Cannot add duplicate entry for Season {season_number}, '
                 f'Episode {episode_number} in "{self.file.resolve()}"')
            return None

        # Construct episode data
        yaml[season_key][episode_number] = {'title': title.title_yaml}

        # Add absolute number if given, add key
        if abs_number != None:
            yaml[season_key][episode_number]['abs_number'] = abs_number

        # Write updated data
        self.__write_data(yaml)

        

