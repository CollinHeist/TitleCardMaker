from csv import reader, writer
from pathlib import Path

from modules.Debug import *

class DataFileInterface:
    """
    This class is used to interface with a show's data file. 

    This can be used for reading from and writing to the files for the purpose of
    adding new or reading existing episodes.
    """

    GENERIC_DATA_FILE_NAME: str = 'data.tsv'
    DELIMETER: str = '\t'

    """String that indicates empty text in title text"""
    EMPTY_VALUE: str ='_EMPTY_'

    """Label headers found at the top of all data files"""
    GENERIC_HEADERS: list = [
        'title_top', 'title_bottom', 'season', 'episode', 'abs_number'
    ]

    def __init__(self, data_file: Path) -> None:
        """
        Constructs a new instance of the interface for the specified
        data file. Permits future reading and writing.
        """
        
        self.file = data_file


    def read(self) -> dict:
        """
        Reads a data file.
        
        :returns:   Yields from each row in the data file.
        """

        # Create an empty data file if nothing exists, then exit (no data to read)
        if not self.file.exists():
            info(f'Creating blank source file "{self.file.resolve()}"')
            self.create_new_data_file()
            return None
            
        # Start reading this interface's file, yielding each row (except headers)
        with self.file.open('r') as file_handle:
            for row_number, row in enumerate(reader(file_handle, delimiter=self.DELIMETER)):
                # Skip headers
                if row_number == 0:
                    continue

                # Skip invalid rows
                if len(row) < 4:
                    error(f'Row {row_number} of {self.file.resolve()} is '
                          f'invalid ({row})')
                    continue

                # Process EMPTY_VALUE text into blank text
                title_top = '' if row[0] == self.EMPTY_VALUE else row[0]
                title_bottom = '' if row[1] == self.EMPTY_VALUE else row[1]

                # Create dictionary for this row, add the abs_number if present
                row_dict = {
                    'title': (title_top, title_bottom),
                    'season_number': row[2],
                    'episode_number': row[3],
                }

                # Rows with the (optional) abs_number value have extra key
                if len(row) == 5:
                    row_dict['abs_number'] = row[4]

                yield row_dict


    def read_entries_without_absolute(self) -> dict:
        """
        Reads an entries without absolute.
        
        :returns:   { description_of_the_return_value }
        """

        # If the specified file doesn't exist, skip..
        if not self.file.exists():
            return {}

        # Iterate through each row in the file, yielding season/episode number
        with self.file.open('r') as file_handle:
            for row_number, row in enumerate(reader(file_handle, delimiter=self.DELIMETER)):
                # Skip headers
                if row_number == 0 or len(row) != 4:
                    continue

                # Create dictionary for this row, add the abs_number if present
                yield {
                    'row_number': row_number,
                    'title_top': row[0],
                    'title_bottom': row[1],
                    'season_number': int(row[2]),
                    'episode_number': int(row[3]),
                }


    def modify_entry(self, row_number: int, title_top: str, title_bottom: str,
                     season_number: int, episode_number: int,
                     abs_number: int=None) -> None:
        """
        { function_description }
        
        :param      row_number:      The row number
        :param      title_top:       The title top
        :param      title_bottom:    The title bottom
        :param      season_number:   The season number
        :param      episode_number:  The episode number
        :param      abs_number:      The absolute number
        """

        # Read current data
        with self.file.open('r') as file_handle:
            current = file_handle.readlines()

        # Construct row with new data
        row_list = [title_top, title_bottom, season_number, episode_number]
        if abs_number != None:
            row_list += [abs_number]

        # Change this row
        current[row_number] = self.DELIMETER.join(map(str, row_list)) + '\n'
        with self.file.open('w') as file_handle:
            file_handle.writelines(current)

        info(f'Modified line {row_number} to {row_list}')


    def add_entry(self, title_top: str, title_bottom: str, season_number: int,
                  episode_number: int, abs_number: int=None) -> None:
        """
        Add the info provided to this object's data file.

        :param      title_top:      Top line of the episode title text for
                                    the entry.

        :param      title_bottom:   Bottom line of the episode title text for
                                    the entry.

        :param      season_number:  Season number of the entry being added.

        :param      episode_number: Episode number of the entry being added.

        :param      abs_number:     Optional absolute number of the entry.
        """

        if not self.file.exists():
            self.create_new_data_file()

        # Ensure newline is added to end of file
        self.__add_newline()

        # Empty title text should be replaced with EMPTY_VALUE
        title_top = self.EMPTY_VALUE if title_top == '' else title_top
        title_bottom = self.EMPTY_VALUE if title_bottom == '' else title_bottom
        
        # Write new row
        with self.file.open('a', newline='') as file_handle:
            file_writer = writer(file_handle, delimiter=self.DELIMETER)

            # Construct new row
            row = [title_top, title_bottom, season_number, episode_number]
            row += [abs_number] if abs_number != None else []
            file_writer.writerow(row)


    def create_new_data_file(self) -> None:
        """
        Creates a new data file for this interface. This will construct the
        necessary parent folders, and exits if the file already exists. The
        generic headers are written to the first line of the file.
        """

        # Exit if the file already exists
        if self.file.exists():
            return

        # Make parent directory if it doesn't exist
        self.file.parent.mkdir(parents=True, exist_ok=True)

        # Write row of headers, then exit
        with self.file.open('w') as file_handle:
            file_writer = writer(file_handle, delimiter=self.DELIMETER)

            file_writer.writerow(self.GENERIC_HEADERS)


    def __add_newline(self) -> None:
        """
        Adds a newline if the datafile does not end in one. Ensures
        new rows are added correctly (and not appended to end of existing
        last row).
        """

        # Exit if the file doesnt' exist
        if not self.file.exists():
            return

        # Read existign content
        with self.file.open('r') as file_handle:
            existing = file_handle.read()

        # If the file ends without a newline character, add one
        if not existing.endswith('\n'):
            with self.file.open('a') as file_handle:
                file_handle.write('\n')


