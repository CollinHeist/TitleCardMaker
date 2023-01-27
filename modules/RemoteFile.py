from pathlib import Path

from requests import get
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential
from tinydb import TinyDB, where

from modules.Debug import log
import modules.global_objects as global_objects

class RemoteFile:
    """
    This class describes a RemoteFile. A RemoteFile is a file that is loaded
    from the TCM Card Types repository, and is necessary to allow card types to
    utilize non-standard files that can be downloaded at runtime alongside
    CardType classes. This class has no real executable methods, and
    upon initialization attempts to download the remote file if it DNE.
    """

    """Base URL to look for remote content at"""
    BASE_URL = ('https://github.com/CollinHeist/TitleCardMaker-CardTypes/'
                'raw/master')

    """Temporary directory all files will be downloaded into"""
    TEMP_DIR = Path(__file__).parent / '.objects'

    """Database of assets that have been loaded already"""
    LOADED_FILE = 'remote_assets.json'

    __slots__ = ('loaded', 'remote_source', 'local_file', 'valid')


    def __init__(self, username: str, filename: str) -> None:
        """
        Construct a new RemoteFile object. This downloads the file for the given
        user and file into the temporary directory of the Maker.

        Args:
            username: Username containing the file.
            filename: Filename of the file within the user's folder to download.
        """

        # Object validity to be updated
        self.valid = True

        # Get database of loaded assets
        database_directory = global_objects.pp.database_directory
        self.loaded = TinyDB(database_directory / self.LOADED_FILE)

        # Remote font will be stored at github/username/filename
        self.remote_source = f'{self.BASE_URL}/{username}/{filename}'

        # The font fill will be downloaded and exist in the temporary directory
        self.local_file = self.TEMP_DIR / username / filename.rsplit('/')[-1]

        # Create parent folder structure if necessary
        self.local_file.parent.mkdir(parents=True, exist_ok=True)

        # If file has already been loaded this run, skip
        if self.loaded.get(where('remote') == self.remote_source) is not None:
            return None

        # Download the remote file for local use
        try:
            self.download()
            log.debug(f'Downloaded RemoteFile "{username}/{filename}"')
            try:
                self.loaded.insert({'remote': self.remote_source})
            except Exception:
                pass
        except Exception as e:
            self.valid = False
            log.error(f'Could not download RemoteFile "{username}/{filename}", '
                      f'returned "{e}"')


    def __str__(self) -> str:
        """
        Returns a string representation of the object. This is just the complete
        filepath for the locally downloaded file.
        """

        return str(self.local_file.resolve())


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return (f'<RemoteFile remote_source={self.remote_source}, local_file='
                f'{self.local_file}, valid={self.valid}>')


    def resolve(self) -> Path:
        """
        Get the absolute path of the locally downloaded file.

        Returns:
            Path to the locally downloaded file.
        """

        return self.local_file.resolve()


    @retry(stop=stop_after_attempt(3),
           wait=wait_fixed(3)+wait_exponential(min=1, max=16))
    def __get_remote_content(self) -> 'Response':
        """
        Get the content at the remote source.

        Returns:
            Response object from this object's remote source.
        """

        return get(self.remote_source)


    def download(self):
        """
        Download the specified remote file from the TCM CardTypes github, and
        write it to a temporary local file.

        Raises:
            AssertionError if the Response is not OK; Exception if there is some
            uncaught error.
        """

        # Download remote file
        content = self.__get_remote_content()

        # Verify content is valid
        assert content.ok, 'File does not exist'

        # Write content to file
        with self.local_file.open('wb') as file_handle:
            file_handle.write(content.content)


    @staticmethod
    def reset_loaded_database(database_directory: Path) -> None:
        """
        Reset (clear) this class's database of loaded remote files.

        Args:
            database_directory: Base Path to read/write any databases from.
        """

        database_file = database_directory / RemoteFile.LOADED_FILE
        database = TinyDB(database_file)

        try:
            # Remove all records
            database.truncate()
        except Exception:
            # Misformed databases can cause read errors
            database_file.unlink(missing_ok=True)
            pass