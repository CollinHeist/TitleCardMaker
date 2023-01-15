from shlex import split as command_split
from subprocess import Popen, PIPE, TimeoutExpired

from modules.Debug import log

class ImageMagickInterface:
    """
    This class describes an interface to ImageMagick. If initialized with a
    valid docker container (name or ID), then all given ImageMagick commands
    will be run through that docker container.

    Note: This class does not validate the provided container corresponds to
    a valid ImageMagick container. Commands are passed to docker so long as any
    container name/ID is provided.

    An example command

    >>> docker run --name="ImageMagick" --entrypoint="/bin/bash" \
        -dit -v "/mnt/user/":"/mnt/user/" 'dpokidov/imagemagick'
    """

    """How long to wait before terminating a command as timed out"""
    COMMAND_TIMEOUT_SECONDS = 240

    """Characters that must be escaped in commands"""
    __REQUIRED_ESCAPE_CHARACTERS = ('"', '`', '%')

    """Substrings that must be present in --version output"""
    __REQUIRED_VERSION_SUBSTRINGS = ('Version','Copyright','License','Features')

    __slots__ = ('container', 'use_docker', 'prefix', 'timeout', '__history')


    def __init__(self, container: str=None, use_magick_prefix: bool=False,
                 timeout: int=COMMAND_TIMEOUT_SECONDS) -> None:
        """
        Construct a new instance. If container is falsey, then commands will not
        use a docker container.
        
       Args:
            container: Optional docker container name/ID to sending ImageMagick
                commands to.
            use_magick_prefix: Whether to use 'magick' command prefix.
            timeout: How many seconds to wait for a command to execute. Defaults
                to COMMAND_TIMEOUT_SECONDS.
        """
        
        # Definitions of this interface, i.e. whether to use docker and how
        self.container = container
        self.use_docker = bool(container)

        # Whether to prefix commands with "magick" or not
        self.prefix = 'magick ' if use_magick_prefix else ''

        # Store command timeout
        self.timeout = timeout

        # Command history for debug purposes
        self.__history = []


    def verify_interface(self) -> bool:
        """
        Verify this interface has a valid connection to ImageMagick.

        Returns:
            True if the connection is valid, False otherwise.
        """

        output = self.run_get_output('convert --version')

        return all(_ in output for _ in self.__REQUIRED_VERSION_SUBSTRINGS)


    @staticmethod
    def escape_chars(string: str) -> str:
        """
        Escape the necessary characters within the given string so that they
        can be sent to ImageMagick.
        
        Args:
            string: The string to escape.
        
        Returns:
            Input string with all necessary characters escaped. This assumes
            that text will be wrapped in "", and so only escapes " and `
            characters.
        """

        # Handle possible bad (None) strings
        if string is None:
            return None

        for char in ImageMagickInterface.__REQUIRED_ESCAPE_CHARACTERS:
            string = string.replace(char, f'\{char}')

        return string


    def run(self, command: str) -> tuple[bytes, bytes]:
        """
        Wrapper for running a given command. This uses either the host machine
        (i.e. direct calls); or through the provided docker container (if
        preferences has been set; i.e. wrapped through "docker exec -t {id}
        {command}").

        Args:
            command: The command (as string) to execute.

        Returns:
            Tuple of the STDOUT and STDERR of the executed command.
        """
        
        # If a docker image ID is specified, execute the command in that container
        # otherwise, execute on the host machine (no docker wrapper)
        if self.use_docker:
            command = f'docker exec -t {self.container} {self.prefix}{command}'
        else:
            command = f'{self.prefix}{command}'
            
        # Split command into list of strings for Popen
        cmd = command_split(command)

        # Execute, capturing stdout and stderr
        stdout, stderr = b'', b''
        try:
            process = Popen(cmd, stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate(timeout=self.timeout)
        except TimeoutExpired:
            log.error(f'ImageMagick command timed out')
            log.debug(command)
        except FileNotFoundError as e:
            log.error(f'Command error "{e}"')
            log.debug(command)
            
        # Add command to history and return results
        self.__history.append((command, stdout, stderr))
        
        return stdout, stderr


    def run_get_output(self, command: str) -> str:
        """
        Wrapper for run(), but return the byte-decoded stdout.
        
        Args:
            command: The command (as string) being executed.

        Returns:
            The decoded stdout output of the executed command.
        """

        output = self.run(command)
        
        try:
            return b''.join(output).decode()
        except UnicodeDecodeError:
            return b''.join(output).decode('iso8859')


    def delete_intermediate_images(self, *paths: tuple) -> None:
        """
        Delete all the provided intermediate files.
        
        Args:
            paths: Any number of files to delete. Must be Path objects.
        """

        # Delete (unlink) each image, don't raise FileNotFoundError if DNE
        for image in paths:
            image.unlink(missing_ok=True)


    def print_command_history(self) -> None:
        """Print the command history of this Interface."""

        for command, stdout, stderr in self.__history:
            log.debug(f'Command: {command}\n\n'
                      f'stdout: {stdout}\n\n'
                      f'stderr: {stderr}\n'
                      f'{"-" * 60}')