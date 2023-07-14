from pathlib import Path as _Path_, _windows_flavour, _posix_flavour
import os


class CleanPath(_Path_):
    """
    Subclass of Path that is more OS-agnostic and implements methods of
    cleaning directories and filenames of bad characters. For example:

    >>> p = CleanPath('./some_file: 123.jpg')
    >>> print(p)
    './some_file: 123.jpg'
    >>> print(p.sanitize())
    >>> '{parent folders}/some_file - 123.jpg'
    """

    """Mapping of illegal filename characters and their replacements"""
    ILLEGAL_FILE_CHARACTERS = {
        '?': '!',
        '<': '',
        '>': '',
        ':':' -',
        '"': '',
        '|': '',
        '*': '-',
        '/': '+',
        '\\': '+',
    }

    """Implement the correct 'flavour' depending on the host OS"""
    _flavour = _windows_flavour if os.name == 'nt' else _posix_flavour


    def finalize(self) -> 'CleanPath':
        """
        Finalize this path by properly resolving if absolute or
        relative.

        Returns:
            This object as a fully resolved path.

        Raises:
            OSError if the resolution fails (likely due to an
            unresolvable filename).
        """

        return (CleanPath.cwd() / self).resolve()


    @staticmethod
    def sanitize_name(filename: str) -> str:
        """
        Sanitize the given filename to remove any illegal characters.

        Args:
            filename: Filename (string) to remove illegal characters
                from.

        Returns:
            Sanitized filename.
        """

        replacements = CleanPath.ILLEGAL_FILE_CHARACTERS

        return filename.translate(str.maketrans(replacements))


    @staticmethod
    def _sanitize_parts(path: 'CleanPath') -> 'CleanPath':
        """
        Sanitize all parts of the given path based on the current OS.

        Args:
            path: Path to sanitize.

        Returns:
            Sanitized path. This is a reconstructed CleanPath object
            with each folder (or part), except the root/drive, sanitized.
        """

        return CleanPath(
            path.parts[0],
            *[CleanPath.sanitize_name(name) for name in path.parts[1:]]
        )


    def sanitize(self) -> 'CleanPath':
        """
        Sanitize all parts (except the root) of this objects path.

        Returns:
            CleanPath object instantiated with sanitized names of each
            part of this object's path.
        """

        # Attempt to resolve immediately
        try:
            finalized_path = self.finalize()
        # If path resolution raises an error, clean and then re-resolve
        except Exception as e:
            finalized_path =self._sanitize_parts(CleanPath.cwd()/self).resolve()

        return self._sanitize_parts(finalized_path)
