from pathlib import Path

from Debug import *
from TitleCardMaker import TitleCardMaker
from TitleCardProfile import TitleCardProfile

class TitleCard:

    SOURCE_EXTENSION: str = 'jpg'

    EMPTY_TEXT: str = '_EMPTY_'

    def __init__(self, data_row: list, media_directory: Path,
                 source_directory: Path, profile: TitleCardProfile) -> None:

        # Parse each entry of the row from the CSV file
        self.title_line1 = data_row[1]
        self.title_line2 = data_row[2] if data_row[2] != self.EMPTY_TEXT else None
        self.season_number = int(data_row[3])
        self.episode_number = int(data_row[4])

        if self.season_number == 0:
            self.__output_structure = [Path(media_directory.stem), Path('Specials') / data_row[0]]
            self.output_path = media_directory / 'Specials' / data_row[0]
        else:
            self.__output_structure = [Path(media_directory.stem), Path(f'Season {self.season_number}') / data_row[0]]
            self.output_path = media_directory / f'Season {self.season_number}' / data_row[0]

        # This title card's input path will be s1e1, s1e2, etc.
        file = f's{self.season_number}e{self.episode_number}.{self.SOURCE_EXTENSION}'
        self.input_path = source_directory / file

        # Whether or not the ouput title card already exists
        self.exists = self.output_path.exists()

        # Instantiate a tile card maker for this card
        self.title_card_maker = TitleCardMaker(
            self.input_path,
            self.output_path,
            self.title_line1,
            self.title_line2,
            **profile.get_title_card_maker_args(self.season_number, self.episode_number),
        )


    def __repr__(self) -> str:
        """
        Returns a unambiguous string representation of the object (for debug).
        
        :returns:   String representation of the object.
        """
        
        return (f'<TitleCard at "{self.output_path.resolve()}" for Season '
            f'{self.season_number}, Episode {self.episode_number} : '
            f'"{self.title_line2}" // "{self.title_line1}" that does'
            f'{"" if self.exists else " NOT"} exist>')


    def create(self) -> None:
        if self.exists:
            info(f'Title Card {self.output_path} already exists')
            return

        if not self.input_path.exists():
            warn(f'Source image {self.input_path.resolve()} does not exist')
            return

        info(f'Creating title card for {self.output_path.name}')
        self.title_card_maker.create()


        