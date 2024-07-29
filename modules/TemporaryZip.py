from logging import Logger
from pathlib import Path
from shutil import copy as copy_file, make_archive as zip_directory
from time import sleep
from typing import Optional

from fastapi import BackgroundTasks

from modules.Debug import generate_context_id, log


class TemporaryZip:
    """
    This class defines a temporarily-existing zip directory. Files can
    be aded to and zipped from the directory.
    """

    def __init__(self,
            temporary_directory: Path,
            background_tasks: BackgroundTasks,
        ) -> None:
        """
        Initialize a new temporary directory.

        Args:
            temporary_directory: Root directory where zips should be
                created.
            background_tasks: Task queue to add the delayed deletion to.
        """

        self.tasks = background_tasks

        # Generate a random subfolder
        zip_dir = temporary_directory / 'zips'
        context_id = generate_context_id()
        self.dir = zip_dir / context_id
        self.dir.mkdir(exist_ok=True, parents=True)


    def __delete_zip(self,
            directory: Path,
            file: Path,
            *,
            log: Logger = log,
        ) -> None:
        """
        Delete the given zip directory and files. A delay is utilized so
        that the browser is able to download the content before they are
        deleted.

        Args:
            directory: Directory containing zipped files to be deleted.
                The contents are deleted, then the directory itself.
            file: Zip file to delete directly.
            log: Logger for all log messages.
        """

        # Wait a while to give the browser time to download the zips
        sleep(5)

        # Delete zipped file
        file.unlink(missing_ok=True)
        log.debug(f'Deleted "{file}"')

        # Delete zip directory contents
        for file in directory.glob('*'):
            file.unlink(missing_ok=True)
            log.debug(f'Deleted "{file}"')

        # Delete zip directory
        directory.rmdir()
        log.debug(f'Deleted {directory}')


    def add_file(self,
            file: Path,
            filename: Optional[str] = None,
            *,
            log: Logger = log,
        ) -> None:
        """
        Add the given file to this directory for future zipping.

        Args:
            file: File to add to copy into this directory.
            filename: Filename to name `file` as. If not provided, then
                the original filename is used.
            log: Logger for all log messages.
        """

        copy_file(file, self.dir / (filename or file.name))
        log.debug(f'Copied "{file}" into zip directory')


    def zip(self, *, log: Logger = log) -> Path:
        """
        Zip this object's directory and then queue its deletion.

        Args:
            log: Logger for all log messages.

        Returns:
            Path to the created zip file.
        """

        zip_file = Path(zip_directory(self.dir, 'zip', self.dir))
        self.tasks.add_task(
            self.__delete_zip,
            directory=self.dir, file=zip_file, log=log,
        )

        return zip_file
