---
title: Integrating Local Card Types
description: >
    How to add and integrate local card type Python files.
---

# Local Card Types

!!! warning "Programming Knowledge"

    The development of local card types is not very difficult, but it _does_
    require a basic understanding of the Python programming language and
    ImageMagick. I can provide some support for the TCM-specific requirements,
    but I do not have time to teach these concepts in addition to developing
    TCM.

    If you have an idea for a card type, but are not interested in (or cannot
    dedicate the time to) developing it yourself, I offer card design as a
    [Sponsor reward](https://github.com/sponsors/CollinHeist?frequency=one-time&sponsor=CollinHeist) on GitHub.

## File Location

Any local card type files should be placed inside the `card_types` directory in
your main `config` directory. On Docker, this is `/config/card_types/`, and on
non-Docker this is `./config/card_types/`.

TCM will automatically parse all Python (`.py`) files in this directory.

## Syntax Requirements

There are specific requirements for how these Python files and classes must be
structured in order to integrate into TCM. These are outlined below.

1. The file must be named the same as the card class.

    ??? example "Example"

        If I were making a card class called "Fancy", and the Python class were
        named `FancyTitleCard`

        ```python title="FancyTitleCard.py" linenums="1" hl_lines="1"
        class FancyTitleCard(BaseCardType):
            ...
        ```

        Then the filename _must_ be `FancyTitleCard.py` - e.g. the class name
        and `.py`.

2. The Python class must be a sub-class of `modules.BaseCardType.BaseCardType`.

    ??? example "Example"

        ```python title="FancyTitleCard.py" linenums="1" hl_lines="1 3"
        from modules.BaseCardType import BaseCardType

        class FancyTitleCard(BaseCardType):
            ...
        ```

3. The class must define `TITLE_CHARACTERISTICS`, which is a dictionary which
matches the type definition of `modules.Title.SplitCharacteristics`, which is:

    ```python
    class SplitCharacteristics(TypedDict):
        # Character count to begin splitting titles into multiple lines
        max_line_width: int
        # Maximum number of lines a title can take up
        max_line_count: int
        # How to split titles into multiple lines
        style: Literal['top', 'bottom', 'even', 'forced even']
    ```

    ??? example "Example"

        ```python title="FancyTitleCard.py" linenums="1" hl_lines="5-9"
        from modules.BaseCardType import BaseCardType
        from modules.Title import SplitCharacteristics

        class FancyTitleCard(BaseCardType):
            TITLE_CHARACTERISTICS: SplitCharacteristics = {
                'max_line_width': 20,
                'max_line_count': 2,
                'style': 'top',
            }
        ```

        This would make TCM auto-split titles after 20 characters into at most
        2 lines, and the titles would be top-heavy (i.e. more text on the first
        line than the second).

4. The class must define `TITLE_FONT` as the string representation of the path
to the default Font file. It can be useful to use the path of the Python file
itself - accessed with `Path(__file__)` - or the path of the reference
directory used by TCM itself - accessed at `BaseCardType.BASE_REF_DIRECTORY`.

    ??? example "Example"

        ```python title="FancyTitleCard.py" linenums="1" hl_lines="14"
        from pathlib import Path
        from modules.BaseCardType import BaseCardType
        from modules.Title import SplitCharacteristics

        class FancyTitleCard(BaseCardType):
            REF_DIRECTORY = Path(__file__).parent / 'fancy_files'

            TITLE_CHARACTERISTICS: SplitCharacteristics = {
                'max_line_width': 20,
                'max_line_count': 2,
                'style': 'top',
            }

            TITLE_FONT = str((REF_DIRECTORY / 'DefaultFont.ttf').resolve())
        ```

        This sets the default Font to a `DefaultFont.ttf` file in a folder
        `fancy_files` next to the `FancyTitleCard.py` file.

5. The class must define `TITLE_COLOR` as a string of the default Font color.
Any format of ImageMagick
[color name](https://imagemagick.org/script/color.php#color_names) is accepted.

    ??? example "Example"

        ```python title="FancyTitleCard.py" linenums="1" hl_lines="15"
        from pathlib import Path
        from modules.BaseCardType import BaseCardType
        from modules.Title import SplitCharacteristics

        class FancyTitleCard(BaseCardType):
            REF_DIRECTORY = Path(__file__).parent / 'fancy_files'

            TITLE_CHARACTERISTICS: SplitCharacteristics = {
                'max_line_width': 20,
                'max_line_count': 2,
                'style': 'top',
            }

            TITLE_FONT = str((REF_DIRECTORY / 'DefaultFont.ttf').resolve())
            TITLE_COLOR = 'white'
        ```

6. The class must define `DEFAULT_FONT_CASE` as the name of the case function to
apply to the title text - e.g. `blank`, `lower`, `source`, `title`, or `upper`.
Each is described below:

    | Font Case | Description |
    | :-------: | :---------- |
    | `blank`   | Remove all text |
    | `lower`   | Make all text lowercase |
    | `source`  | Leave the text as-is |
    | `title`   | Apply title texting to - e.g. "Title Text" |
    | `upper`   | Make all text uppercase |

    ??? example "Example"

        ```python title="FancyTitleCard.py" linenums="1" hl_lines="14-16"
        from pathlib import Path
        from modules.BaseCardType import BaseCardType
        from modules.Title import SplitCharacteristics

        class FancyTitleCard(BaseCardType):
            REF_DIRECTORY = Path(__file__).parent / 'fancy_files'

            TITLE_CHARACTERISTICS: SplitCharacteristics = {
                'max_line_width': 20,
                'max_line_count': 2,
                'style': 'top',
            }

            TITLE_FONT = str((REF_DIRECTORY / 'DefaultFont.ttf').resolve())
            TITLE_COLOR = 'white'
            DEFAULT_FONT_CASE = 'source'
        ```

7. The class must define `FONT_REPLACEMENTS` as a dictionary of text
replacements to apply whose keys are the input text to replace with the values
as output text. This is typically used for correcting characters missing from
the default Font.

    ??? example "Example"

        ```python title="FancyTitleCard.py" linenums="1" hl_lines="17-20"
        from pathlib import Path
        from modules.BaseCardType import BaseCardType
        from modules.Title import SplitCharacteristics

        class FancyTitleCard(BaseCardType):
            REF_DIRECTORY = Path(__file__).parent / 'fancy_files'

            TITLE_CHARACTERISTICS: SplitCharacteristics = {
                'max_line_width': 20,
                'max_line_count': 2,
                'style': 'top',
            }

            TITLE_FONT = str((REF_DIRECTORY / 'DefaultFont.ttf').resolve())
            TITLE_COLOR = 'white'
            DEFAULT_FONT_CASE = 'source'
            FONT_REPLACEMENTS = {
                'é': 'e',
                'ü': 'u',
            }
        ```

        This would make TCM replace all instances of `é` with `e` and `ü` with
        `u`.

8. The class must define the class initialization method (`__init__`) as a
function which accepts only keyword arguments (and `**`). It must have the
`blur`, `grayscale`, and `preferences` arguments _and_ pass these into the
`super()` method. All arguments must be stored as attributes where needed.

    ??? example "Example"

        ```python title="FancyTitleCard.py" linenums="1" hl_lines="22-36"
        from pathlib import Path
        from modules.BaseCardType import BaseCardType
        from modules.Title import SplitCharacteristics

        class FancyTitleCard(BaseCardType):
            REF_DIRECTORY = Path(__file__).parent / 'fancy_files'

            TITLE_CHARACTERISTICS: SplitCharacteristics = {
                'max_line_width': 20,
                'max_line_count': 2,
                'style': 'top',
            }

            TITLE_FONT = str((REF_DIRECTORY / 'DefaultFont.ttf').resolve())
            TITLE_COLOR = 'white'
            DEFAULT_FONT_CASE = 'source'
            FONT_REPLACEMENTS = {
                'é': 'e',
                'ü': 'u',
            }

            def __init__(self,
                source_file: Path,
                card_file: Path,
                title_text: str,
                blur: bool = False,
                grayscale: bool = False,
                preferences: 'Preferences' = None,
                **unused,
            ) -> None:

                super().__init__(blur, grayscale, preferences=preferences)

                self.source_file = source_file
                self.card_file = card_file
                self.title_text = title_text
        ```

9. The class must define `__slots__` as a tuple of all the attribute names as
strings.

    ??? example "Example"

        ```python title="FancyTitleCard.py" linenums="1" hl_lines="22 36-38"
        from pathlib import Path
        from modules.BaseCardType import BaseCardType
        from modules.Title import SplitCharacteristics

        class FancyTitleCard(BaseCardType):
            REF_DIRECTORY = Path(__file__).parent / 'fancy_files'

            TITLE_CHARACTERISTICS: SplitCharacteristics = {
                'max_line_width': 20,
                'max_line_count': 2,
                'style': 'top',
            }

            TITLE_FONT = str((REF_DIRECTORY / 'DefaultFont.ttf').resolve())
            TITLE_COLOR = 'white'
            DEFAULT_FONT_CASE = 'source'
            FONT_REPLACEMENTS = {
                'é': 'e',
                'ü': 'u',
            }

            __slots__ = ('source_file', 'card_file', 'title_text')

            def __init__(self,
                source_file: Path,
                card_file: Path,
                title_text: str,
                blur: bool = False,
                grayscale: bool = False,
                preferences: 'Preferences' = None,
                **unused,
            ) -> None:

                super().__init__(blur, grayscale, preferences=preferences)

                self.source_file = source_file
                self.card_file = card_file
                self.title_text = title_text
        ```

9. The class must define a `create` method which accepts no arguments,
implements the actual Card creation, and must delete all intermediate files
created by the Card.

    ??? example "Example"

        ```python title="FancyTitleCard.py" linenums="1" hl_lines="41-56"
        from pathlib import Path
        from modules.BaseCardType import BaseCardType
        from modules.Title import SplitCharacteristics

        class FancyTitleCard(BaseCardType):
            REF_DIRECTORY = Path(__file__).parent / 'fancy_files'

            TITLE_CHARACTERISTICS: SplitCharacteristics = {
                'max_line_width': 20,
                'max_line_count': 2,
                'style': 'top',
            }

            TITLE_FONT = str((REF_DIRECTORY / 'DefaultFont.ttf').resolve())
            TITLE_COLOR = 'white'
            DEFAULT_FONT_CASE = 'source'
            FONT_REPLACEMENTS = {
                'é': 'e',
                'ü': 'u',
            }

            __slots__ = ('source_file', 'card_file', 'title_text')

            def __init__(self,
                source_file: Path,
                card_file: Path,
                title_text: str,
                blur: bool = False,
                grayscale: bool = False,
                preferences: 'Preferences' = None,
                **unused,
            ) -> None:

                super().__init__(blur, grayscale, preferences=preferences)

                self.source_file = source_file
                self.card_file = card_file
                self.title_text = title_text


            def create(self) -> None:

                command = ' '.join([
                    f'convert "{self.source_file.resolve()}"',
                    # Resize and apply styles to source image
                    *self.resize_and_style,
                    f'-pointsize 500',
                    f'-gravity center',
                    f'-fill skyblue',
                    f'-annotate +0+0 "{self.title_text}"',
                    # Create card
                    *self.resize_output,
                    f'"{self.output_file.resolve()}"',
                ])

                self.image_magick.run(command)
        ```

11. The class must define `API_DETAILS` as a `CardDescription` object with all
attributes defined. This information is what is displayed in the UI.

    ??? example "Example"

        ```python title="FancyTitleCard.py" linenums="1" hl_lines="2 7-24"
        from pathlib import Path
        from modules.BaseCardType import BaseCardType, Extra, CardDescription
        from modules.Title import SplitCharacteristics

        class FancyTitleCard(BaseCardType):

            API_DETAILS = CardDescription(
                name='Test',
                identifier='fancy',
                example='/path/to/some/preview/image.jpg',
                creators=['CollinHeist'],
                source='local',
                supports_custom_fonts=False,
                supports_custom_seasons=False,
                supported_extras=[
                    Extra(
                        name='Extra Value',
                        identifier='extra_val',
                        description='Some extra value!',
                    ),
                ], description=[
                    'A very Fancy title card.'
                ]
            )

            REF_DIRECTORY = Path(__file__).parent / 'fancy_files'

            TITLE_CHARACTERISTICS: SplitCharacteristics = {
                'max_line_width': 20,
                'max_line_count': 2,
                'style': 'top',
            }

            TITLE_FONT = str((REF_DIRECTORY / 'DefaultFont.ttf').resolve())
            TITLE_COLOR = 'white'
            DEFAULT_FONT_CASE = 'source'
            FONT_REPLACEMENTS = {
                'é': 'e',
                'ü': 'u',
            }

            __slots__ = ('source_file', 'card_file', 'title_text', 'extra_val')

            def __init__(self,
                source_file: Path,
                card_file: Path,
                title_text: str,
                extra_val: str,
                blur: bool = False,
                grayscale: bool = False,
                preferences: 'Preferences' = None,
                **unused,
            ) -> None:

                super().__init__(blur, grayscale, preferences=preferences)

                self.source_file = source_file
                self.card_file = card_file
                self.title_text = title_text
                self.extra_val = extra_val


            def create(self) -> None:

                command = ' '.join([
                    f'convert "{self.source_file.resolve()}"',
                    # Resize and apply styles to source image
                    *self.resize_and_style,
                    f'-pointsize 500',
                    f'-gravity center',
                    f'-fill skyblue',
                    f'-annotate +0+0 "{self.title_text}"',
                    # Create card
                    *self.resize_output,
                    f'"{self.output_file.resolve()}"',
                ])

                self.image_magick.run(command)
        ```

12. And finally, the class must define an attribute `CardModel` class which
is a subclass of either the `pydantic.BaseModel` or any of the
`app.schemas.card_type.BaseCardModel` subclasses - and performs any field
validation.

    ??? example "Example"

        ```python title="FancyTitleCard.py" linenums="1" hl_lines="2 27-28"
        from pathlib import Path
        from app.schemas.card_type import BaseCardModel
        from modules.BaseCardType import BaseCardType, Extra, CardDescription
        from modules.Title import SplitCharacteristics

        class FancyTitleCard(BaseCardType):

            API_DETAILS = CardDescription(
                name='Test',
                identifier='fancy',
                example='/path/to/some/preview/image.jpg',
                creators=['CollinHeist'],
                source='local',
                supports_custom_fonts=False,
                supports_custom_seasons=False,
                supported_extras=[
                    Extra(
                        name='Extra Value',
                        identifier='extra_val',
                        description='Some extra value!',
                    ),
                ], description=[
                    'A very Fancy title card.'
                ]
            )

            class CardModel(BaseCardModel):
                extra_val: str

            REF_DIRECTORY = Path(__file__).parent / 'fancy_files'

            TITLE_CHARACTERISTICS: SplitCharacteristics = {
                'max_line_width': 20,
                'max_line_count': 2,
                'style': 'top',
            }

            TITLE_FONT = str((REF_DIRECTORY / 'DefaultFont.ttf').resolve())
            TITLE_COLOR = 'white'
            DEFAULT_FONT_CASE = 'source'
            FONT_REPLACEMENTS = {
                'é': 'e',
                'ü': 'u',
            }

            __slots__ = ('source_file', 'card_file', 'title_text', 'extra_val')

            def __init__(self,
                source_file: Path,
                card_file: Path,
                title_text: str,
                extra_val: str,
                blur: bool = False,
                grayscale: bool = False,
                preferences: 'Preferences' = None,
                **unused,
            ) -> None:

                super().__init__(blur, grayscale, preferences=preferences)

                self.source_file = source_file
                self.card_file = card_file
                self.title_text = title_text
                self.extra_val = extra_val


            def create(self) -> None:

                command = ' '.join([
                    f'convert "{self.source_file.resolve()}"',
                    # Resize and apply styles to source image
                    *self.resize_and_style,
                    f'-pointsize 500',
                    f'-gravity center',
                    f'-fill skyblue',
                    f'-annotate +0+0 "{self.title_text}"',
                    # Create card
                    *self.resize_output,
                    f'"{self.output_file.resolve()}"',
                ])

                self.image_magick.run(command)
        ```
