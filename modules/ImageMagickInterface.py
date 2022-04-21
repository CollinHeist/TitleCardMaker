from shlex import split as command_split
from subprocess import Popen, PIPE

from modules.Debug import log

class ImageMagickInterface:
    """
    This class describes an interface to ImageMagick. If initialized with a
    valid docker container (name or ID), then all given ImageMagick commands
    will be run through that docker container.

    Note: This class does not validate the provided container corresponds to
    a valid ImageMagick container. Commands are passed to docker so long as any
    container is fiben.

    The command I use for launching an ImageMagick container is:

    >>> docker run --name="ImageMagick" --entrypoint="/bin/bash" \
        -dit -v "/mnt/user/":"/mnt/user/" 'dpokidov/imagemagick'
    """

    def __init__(self, container: str=None,
                 use_magick_prefix: bool=False) -> None:
        """
        Constructs a new instance. If docker_id is None/0/False, then commands
        will not use a docker container.
        
        :param      container:  The container for sending requests to
                                ImageMagick, can be a name or container ID.
        """
        
        # Definitions of this interface, i.e. whether to use docker and how
        self.container = container
        self.use_docker = bool(container)

        # Whether to prefix commands with "magick" or not
        self.prefix = 'magick ' if use_magick_prefix else ''

        # Command history for debug purposes
        self.__history = []


    @staticmethod
    def escape_chars(string: str) -> str:
        """
        Escape the necessary characters within the given string so that they
        can be sent to ImageMagick.
        
        :param      string: The string to escape.
        
        :returns:   Input string with all necessary characters escaped. This 
                    assumes that text will be wrapped in "", and so only escapes
                    " and ` characters.
        """

        # Handle possible None strings
        if string is None:
            return None

        return string.replace('"', r'\"').replace('`', r'\`')


    def run(self, command: str) -> (bytes, bytes):
        """
        Wrapper for running a given command. This uses either the host machine
        (i.e. direct calls); or through the provided docker container (if
        preferences has been set; i.e. wrapped through "docker exec -t {id}
        {command}").

        :param      command:    The command (as string) to execute.

        :returns:   Tuple of the STDOUT and STDERR of the executed command.
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
            stdout, stderr = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()

            # Add command to history
            self.__history.append((command, stdout, stderr))

            return stdout, stderr
        except FileNotFoundError as e:
            if 'docker' in str(e):
                log.critical(f'ImageMagick docker container not found')
                exit(1)
            else:
                log.error(f'Command error "{e}"')
                return b'', b''


    def run_get_output(self, command: str) -> str:
        """
        Wrapper for run(), but return the byte-decoded stdout.
        
        :param      command:    The command (as string) being executed.

        :returns:   The decoded stdout output of the executed command.
        """

        return b''.join(self.run(command)).decode()


    def delete_intermediate_images(self, *paths: tuple) -> None:
        """
        Delete all the provided intermediate files.
        
        :param      paths:  Any number of files to delete. Must be Path objects.
        """

        # Delete (unlink) each image, don't raise FileNotFoundError if DNE
        for image in paths:
            image.unlink(missing_ok=True)


    def print_command_history(self) -> None:
        """
        Prints the command history of this Interface.
        """

        for entry in self.__history:
            command, stdout, stderr = entry
            sep = '-' * 60
            log.debug(f'Command: {command}\n\nstdout: {stdout}\n\nstderr: '
                      f'{stderr}\n{sep}')



