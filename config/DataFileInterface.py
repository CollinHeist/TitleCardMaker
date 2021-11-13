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

    GENERIC_HEADERS: list = ['title_top', 'title_bottom', 'season', 'episode']

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
            warn(f'Source file "{self.file.resolve()}" does not exist - creating blank')
            self.create_new_data_file()
            return
            
        # Start reading this interface's file, yielding each row (except headers)
        with self.file.open('r') as file_handle:
            for row_number, row in enumerate(reader(file_handle, delimiter=self.DELIMETER)):
                # Skip headers
                if row_number == 0:
                    continue

                # Skip invalid rows
                if len(row) != 4:
                    error(f'Row {row_number} of {self.file.resolve()} is invalid ({row})')
                    continue

                # Process EMPTY_VALUE text into blank text
                title_top = '' if row[0] == self.EMPTY_VALUE else row[0]
                title_bottom = '' if row[1] == self.EMPTY_VALUE else row[1]

                yield {
                    'title': (title_top, title_bottom),
                    'season_number': row[2],
                    'episode_number': row[3],
                }


    def add_entry(self, title_top: str, title_bottom: str,
                  season_number: int, episode_number: int) -> None:
        """
        Add the info provided to this object's data file.
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
            file_writer.writerow(row)


    def create_new_data_file(self) -> None:
        """
        Creates a new data file.
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

        if not self.file.exists():
            return

        with self.file.open('r') as file_handle:
            existing = file_handle.read()

        if not existing.endswith('\n'):
            with self.file.open('a') as file_handle:
                file_handle.write('\n')


