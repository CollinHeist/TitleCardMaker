from os import environ, name as os_name
from pathlib import Path
from random import choices as random_choices
from re import findall
from shlex import split as command_split
from string import hexdigits
from subprocess import Popen, PIPE, TimeoutExpired
from typing import Iterable, Literal, NamedTuple, Optional, overload

from imagesize import get as im_get

from modules.Debug import log


class Dimensions(NamedTuple): # pylint: disable=missing-class-docstring
    width: float
    height: float


class ImageMagickInterface:
    """
    This class describes an interface to ImageMagick. If initialized
    with a valid docker container (name or ID), then all given
    ImageMagick commands will be run through that docker container.

    Note: This class does not validate the provided container
    corresponds to a valid ImageMagick container. Commands are passed to
    docker so long as any container name/ID is provided.

    An example command

    >>> docker run --name="ImageMagick" --entrypoint="/bin/bash" \
        -dit -v "/mnt/user/":"/mnt/user/" 'dpokidov/imagemagick'
    """

    """How long to wait before terminating a command as timed out"""
    COMMAND_TIMEOUT_SECONDS = 60

    """Default quality for image creation"""
    DEFAULT_CARD_QUALITY = 95

    """Directory for all temporary images created during image creation"""
    TEMP_DIR = Path(__file__).parent / '.objects'

    """Temporary file location for svg -> png conversion"""
    TEMPORARY_SVG_FILE = TEMP_DIR / 'temp_logo.svg'

    """Characters that must be escaped in commands"""
    __REQUIRED_ESCAPE_CHARACTERS = ('\\', '"', '`', '%')

    """Substrings that must be present in --version output"""
    __REQUIRED_VERSION_SUBSTRINGS = ('Version','Copyright','License','Features')

    __slots__ = ('container', 'use_docker', 'prefix', 'timeout', '__history')


    def __init__(self,
            container: Optional[str] = None,
            use_magick_prefix: bool = False,
            timeout: int = COMMAND_TIMEOUT_SECONDS,
        ) -> None:
        """
        Construct a new instance. If container is falsey, then commands
        will not use a docker container.

       Args:
            container: Optional docker container name/ID to sending
                ImageMagick commands to.
            use_magick_prefix: Whether to use 'magick' command prefix.
            timeout: How many seconds to wait for a command to execute.
        """

        # Definitions of this interface, i.e. whether to use docker and how
        self.container = container
        self.use_docker = bool(container)

        # Whether to prefix commands with "magick" or not
        self.prefix = 'magick ' if use_magick_prefix else ''

        # Store command timeout
        self.timeout = timeout

        # Command history for debug purposes
        self.__history: list[tuple[str, bytes, bytes]] = []


    def validate_interface(self) -> bool:
        """
        Verify this interface has a valid connection to ImageMagick.

        Returns:
            True if the connection is valid, False otherwise.
        """

        output = self.run_get_output('convert --version')

        return all(_ in output for _ in self.__REQUIRED_VERSION_SUBSTRINGS)


    @overload
    @staticmethod
    def escape_chars(string: Literal[None]) -> Literal[None]: ...
    @overload
    @staticmethod
    def escape_chars(string: str) -> str: ...

    @staticmethod
    def escape_chars(string: Optional[str]) -> Optional[str]:
        """
        Escape the necessary characters within the given string so that
        they can be sent to ImageMagick.

        Args:
            string: The string to escape.

        Returns:
            Input string with all necessary characters escaped. This
            assumes that text will be wrapped in "".
        """

        if string is None:
            return None

        for char in ImageMagickInterface.__REQUIRED_ESCAPE_CHARACTERS:
            string = string.replace(char, f'\{char}')

        return string


    def run(self, command: str) -> tuple[bytes, bytes]:
        """
        Wrapper for running a given command. This uses either the host
        machine (i.e. direct calls); or through the provided docker
        container (if preferences has been set; i.e. wrapped through
        "docker exec -t {id} {command}").

        Args:
            command: The command (as string) to execute.

        Returns:
            Tuple of the STDOUT and STDERR of the executed command.
        """

        # Un-escape \( and \) into ( and )
        if os_name == 'nt':
            command = command.replace('\(', '(').replace('\)', ')')

        # If a docker image ID is specified, execute the command in that container
        # otherwise, execute on the host machine (no docker wrapper)
        if self.use_docker:
            command = f'docker exec -t {self.container} {self.prefix}{command}'
        else:
            command = f'{self.prefix}{command}'

        # Split command into list of strings for Popen
        try:
            cmd = command_split(command)
        except ValueError:
            log.exception(f'Invalid ImageMagick command')
            log.debug(command)
            return b'', b''

        # Execute, capturing stdout and stderr
        stdout, stderr = b'', b''
        try:
            with Popen(cmd, stdout=PIPE, stderr=PIPE) as process:
                stdout, stderr = process.communicate(timeout=self.timeout)
        except TimeoutExpired:
            log.error(f'ImageMagick command timed out')
            log.debug(command)
        except FileNotFoundError:
            log.exception(f'Command error')
            log.debug(command)

        # Add command to history and return results
        self.__history.append((command, stdout, stderr))

        return stdout, stderr


    def run_get_output(self, command: str) -> str:
        """
        Wrapper for `run()`, but return the byte-decoded stdout.

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


    def delete_intermediate_images(self, *paths: Path) -> None:
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
            log.debug(f'Command:\n{command}\n\n'
                      f'stdout:\n{stdout.decode()}\n\n'
                      f'stderr:\n{stderr.decode()}')


    def get_image_dimensions(self, image: Path) -> Dimensions:
        """
        Get the dimensions of the given image.

        Args:
            image: Path to the image to get the dimensions of.

        Returns:
            Namedtuple of dimensions.
        """

        # Return dimenions of zero if image DNE
        if not image or not image.exists():
            return Dimensions(0, 0)

        return Dimensions(*im_get(image))


    def get_text_dimensions(self,
            text_command: list[str],
            *,
            density: Optional[int] = None,
            interline_spacing: int = 0,
            line_count: int = 1,
            width: Literal['sum', 'max'] = 'max',
            height: Literal['sum', 'max'] = 'sum',
        ) -> Dimensions:
        """
        Get the dimensions of the text produced by the given text
        command. For 'width' and 'height' arguments, if 'max' then the
        maximum value of the text is utilized, while 'sum' will add each
        value. For example, if the given text command produces text like:

            Top Line Text
            Bottom Text

        Specifying width='sum', will add the widths of the two lines
        (not very meaningful), width='max' will return the maximum width
        of the two lines. Specifying height='sum' will return the total
        height of the text, and height='max' will return the tallest
        single line of text.

        Args:
            text_command: ImageMagick commands that produce text(s) to
                measure.
            density: Density of the image.
            width: How to process the width of the produced text(s).
            height: How to process the height of the produced text(s).

        Returns:
            Dimensions namedtuple.
        """

        # No text
        if not text_command:
            return Dimensions(0, 0)

        text_command = ' '.join([
            f'convert',
            f'-debug annotate',
            f'-density {density}' if density else '',
            f'' if '-annotate ' in ' '.join(text_command) else f'xc: ',
            *text_command,
            f'null: 2>&1',
        ])

        # Execute dimension command, parse output
        metrics = self.run_get_output(text_command)
        widths = list(map(int, findall(r'Metrics:.*width:\s+(\d+)', metrics)))
        heights = list(map(int, findall(r'Metrics:.*height:\s+(\d+)', metrics)))
        ascents = list(map(int, findall(r'Metrics:.*ascent:\s+(\d+)', metrics)))
        descents = list(map(int, findall(r'Metrics:.*descent:\s+-(\d+)', metrics)))

        try:
            # Label text produces duplicate Metrics
            def sum_(dims: Iterable[float]) -> int:
                return sum(dims) / (2 if ' label:"' in text_command else 1)

            # Process according to given methods
            height_adjustment = interline_spacing * (line_count - 1)
            return Dimensions(
                sum_(widths)  if width  == 'sum' else max(widths),
                (sum_(ascents) + sum_(descents)) + height_adjustment,
                # (sum_(ascents) + sum_(descents)) * (density or 72) / 72 + height_adjustment,
                # sum_(heights) if height == 'sum' else max(heights),
            )
        except ValueError as e:
            log.debug(f'Cannot identify text dimensions - {e}')
            log.trace(f'{widths=} {heights=}')
            return Dimensions(0, 0)


    def resize_image(self,
            input_image: Path,
            output_image: Path,
            *,
            by: Literal['width', 'height'],
            width: Optional[int] = None,
            height: Optional[int] = None
        ) -> Path:
        """
        Resize the given input image by a given width or height.

        Args:
            input_image: Path to the image to resize.
            output_image: Path to write the resized image to.
            by: Whether to resize by width or height.
            width: Width dimension to resize toward (if indicated).
            height: Height dimension to resize toward (if indicated).

        Raises:
            ValueError if by is not "width" or "height".
            ValueError if the indicated dimension is not provided or
                less than 0.
        """

        if by not in ('width', 'height'):
            raise ValueError(f'Can only resize by "width" or "height"')

        if by == 'width' and width is not None and width > 0:
            resize_command = f'-resize {width}x'
        elif by == 'height' and height is not None and height > 0:
            resize_command = f'-resize x{height}'
        else:
            raise ValueError(f'Resized dimension must be greater than zero')

        command = ' '.join([
            f'convert "{input_image.resolve()}"',
            f'-sampling-factor 4:4:4',
            f'-set colorspace sRGB',
            f'+profile "*"',
            f'-background transparent',
            f'-gravity center',
            resize_command,
            f'"{output_image.resolve()}"',
        ])

        self.run(command)

        return output_image


    def convert_svg_to_png(self,
            image: Path,
            destination: Path,
            min_dimension: int = 2500
        ) -> Optional[Path]:
        """
        Convert the given SVG image to PNG format.

        Args:
            image: Path to the SVG image being converted.
            destination: Path to the output image.
            min_dimension: Minimum dimension of the converted image.

        Returns:
            Path to the converted file. None if the conversion failed.
        """

        # If the temp file doesn't exist, return
        if not image.exists():
            return None

        # Command to convert file to PNG
        command = ' '.join([
            f'convert',
            f'-density 512',
            f'-resize "{min_dimension}x{min_dimension}"',
            f'-background None',
            f'"{image.resolve()}"',
            f'"{destination.resolve()}"',
        ])
        self.run(command)

        # Print command history if conversion failed
        if destination.exists():
            return destination

        self.print_command_history()
        return None


    def round_image_corners(self,
            image: Path,
            commands: list[str],
            dimensions: Optional[Dimensions] = None,
            radius: int = 25,
        ) -> Path:
        """
        Round the corners of the given image, writing the resulting
        image to a new file.

        Args:
            image: Path to the image to modify.
            commands: List of ImageMagick commands which contains the
                image data to modify.
            dimensions: Dimensions of the image. If not provided, these
                are calculated.
            radius: Radius to utilize for the corner rounding.

        Returns:
            Path to the created file.
        """

        # Calculate dimensions if not provided
        if not dimensions:
            dimensions = self.get_image_dimensions(image)

        # Path to temporary file for rounded image
        random_chars = ''.join(random_choices(hexdigits, k=6))
        temp_image = image.parent / f'{image.stem}.{random_chars}.webp'

        self.run(' '.join([
            f'convert',
            f'-background none',
            *commands,
            f'-matte',
            f'\( -size {dimensions.width}x{dimensions.height}',
            f'xc:none',
            f'-draw "roundrectangle',
            f'0,0 {dimensions.width:.0f},{dimensions.height:.0f}',
            f'{radius:.0f},{radius:.0f}"',
            f'\)',
            f'-compose DstIn',
            f'-composite',
            f'"{temp_image.resolve()}"',
        ]))

        return temp_image
