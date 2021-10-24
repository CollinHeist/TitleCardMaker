from csv import reader

class DataFileInterface:
    """
    This class is used to interface with a show's data file. 

    This can be used for reading from and writing to the files for the purpose of
    adding new episodes, or reading existing ones.
    """

    GENERIC_DATA_FILE_NAME: str = 'data.tsv'
    DELIMETER: str = '\t'

    def __init__(self, data_file: Path) -> None:
        """
        Constructs a new instance.
        """
        
        self.file = data_file
        self.__delimeter = delimiter 


    def read(self) -> list:
        """
        Reads a data file.
        
        :returns:   { description_of_the_return_value }
        :rtype:     None
        """
        
        with self.file.open('r') as file_handle:
            for row_number, row in enumerate(reader(file_handle, delimiter=self.DELIMETER)):
                if row_number == 0:
                    continue

                yield row

