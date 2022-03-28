from subprocess import run

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

    def __init__(self, container: str=None) -> None:
        """
        Constructs a new instance. If docker_id is None/0/False, then commands
        will not use a docker container.
        
        :param      container:  The container for sending requests to
                                ImageMagick, can be a name or container ID.
        """
        
        # Definitions of this interface, i.e. whether to use docker and how
        self.container = container
        self.use_docker = bool(container)


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


    def run(self, command: str, *args: tuple, **kwargs: dict):
        """
        Wrapper for running a given command. This uses either the host machine
        (i.e. direct calls); or through the provided docker container (if
        preferences has been set; i.e. wrapped through "docker exec -t {id}
        {command}"). args and kwargs are used to permit general usage of
        the subprocess.run() function's options (capture_output, etc).

        :param      command:    The command to execute
        
        :param      args:       The arguments to pass to subprocess.run().

        :param      kwargs:     The keyword arguments to pass to subprocess.run().

        :returns:   The return of the subprocess.run() function execution.
        """
        
        
        # If a docker image ID is specified, execute the command in that container
        # otherwise, execute on the host machine (no docker wrapper)
        if self.use_docker:
            command = f'docker exec -t {self.container} {command}'
        else:
            command = command
            
        return run(command, shell=True, *args, **kwargs)


    def run_get_stdout(self, command: str, *args: tuple, **kwargs: dict) -> str:
        """
        Wrapper for run(), but return the byte-decoded stdout.
        
        :param      command:            The command being executed.
        :param      args and kwargs:    Generalized arguments to pass to
                                        subprocess.run().

        :returns:   The decoded stdout output of the executed command.
        """

        return self.run(
            command, capture_output=True, *args, **kwargs
        ).stdout.decode()


    def delete_intermediate_images(self, *paths: tuple) -> None:
        """
        Delete all the provided intermediate files.
        
        :param      paths:  Any number of files to delete. Must be Path objects.
        """

        # Delete (unlink) each image, don't raise FileNotFoundError if DNE
        for image in paths:
            image.unlink(missing_ok=True)

