from pathlib import Path

from json.decoder import JSONDecodeError
from tinydb import TinyDB

from modules.Debug import log
import modules.global_objects as global_objects

class PersistentDatabase:
    """
    This class describes some persistent storage and is a loose wrapper of a
    TinyDB object. The purpose of this class is to handle corrupted TinyDB
    databases without littering the code with try/except statements. Any
    function calls on this object are called on the underlying TinyDB object and
    any raised JSONDecodeError Exceptions are caught, the database is deleted,
    and the function is re-executed.
    """


    def __init__(self, filename: str) -> None:
        """
        Initialize an instance of an object for the given TinyDB object with the
        given filename.

        Args:
            filename: Filename to the Database object.
        """

        # Path to the file itself
        self.file: Path = global_objects.pp.database_directory / filename
        self.file.parent.mkdir(exist_ok=True, parents=True)
       
        # Initialize TinyDB from file
        try:
            self.db = TinyDB(self.file)
        except JSONDecodeError as e:
            log.exception(f'Database {self.file.resolve()} is corrupted', e)
            self.reset()
        except Exception as e:
            log.exception(f'Uncaught exception on Database initialization', e)
            self.reset()


    def __getattr__(self, database_func: str) -> callable:
        """
        Get an arbitrary function for this object. This returns a wrapped
        version of the accessed function that catches any uncaught
        JSONDecodeError exceptions (prompting a DB reset).

        Args:
            database_func: The function being called.

        Returns:
            Wrapped callable that is the indicated function with any uncaught
            JSONDecodeError exceptions caught, the database reset, and then the
            function recalled.
        """

        # Define wrapper that calls given function with args, and then catches
        # any uncaught exceptions
        def wrapper(*args, **kwargs) -> None:
            try:
                return getattr(self.db, database_func)(*args, **kwargs)
            except JSONDecodeError as e:
                log.exception(f'Database {self.file.resolve()} is corrupted', e)
                self.reset()
                return getattr(self.db, database_func)(*args, **kwargs)

        # Return "attribute" that is the wrapped function
        return wrapper


    def __len__(self) -> int:
        return len(self.db)


    def reset(self) -> None:
        """
        Reset this object's associated database. This deletes the file and 
        recreates a new TinyDB.
        """

        # Attempt to remove all records; if that fails delete and remake file
        try:
            self.db.truncate()
        except Exception:
            self.file.unlink(missing_ok=True)
            self.file.parent.mkdir(exist_ok=True, parents=True)
            self.db = TinyDB(self.file)