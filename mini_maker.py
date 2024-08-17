from dataclasses import dataclass
from pathlib import Path
from re import match as re_match, IGNORECASE
from sys import exit as sys_exit
from typing import Any, Literal, Optional

try:
    import click

    from modules.AspectRatioFixer import AspectRatioFixer
    from modules.CleanPath import CleanPath
    from modules.CollectionPosterMaker import CollectionPosterMaker
    from modules.Debug import log
    from modules.GenreMaker import GenreMaker
    from modules.MoviePosterMaker import MoviePosterMaker
    from modules.RemoteFile import RemoteFile
    from modules.SeasonPoster import SeasonPoster
    from modules.StandardSummary import StandardSummary
    from modules.StylizedSummary import StylizedSummary
    from modules.YamlReader import YamlReader
except ImportError as exc:
    print('Required Python packages are missing - execute "pipenv install"')
    print(f'  Specific Error: {exc}')
    sys_exit(1)


ENV_PREFERENCE_FILE = 'TCM_PREFERENCES'
ENV_CARD_QUALITY = 'TCM_CARD_QUALITY'
ENV_IMAGEMAGICK_CONTAINER = 'TCM_IM_DOCKER'
DEFAULT_PREFERENCE_FILE = Path(__file__).parent / 'preferences.yml'


@click.group()
@click.option('--quality', envvar=ENV_CARD_QUALITY,
              type=click.IntRange(min=0, max=100, clamp=True), default=92,
              help='Image compression quality to utilize')
@click.option('--use-magick-prefix', is_flag=True,
              help='Whether to use the "magick" ImageMagick command prefix')
@click.option('--imagemagick-container', envvar=ENV_IMAGEMAGICK_CONTAINER,
              type=str, default=None,
              help='Docker container to execute ImageMagick commands within')
def mini_maker(
        quality: int,
        use_magick_prefix: bool,
        imagemagick_container: str,
    ) -> None:
    import modules.global_objects as global_objects
    global_objects.pp.card_quality = quality
    global_objects.pp.use_magick_prefix = use_magick_prefix
    global_objects.pp.imagemagick_container = imagemagick_container
    global_objects.pp.summary_minimum_episode_count = 0


@mini_maker.command(help='Apply aspect-ratio correction to an image')
@click.argument('source', type=Path)
@click.argument('destination', type=Path)
@click.option('--style', type=click.Choice(['copy', 'stretch']),
              default=AspectRatioFixer.DEFAULT_STYLE,
              help='Style of the aspect-ratio correction method')
def aspect_ratio(
        source: Path,
        destination: Path,
        style: Literal['copy', 'stretch'],
    ) -> None:

    AspectRatioFixer(
        source=source, destination=destination, style=style
    ).create()


@mini_maker.command(help='Batch apply aspect-ratio correction to a directory')
@click.argument('directory', type=Path)
@click.option('--style', type=click.Choice(['copy', 'stretch']),
              default=AspectRatioFixer.DEFAULT_STYLE,
              help='Style of the aspect-ratio correction method')
@click.option('--postfix', type=str, default='-corrected',
              help='Postfix to add to the filename of corrected files')
def aspect_ratio_batch(
        directory: Path,
        style: Literal['copy', 'stretch'],
        postfix: str,
    ) -> None:

    for file in directory.glob('*'):
        if (file.suffix.lower() in AspectRatioFixer.VALID_IMAGE_EXTENSIONS
            and not file.stem.endswith(postfix)):
            AspectRatioFixer(
                source=file,
                destination=file.with_stem(f'{file.stem}{postfix}'),
                style=style,
            ).create()


@mini_maker.command(help='Create a Collection Poster')
@click.argument('source', type=Path)
@click.argument('destination', type=Path)
@click.option('--title', type=str, multiple=True, default=[''],
              help='Collection title')
@click.option('--font', type=Path, default=CollectionPosterMaker.FONT,
              help='Font file of the text')
@click.option('--font-color', type=str, default=CollectionPosterMaker.FONT_COLOR,
              help='Font color for the title text(s)')
@click.option('--font-size', type=click.FloatRange(min=0.0), default=1.0,
              help='Font size scalar')
@click.option('--omit-collection', is_flag=True,
              help='Whether to omit the "COLLECTION" text')
def collection_poster(
        source: Path,
        destination: Path,
        title: list[str],
        font: Path,
        font_color: str,
        font_size: float,
        omit_collection: bool,
    ) -> None:
    """Manual collection poster creation"""

    CollectionPosterMaker(
        source=source,
        output=destination,
        title='\n'.join(title),
        font_file=font,
        font_color=font_color,
        font_size=font_size,
        omit_collection=omit_collection
    ).create()


@mini_maker.command(help='Create a Genre Card')
@click.argument('source', type=Path)
@click.argument('destination', type=Path)
@click.argument('genre', type=str)
@click.option('--font-size', type=click.FloatRange(min=0.0), default=1.0,
              help='Font size scalar for the genre text')
@click.option('--borderless', is_flag=True,
              help='Omit the border from the created image')
@click.option('--omit-gradient', is_flag=True,
              help='Omit the gradient from the created image')
def genre_card(
        source: Path,
        destination: Path,
        genre: str,
        font_size: float,
        borderless: bool,
        omit_gradient: bool,
    ) -> None:

    GenreMaker(
        source=source,
        genre=genre,
        output=destination,
        font_size=font_size,
        borderless=borderless,
        omit_gradient=omit_gradient,
    ).create()


@mini_maker.command(help='Create a batch of Genre Cards')
@click.argument('directory', type=Path)
@click.option('--font-size', type=click.FloatRange(min=0.0), default=1.0,
              help='Font size scalar for the genre text')
@click.option('--postfix', type=str, default='-GenreCard',
              help='Postfix to add to the filename of corrected files')
@click.option('--borderless', is_flag=True,
              help='Omit the border from the created image')
@click.option('--omit-gradient', is_flag=True,
              help='Omit the gradient from the created image')
def genre_card_batch(
        directory: Path,
        font_size: float,
        postfix: str,
        borderless: bool,
        omit_gradient: bool,
    ) -> None:

    for file in directory.glob('*'):
        if file.suffix.lower() in GenreMaker.VALID_IMAGE_EXTENSIONS:
            GenreMaker(
                source=file,
                genre=file.stem.upper(),
                output=file.with_stem(f'{file.stem}{postfix}'),
                font_size=font_size,
                borderless=borderless,
                omit_gradient=omit_gradient,
            ).create()


@mini_maker.command(help='Create a movie poster')
@click.argument('source', type=Path)
@click.argument('destination', type=Path)
@click.option('--title', type=str, multiple=True,
              help='Movie title for the movie poster')
@click.option('--top-subtitle', type=str, default='',
              help='Top subtitle line for the movie poster')
@click.option('--subtitle', type=str, default='',
              help='Subtitle for the movie poster')
@click.option('--index', '--number', type=str, default='',
              help='Index number or text to place behind the title')
@click.option('--logo', type=Path, default=None,
              help='Logo file to overlay on top of movie poster')
@click.option('--font', type=Path, default=MoviePosterMaker.FONT,
              help='Custom font for the title text')
@click.option('--font-color', type=str, default=MoviePosterMaker.FONT_COLOR,
              help='Font color for the title text')
@click.option('--font-size', type=click.FloatRange(min=0.0), default=1.0,
              help='Font size scalar for the text')
@click.option('--font-vertical-shift', type=int, default=0,
              help='Vertical shift to apply to title text')
@click.option('--drop-shadow', is_flag=True,
              help='Whether to add a drop shadow to the text for the movie poster')
@click.option('--borderless', is_flag=True,
              help='Omit the border from the created image')
@click.option('--omit-gradient', is_flag=True,
              help='Omit the gradient from the created image')
def movie_poster(
        source: Path,
        destination: Path,
        title: list[str],
        top_subtitle: str,
        subtitle: str,
        index: str,
        logo: Optional[Path],
        font: Path,
        font_color: str,
        font_size: float,
        font_vertical_shift: int,
        drop_shadow: bool,
        borderless: bool,
        omit_gradient: bool,
    ) -> None:

    MoviePosterMaker(
        source=source,
        output=destination,
        title='\n'.join(title),
        top_subtitle=top_subtitle,
        subtitle=subtitle,
        movie_index=index,
        logo=logo,
        font_file=font,
        font_color=font_color,
        font_size=font_size,
        font_vertical_shift=font_vertical_shift,
        borderless=borderless,
        add_drop_shadow=drop_shadow,
        omit_gradient=omit_gradient,
    ).create()


@mini_maker.command(help='Create a show summary image')
@click.argument('directory', type=Path)
@click.argument('logo', type=Path)
@click.option('--background', type=str, default=None,
              help='Background color or image for the created show summary')
@click.option('--creator', type=str, default=None,
              help='Custom username for the "Created by .." text')
@click.option('--summary-type',
              type=click.Choice(['standard', 'stylized']), default='stylized',
              help='Type of summary image to create')
def show_summary(
        directory: Path,
        logo: Path,
        background: Optional[str],
        creator: Optional[str],
        summary_type: Literal['standard', 'stylized'],
    ) -> None:

    # Temporary classes
    @dataclass
    class EpisodeInfo:
        season_number: int
        episode_number: int
    @dataclass
    class Episode:
        episode_info: EpisodeInfo
        destination: Path
    @dataclass
    class Show:
        logo: Path
        media_directory: Path
        episodes: dict

    # Get all images in folder
    all_images = directory.glob('**/*.jpg')
    season, episode, episodes = 1, 1, {}
    for file in all_images:
        # Attempt to get index from filename, if not just increment last number
        if (groups := re_match(r'.*s(\d+).*e(\d+)', file.name, IGNORECASE)):
            season, episode = map(int, groups.groups())
            info = EpisodeInfo(season, episode)
            episodes[f'{season}-{episode}'] = Episode(info, file)
        else:
            info = EpisodeInfo(season, episode)
            episodes[f'{season}-{episode}'] = Episode(info, file)
            episode += 1

    # Create pseudo "Show" of these episodes
    show = Show(logo, directory, episodes)

    # Create Summary
    if summary_type == 'standard':
        summary = StandardSummary(show, background, creator)
    elif summary_type == 'stylized':
        summary = StylizedSummary(show, background, creator)
    summary.create()

    # Log success/failure
    if summary.output.exists():
        log.info(f'Created "{summary.output.resolve()}"')
    else:
        log.warning(f'Failed to create "{summary.output.resolve()}"')
        summary.image_magick.print_command_history()


@mini_maker.command(help='Create a season poster')
@click.argument('source', type=Path)
@click.argument('destination', type=Path)
@click.option('--logo', type=Path, default=None,
              help='Logo to add to the season poster')
@click.option('--season-text', type=str, multiple=True,
              help='Season text')
@click.option('--font-file', '--font', type=Path, default=SeasonPoster.SEASON_TEXT_FONT,
              help='Custom font file of the season text')
@click.option('--font-color', type=str, default=SeasonPoster.SEASON_TEXT_COLOR,
              show_default=True,
              help='Custom font color of the season text')
@click.option('--font-size', type=click.FloatRange(min=0.0), default=1.0,
              help='Font size scalar for the season text')
@click.option('--font-kerning', type=float, default=1.0,
              help='Font kerning scale for the season text')
@click.option('--font-vertical-shift', type=int, default=0,
              help='Vertical shift to apply to the season text (in pixels)')
@click.option('--logo-placement',
              type=click.Choice(['top', 'middle', 'bottom']), default='bottom',
              help='Placement of the logo')
@click.option('--text-placement',
              type=click.Choice(['top', 'bottom']), default='bottom',
              help='Placement of the season text')
@click.option('--omit-gradient', is_flag=True,
              help='Omit the gradient from the created image')
def season_poster(
        source: Path,
        destination: Path,
        logo: Optional[Path],
        season_text: list[str],
        font_file: Path,
        font_color: str,
        font_size: float,
        font_kerning: float,
        font_vertical_shift: int,
        logo_placement: Literal['top', 'middle', 'bottom'],
        text_placement: Literal['top', 'bottom'],
        omit_gradient: bool,
    ) -> None:

    SeasonPoster(
        source=source,
        destination=destination,
        logo=logo,
        season_text='\n'.join(season_text),
        font_color=font_color,
        font=font_file,
        font_size=font_size,
        font_kerning=font_kerning,
        font_vertical_shift=font_vertical_shift,
        logo_placement=logo_placement,
        text_placement=text_placement,
        omit_gradient=omit_gradient,
        omit_logo=logo is None or (isinstance(logo, Path) and not logo.exists()),
    ).create()


@mini_maker.command(help='Create a Title Card')
@click.argument('source', type=Path)
@click.argument('destination', type=Path)
@click.option('--card-type', type=str, default='standard', show_default=True,
              help='Card type of the Title Card to create')
@click.option('--episode', type=str, default='',
              help='The episode text')
@click.option('--season', type=str, default='',
              help='The season text')
@click.option('--title', type=str, multiple=True, default=[''],
              help='The title text for this Card, each value is a new line')
@click.option('--logo', type=Path, default=None,
              help='Logo file to add to the card (if supported)')
@click.option('--font-file', '--font', type=Path, default=None,
              help='Custom font file')
@click.option('--font-size', type=click.FloatRange(min=0.0), default=1.0,
              help='Font size scalar for the title text')
@click.option('--font-color', type=str, default=None,
              help='Custom font color')
@click.option('--font-vertical-shift', type=float, default=0.0,
              help='How many pixels to vertically shift the title text')
@click.option('--font-interline-spacing', type=float, default=0.0,
              help='How many pixels to increase the interline spacing of the title text')
@click.option('--font-kerning', type=float, default=1.0,
              help='Font kerning scalar')
@click.option('--font-stroke-width', type=float, default=1.0,
              help='Font stroke scalar')
@click.option('--blur', is_flag=True, help='Apply a blurred styling')
@click.option('--grayscale', is_flag=True, help='Apply a grayscale styling')
@click.argument('extras', nargs=-1)
def title_card(
        source: Path,
        destination: Path,
        card_type: str,
        episode: str,
        season: str,
        title: list[str],
        logo: Optional[Path],
        font_file: Optional[Path],
        font_size: float,
        font_color: Optional[str],
        font_vertical_shift: float,
        font_interline_spacing: float,
        font_kerning: float,
        font_stroke_width: float,
        blur: bool,
        grayscale: bool,
        extras: list[Any],
    ) -> None:

    import modules.global_objects as global_objects

    # Parse arbitrary extras
    arbitrary_data = {}
    if len(extras) % 2 == 0 and len(extras) > 1:
        arbitrary_data = dict(zip(extras[::2], extras[1::2]))
        log.debug('Extras Identified:')
        for key, value in arbitrary_data.items():
            log.debug(f'  {key}: "{value}"')

    # Attempt to get local card type, if not, try RemoteCardType
    if not (CardClass := YamlReader.parse_card_type(card_type)):
        log.error('Invalid --card-type')
        return None
    RemoteFile.reset_loaded_database()

    # Override unspecified defaults with their class specific defaults
    if not font_file:
        font_file = Path(str(CardClass.TITLE_FONT))
    if not font_color:
        font_color = CardClass.TITLE_COLOR

    # Create the given card
    destination = CleanPath(destination).sanitize()
    destination.unlink(missing_ok=True)

    card = CardClass(
        source_file=source,
        card_file=destination,
        title_text='\n'.join(title),
        season_text=season,
        episode_text=episode,
        hide_season_text=not bool(season),
        hide_episode_text=not bool(episode),
        font_color=font_color,
        font_file=font_file,
        font_size=font_size,
        font_vertical_shift=font_vertical_shift,
        font_interline_spacing=font_interline_spacing,
        font_kerning=font_kerning,
        font_stroke_width=font_stroke_width,
        logo_file=logo,
        blur=blur,
        grayscale=grayscale,
        **arbitrary_data,
    )

    # Create, log success/failure
    card.create()
    if destination.exists():
        log.info(f'Created "{destination.resolve()}"')
    else:
        log.warning(f'Could not create "{destination.resolve()}"')
        card.image_magick.print_command_history()


if __name__ == '__main__':
    mini_maker()
