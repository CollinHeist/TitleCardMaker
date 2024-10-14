from pathlib import Path
from time import sleep
from typing import Callable

from json.decoder import JSONDecodeError
from tinydb import TinyDB

from modules.Debug import log
from modules import global_objects


class PersistentDatabase:
    """
    This class describes some persistent storage and is a loose wrapper
    of a TinyDB object. The purpose of this class is to handle corrupted
    TinyDB databases without littering the code with try/except
    statements. Any function calls on this object are called on the
    underlying TinyDB object and any raised JSONDecodeError Exceptions
    are caught, the database is deleted, and the function is
    re-executed.
    """

    MAX_DB_RETRY_COUNT: int = 5


    def __init__(self, filename: str) -> None:
        """
        Initialize an instance of an object for the given TinyDB object
        with the given filename.

        Args:
            filename: Filename to the Database object.
        """

        # Path to the file itself
        self.file: Path = global_objects.pp.database_directory / filename
        self.file.parent.mkdir(exist_ok=True, parents=True)

        # Initialize TinyDB from file
        try:
            self.db = TinyDB(self.file)
        except JSONDecodeError:
            log.exception(f'Database {self.file.resolve()} is corrupted')
            self.reset()
        except Exception:
            log.exception(f'Uncaught exception on Database initialization')
            self.reset()


    def __getattr__(self, database_func: str) -> Callable:
        """
        Get an arbitrary function for this object. This returns a
        wrapped version of the accessed function that catches any
        uncaught JSONDecodeError exceptions (prompting a DB reset).

        Args:
            database_func: The function being called.

        Returns:
            Wrapped callable that is the indicated function with any
            uncaught JSONDecodeError exceptions caught, the database
            reset, and then the function recalled.
        """

        # Define wrapper that calls given function with args, and then catches
        # any uncaught exceptions
        def wrapper(*args, __retries: int = 0, **kwargs) -> None:
            try:
                kwargs.pop('__retries', None)
                return getattr(self.db, database_func)(*args, **kwargs)
            except (ValueError, JSONDecodeError) as e:
                # If this function has been attempted too many times, just raise
                if __retries > self.MAX_DB_RETRY_COUNT:
                    raise e

                # Log conflict, sleep, reset database, and try function again
                log.exception(f'Database {self.file.resolve()} has conflict')
                sleep(3)
                self.reset()
                return wrapper(*args, **kwargs, __retries=__retries+1)

        # Return "attribute" that is the wrapped function
        return wrapper


    def __len__(self) -> int:
        """Call len() on this object's underlying TinyDB object."""

        return len(self.db)


    def reset(self) -> None:
        """
        Reset this object's associated database. This deletes the file
        and  recreates a new TinyDB.
        """

        # Attempt to remove all records; if that fails delete and remake file
        try:
            self.db.truncate()
        except Exception:
            self.file.unlink(missing_ok=True)
            self.file.parent.mkdir(exist_ok=True, parents=True)
            self.db = TinyDB(self.file)
