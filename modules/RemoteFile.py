from pathlib import Path

from requests import get
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential

from modules.Debug import log
from tinydb import TinyDB, where

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

    """List of assets that have been loaded already"""
    LOADED_FILE = TEMP_DIR / 'remote_assets.json'
    LOADED = TinyDB(LOADED_FILE, create_dirs=True)


    def __init__(self, username: str, filename: str) -> None:
        """
        Construct a new RemoteFile object. This downloads the file for the given
        user and file into the temporary directory of the Maker.
        
        :param      username:   Username containing the file.
        :param      filename:   Filename of the file within the user's folder
                                to download.
        """
        
        # Remote font will be stored at github/username/filename
        self.remote_source = f'{self.BASE_URL}/{username}/{filename}'

        # The font fill will be downloaded and exist in the temporary directory
        self.local_file = self.TEMP_DIR / username / filename.rsplit('/')[-1]

        # Create parent folder structure if necessary
        self.local_file.parent.mkdir(parents=True, exist_ok=True)

        # If file has already been loaded this run, skip
        if self.LOADED.get(where('remote') == self.remote_source) is not None:
            return None

        # Download the remote file for local use
        try:
            self.download()
            log.debug(f'Downloaded RemoteFile "{username}/{filename}"')
            try:
                self.LOADED.insert({'remote': self.remote_source})
            except Exception:
                pass
        except Exception as e:
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

        return f'<RemoteFile {self.remote_source=}, {self.local_file=}>'


    def resolve(self) -> Path:
        """
        Get the absolute path of the locally downloaded file.
        
        :returns:   Path to the locally downloaded file.
        """

        return self.local_file.resolve()


    @retry(stop=stop_after_attempt(3),
           wait=wait_fixed(3)+wait_exponential(min=1, max=16))
    def __get_remote_content(self) -> bytes:
        """
        Get the content at the remote source.

        :returns:   Bytes of the remote content
        """

        return get(self.remote_source).content


    def download(self):
        """
        Download the specified remote file from the TCM CardTypes github, and
        write it to a temporary local file.
        """

        # Download remote file
        content = self.__get_remote_content()

        # Write content to file
        with self.local_file.open('wb') as file_handle:
            file_handle.write(content)

    @staticmethod
    def reset_loaded_database() -> None:
        """
        Reset (clear) this class's database of loaded remote files.
        """

        try:
            RemoteFile.LOADED.truncate()
        except Exception:
            # Misformed databases can cause read errors
            RemoteFile.LOADED_FILE.unlink(missing_ok=True)
            pass