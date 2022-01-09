from subprocess import run

from Debug import *

class ImageMagickInterface:
    def __init__(self, docker_id: str) -> None:
        """
        Constructs a new instance.
        
        :param      docker_id:  The docker identifier
        """
        
        # Definitions of this interface, i.e. whether to use docker and how
        self.docker_id = docker_id
        self.use_docker = bool(docker_id)


    def run(self, command: str, *args: tuple, **kwargs: dict):
        """
        Wrapper for running a given command. This uses either the host machine
        (i.e. direct calls); or through the provided docker container (if
        `preferences` has been set; i.e. wrapped through "docker exec -t {id}
        {command}"). `args` and `kwargs` are used to permit general usage of
        the `subprocess.run()` function's options (`capture_output`, etc).

        :param      command:    The command to execute
        
        :param      args:       Any arguments to pass to the subprocess `run`
                                function.

        :param      kwargs:     Any keyword arguments to pass to the subprocess `run`
                                function.
        """
        
# docker run --name="ImageMagick" --entrypoint="/bin/bash" -dit -v "/mnt/user/":"/mnt/user/" 'dpokidov/imagemagick'
        
        # If a docker image ID is specified, execute the command in that container
        # otherwise, execute on the host machine (no docker wrapper)
        if self.use_docker:
            command = f'docker exec -t {self.docker_id} {command}'
        else:
            command = command
            
        return run(command, shell=True, *args, **kwargs)


    def run_get_stdout(self, command: str, *args: tuple, **kwargs: dict):
        """
        Wrapper for `run()`, but return the byte-decoded stdout immediately.
        
        :param      command:    The command
        :param      args:     The arguments
        :param      kwargs:   The keywords arguments
        """

        return self.run(command, capture_output=True, *args, **kwargs).stdout.decode()


    def delete_intermediate_images(self, *paths: tuple) -> None:
        """
        Delete all the provided files.
        
        :param      paths:  Any number of files to delete. Must be
                            Path objects.
        """

        # Delete (unlink) each image, don't raise FileNotFoundError if DNE
        for image in paths:
            image.unlink(missing_ok=True)

