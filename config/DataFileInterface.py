from csv import reader, writer
from pathlib import Path

from Debug import *

class DataFileInterface:
    """
    This class is used to interface with a show's data file. 

    This can be used for reading from and writing to the files for the purpose of
    adding new episodes, or reading existing ones.
    """

    GENERIC_DATA_FILE_NAME: str = 'data.tsv'
    DELIMETER: str = '\t'

    """String that indicates empty text in title text."""
    EMPTY_VALUE: str ='_EMPTY_'

    def __init__(self, data_file: Path) -> None:
        """
        Constructs a new instance of the interface for the specified
        data file. Permits future reading and writing.
        """
        
        self.file = data_file


    def read(self) -> list:
        """
        Reads a data file.
        
        :returns:   Yields from each row in the data file.
        """

        if not self.file.exists():
            raise FileNotFoundError(f'Source file "{self.data_file.resolve()}" does not exist')
        
        with self.file.open('r') as file_handle:
            for row_number, row in enumerate(reader(file_handle, delimiter=self.DELIMETER)):
                if row_number == 0:
                    continue

                title_top = row[0] if row[0] != self.EMPTY_VALUE else ''
                title_bottom = row[1] if row[1] != self.EMPTY_VALUE else ''

                yield {
                    'title': (title_top, row[1]),
                    'season_number': row[2],
                    'episode_number': row[3],
                }


    def add_entry(self, title_top: str, title_bottom: str,
                  season_number: int, episode_number: int) -> None:
        """
        Add the info provided to this object's data file.
        """

        if not self.file.exists():
            raise FileNotFoundError(f'Source file "{self.data_file.resolve()}" does not exist')

        # Ensure newline is added to end of file
        self.__add_newline()

        # Empty top line should be replaced with empty text
        title_top = self.EMPTY_VALUE if title_top == '' else title_top
        
        # Write new row
        with self.file.open('a', newline='') as file_handle:
            file_writer = writer(file_handle, delimiter=self.DELIMETER)

            # Construct new row
            row = [title_top, title_bottom, season_number, episode_number]
            file_writer.writerow(row)


    def __add_newline(self) -> None:
        """
        Adds a newline if the datafile does not end in one. Ensures
        new rows are added correctly.
        """

        if not self.file.exists():
            return

        with self.file.open('r') as file_handle:
            stuff = file_handle.read()

        if not stuff.endswith('\n'):
            with self.file.open('a') as file_handle:
                file_handle.write('\n')


