from argparse import ArgumentParser, SUPPRESS
from dataclasses import dataclass
from os import environ
from pathlib import Path
from re import match, IGNORECASE
from sys import exit as sys_exit

try:
    from modules.AspectRatioFixer import AspectRatioFixer
    from modules.CleanPath import CleanPath
    from modules.CollectionPosterMaker import CollectionPosterMaker
    from modules.Debug import log
    from modules.GenreMaker import GenreMaker
    from modules.MoviePosterMaker import MoviePosterMaker
    from modules.PreferenceParser import PreferenceParser
    from modules.global_objects import set_preference_parser
    from modules.RemoteFile import RemoteFile
    from modules.SeasonPoster import SeasonPoster
    from modules.StandardSummary import StandardSummary
    from modules.StylizedSummary import StylizedSummary
except ImportError:
    print(f'Required Python packages are missing - execute "pipenv install"')
    sys_exit(1)

# Environment Variables
ENV_IS_DOCKER = 'TCM_IS_DOCKER'
ENV_PREFERENCE_FILE = 'TCM_PREFERENCES'

# Default values
DEFAULT_PREFERENCE_FILE = Path(__file__).parent / 'preferences.yml'

parser = ArgumentParser(description='Manually make cards')
parser.add_argument(
    '-p', '--preferences', '--preference-file',
    type=Path,
    default=environ.get(ENV_PREFERENCE_FILE, DEFAULT_PREFERENCE_FILE),
    metavar='FILE',
    help=f'File to read global preferences from. Environment variable '
         f'{ENV_PREFERENCE_FILE}. Defaults to '
         f'"{DEFAULT_PREFERENCE_FILE.resolve()}"')
parser.add_argument(
    '--borderless', '--omit-border',
    action='store_true',
    help='Omit the border from the created Collection/Genre image')
parser.add_argument(
    '--no-gradient', '--omit-gradient',
    action='store_true',
    help='Omit the gradient from the created Collection/Genre/Season image')

# Argument group for 'manual' title card creation
title_card_group = parser.add_argument_group(
    'Title Cards', 'Manual TitleCardMaker interaction'
)
title_card_group.add_argument(
    '--title-card',
    type=Path,
    nargs=2,
    default=SUPPRESS,
    metavar=('SOURCE', 'DESTINATION'),
    help='Create a title card with the given source image, written to the given'
         ' destination')
title_card_group.add_argument(
    '--card-type',
    type=str,
    default='standard',
    metavar='TYPE',
    help='Create a title card of a specific type')
title_card_group.add_argument(
    '--blur',
    action='store_true',
    help='Blur the source image for this card')
title_card_group.add_argument(
    '--grayscale',
    action='store_true',
    help='Convert the source image to grayscale for this card')
title_card_group.add_argument(
    '--episode',
    type=str,
    default='EPISODE',
    metavar='EPISODE_TEXT',
    help='The episode text for this card')
title_card_group.add_argument(
    '--season',
    type=str,
    default=None,
    metavar='SEASON_TEXT',
    help='The season text for this card')
title_card_group.add_argument(
    '--title',
    type=str,
    nargs='+',
    default='',
    metavar=('TITLE_LINE'),
    help="The title text for this card, each value is a new line")
title_card_group.add_argument(
    '--logo',
    type=Path,
    default=None,
    metavar='LOGO_FILE',
    help='Logo file to add to the card (if supported)')
title_card_group.add_argument(
    '--font-file', '--font',
    type=Path,
    default='__default',
    metavar='FONT_FILE',
    help="A custom font file for this card")
title_card_group.add_argument(
    '--font-size', '--size',
    type=str,
    default='100%',
    metavar='SCALE%',
    help='A font scale (as percentage) for this card')
title_card_group.add_argument(
    '--font-color', '--color',
    type=str,
    default='__default',
    metavar='#HEX',
    help='A custom font color for this card')
title_card_group.add_argument(
    '--font-vertical-shift', '--vertical-shift',
    type=float,
    default=0.0,
    metavar='PIXELS',
    help='How many pixels to vertically shift the title text')
title_card_group.add_argument(
    '--font-interline-spacing', '--interline-spacing',
    type=float,
    default=0.0,
    metavar='PIXELS',
    help='How many pixels to increase the interline spacing of the title text')
title_card_group.add_argument(
    '--font-kerning', '--kerning',
    type=str,
    default='100%',
    metavar='SCALE%',
    help='Specify the font kerning scale (as percentage)')
title_card_group.add_argument(
    '--font-stroke-width', '--stroke-width',
    type=str,
    default='100%',
    metavar='SCALE%',
    help='Specify the font black stroke scale (as percentage)')

# Argument group for aspect ratio fixing
aspect_ratio_group = parser.add_argument_group(
    'Aspect Ratio Correction',
    'Fit images into a 16:9 aspect ratio')
aspect_ratio_group.add_argument(
    '--ratio', '--aspect-ratio',
    type=Path,
    nargs=2,
    default=SUPPRESS,
    metavar=('SOURCE', 'DESTINATION'),
    help='Correct the aspect ratio of the given image, write to destination')
aspect_ratio_group.add_argument(
    '--ratio-batch', '--aspect-ratio-batch',
    type=Path,
    default=SUPPRESS,
    metavar='DIRECTORY',
    help='Correct the aspect ratios of all images in the given directory')
aspect_ratio_group.add_argument(
    '--ratio-style', '--aspect-ratio-style',
    type=str,
    default=AspectRatioFixer.DEFAULT_STYLE,
    choices=AspectRatioFixer.VALID_STYLES,
    help='Style of the aspect-ratio correction to utilize')

# Argument group for collection posters
collection_group = parser.add_argument_group(
    'Collection Posters',
    'Manual collection poster creation')
collection_group.add_argument(
    '--collection-poster',
    type=Path,
    nargs=2,
    default=SUPPRESS,
    metavar=('SOURCE', 'DESTINATION'),
    help='Create a collection poster with the given files')
collection_group.add_argument(
    '--collection-title',
    type=str,
    nargs='+',
    default='',
    metavar=('TITLE_LINE'),
    help='Collection title for this collection poster')
collection_group.add_argument(
    '--collection-font',
    type=Path,
    default=CollectionPosterMaker.FONT,
    metavar='FONT',
    help='Custom font for the collection text of the collection poster')
collection_group.add_argument(
    '--collection-font-color',
    type=str,
    default=CollectionPosterMaker.FONT_COLOR,
    metavar='COLOR',
    help='A custom font color for this collection poster')
collection_group.add_argument(
    '--collection-font-size',
    type=str,
    default='100%',
    metavar='SCALE%',
    help='A font scale (as percentage) for this collection poster')
collection_group.add_argument(
    '--omit-collection',
    action='store_true',
    help='Omit the "COLLECTION" text from this collection poster')

# Argument group for movie posters
movie_poster_group = parser.add_argument_group(
    'Movie Posters',
    'Manual movie poster creation')
movie_poster_group.add_argument(
    '--movie-poster',
    type=Path,
    nargs=2,
    default=SUPPRESS,
    metavar=('SOURCE', 'DESTINATION'),
    help='Create a movie poster with the given files')
movie_poster_group.add_argument(
    '--movie-title',
    type=str,
    nargs='+',
    default='',
    metavar=('TITLE_LINE'),
    help='Movie title for the movie poster')
movie_poster_group.add_argument(
    '--movie-top-subtitle',
    type=str,
    default='',
    metavar='TOP_SUBTITLE',
    help='Top subtitle line for the movie poster')
movie_poster_group.add_argument(
    '--movie-subtitle',
    type=str,
    default='',
    metavar='SUBTITLE',
    help='Subtitle for the movie poster')
movie_poster_group.add_argument(
    '--movie-index', '--movie-number',
    type=str,
    default='',
    metavar='INDEX',
    help='Index number/text to place behind the title text on the movie poster')
movie_poster_group.add_argument(
    '--movie-logo',
    type=Path,
    default=None,
    metavar='LOGO_FILE',
    help='Logo file to overlay on top of movie poster')
movie_poster_group.add_argument(
    '--movie-font',
    type=Path,
    default=MoviePosterMaker.FONT,
    metavar='FONT',
    help='Custom font for the title text of the movie poster')
movie_poster_group.add_argument(
    '--movie-font-color',
    type=str,
    default=MoviePosterMaker.FONT_COLOR,
    metavar='COLOR',
    help='A custom font color for the movie poster')
movie_poster_group.add_argument(
    '--movie-font-size',
    type=str,
    default='100%',
    metavar='SCALE%',
    help='A font scale (as percentage) for the movie poster')
movie_poster_group.add_argument(
    '--movie-font-vertical-shift',
    type=int,
    default=0,
    metavar='PIXELS',
    help='How many pixels to vertically shift the title text')
movie_poster_group.add_argument(
    '--movie-drop-shadow',
    action='store_true',
    help='Whether to add a drop shadow to the text for the movie poster')

# Argument group for genre cards
genre_group = parser.add_argument_group(
    'Genre Cards',
    'Manual genre card creation')
genre_group.add_argument(
    '--genre-card',
    type=str,
    nargs=3,
    default=SUPPRESS,
    metavar=('SOURCE', 'GENRE', 'DESTINATION'),
    help='Create a genre card with the given text')
genre_group.add_argument(
    '--genre-card-batch',
    type=Path,
    default=SUPPRESS,
    metavar=('SOURCE_DIRECTORY'),
    help='Create all genre cards for images in the given directory based on '
         'their file names')

# Argument group for show summaries
show_summary_group = parser.add_argument_group(
    'Show Summaries',
    'Manual ShowSummary creation')
show_summary_group.add_argument(
    '--show-summary',
    type=Path,
    nargs=2,
    default=SUPPRESS,
    metavar=('IMAGE_DIRECTORY', 'LOGO'),
    help='Create a show summary for the given directory')
show_summary_group.add_argument(
    '--background',
    type=str,
    default='default',
    metavar='COLOR_OR_IMAGE',
    help='Specify background color or image for the created show summary')
show_summary_group.add_argument(
    '--created-by',
    type=str,
    default=None,
    metavar='CREATOR',
    help='Specify a custom username for the "Created by .." text on the created'
         ' show summary')
show_summary_group.add_argument(
    '--summary-type',
    type=str,
    default='default',
    metavar='SUMMARY_TYPE',
    choices=('default', 'standard', 'stylized'),
    help='Type of summary image to create')

# Argument group for season posters
season_poster_group = parser.add_argument_group(
    'Season Poster',
    'Manual SeasonPoster creation')
season_poster_group.add_argument(
    '--season-poster',
    type=Path,
    nargs=2,
    default=SUPPRESS,
    metavar=('SOURCE', 'DESTINATION'),
    help='Create a season poster with the given assets')
season_poster_group.add_argument(
    '--season-poster-logo',
    type=Path,
    default=SUPPRESS,
    metavar='LOGO',
    help='Add the given logo to the created season poster')
season_poster_group.add_argument(
    '--season-text',
    type=str,
    nargs='+',
    default=['SEASON ONE'],
    metavar=('SEASON_TEXT'),
    help='Season text for the created season poster')
season_poster_group.add_argument(
    '--season-font',
    type=Path,
    default=SeasonPoster.SEASON_TEXT_FONT,
    metavar='FONT_FILE',
    help='A custom font file for this season poster')
season_poster_group.add_argument(
    '--season-font-color',
    default=SeasonPoster.SEASON_TEXT_COLOR,
    metavar='COLOR',
    help='A custom font color for this season poster')
season_poster_group.add_argument(
    '--season-font-size',
    type=str,
    default='100%',
    metavar='SCALE%',
    help='A font scale (as percentage) for this season poster')
season_poster_group.add_argument(
    '--season-font-kerning',
    type=str,
    default='100%',
    metavar='SCALE%',
    help='Specify the font kerning scale (as percentage) in the season poster')
season_poster_group.add_argument(
    '--season-font-vertical-shift',
    type=int,
    default=0,
    metavar='PIXELS',
    help='How many pixels to vertically shift the season text')
season_poster_group.add_argument(
    '--logo-placement',
    choices=('top', 'middle', 'bottom'),
    default='bottom',
    help='Where to place the logo in the created season poster')
season_poster_group.add_argument(
    '--text-placement',
    choices=('top', 'bottom'),
    default='bottom',
    help='Where to place the text in the created season poster')

# Parse given arguments
args, unknown = parser.parse_known_args()
is_docker = environ.get(ENV_IS_DOCKER, 'false').lower() == 'true'

# Create dictionary of unknown arguments
arbitrary_data = {}
if len(unknown) % 2 == 0 and len(unknown) > 1:
    arbitrary_data = dict(zip(unknown[::2], unknown[1::2]))
    log.info(f'Extras Identified:')

# Print unknown arguments
for key, value in arbitrary_data.items():
    log.info(f'  {key}: "{value}"')

# Parse preference file for options that might need it
if not (pp := PreferenceParser(args.preferences, is_docker)).valid:
    sys_exit(1)
set_preference_parser(pp)

# Execute title card related options
if hasattr(args, 'title_card'):
    # Attempt to get local card type, if not, try RemoteCardType
    CardClass = pp._parse_card_type(args.card_type)
    RemoteFile.reset_loaded_database()

    # Override unspecified defaults with their class specific defaults
    if args.font_file == Path('__default'):
        args.font_file = Path(str(CardClass.TITLE_FONT))
    if args.font_color == '__default':
        args.font_color = CardClass.TITLE_COLOR

    # Create the given card
    output_file = CleanPath(args.title_card[1]).sanitize()
    output_file.unlink(missing_ok=True)
    card = CardClass(
        source_file=CleanPath(args.title_card[0]).sanitize(),
        card_file=output_file,
        logo_file=args.logo,
        title_text='\n'.join(args.title),
        season_text=('' if not args.season else args.season),
        episode_text=args.episode,
        hide_season_text=(not bool(args.season)),
        hide_episode_text=(not bool(args.episode)),
        font_color=args.font_color,
        font_file=args.font_file.resolve(),
        font_interline_spacing=args.font_interline_spacing,
        font_kerning=float(args.font_kerning[:-1])/100.0,
        font_size=float(args.font_size[:-1])/100.0,
        font_stroke_width=float(args.font_stroke_width[:-1])/100.0,
        font_vertical_shift=args.font_vertical_shift,
        blur=args.blur,
        grayscale=args.grayscale,
        omit_gradient=args.no_gradient,
        **arbitrary_data,
    )

    # Create, log success/failure
    card.create()
    if output_file.exists():
        log.info(f'Created "{output_file.resolve()}"')
    else:
        log.warning(f'Could not create "{output_file.resolve()}"')
        card.image_magick.print_command_history()

# Correct aspect ration
if hasattr(args, 'ratio'):
    AspectRatioFixer(
        source=args.ratio[0],
        destination=args.ratio[1],
        style=args.ratio_style,
    ).create()

if hasattr(args, 'ratio_batch'):
    for file in args.ratio_batch.glob('*'):
        if file.suffix.lower() in AspectRatioFixer.VALID_IMAGE_EXTENSIONS:
            AspectRatioFixer(
                source=file,
                destination=file.with_stem(f'{file.stem}-corrected'),
                style=args.ratio_style,
            ).create()

# Create Collection Poster
if hasattr(args, 'collection_poster'):
    CollectionPosterMaker(
        source=args.collection_poster[0],
        output=args.collection_poster[1],
        title='\n'.join(args.collection_title),
        font=args.collection_font,
        font_color=args.collection_font_color,
        font_size=float(args.collection_font_size[:-1])/100.0,
        omit_collection=args.omit_collection,
        borderless=args.borderless,
        omit_gradient=args.no_gradient,
    ).create()

# Create Movie Poster
if hasattr(args, 'movie_poster'):
    MoviePosterMaker(
        source=args.movie_poster[0],
        output=args.movie_poster[1],
        title='\n'.join(args.movie_title),
        subtitle=args.movie_subtitle,
        top_subtitle=args.movie_top_subtitle,
        movie_index=args.movie_index,
        logo=args.movie_logo,
        font_file=args.movie_font,
        font_color=args.movie_font_color,
        font_size=float(args.movie_font_size[:-1])/100.0,
        font_vertical_shift=args.movie_font_vertical_shift,
        borderless=args.borderless,
        add_drop_shadow=args.movie_drop_shadow,
        omit_gradient=args.no_gradient,
    ).create()

# Create Genre Poster
if hasattr(args, 'genre_card'):
    GenreMaker(
        source=Path(args.genre_card[0]),
        genre=args.genre_card[1],
        output=Path(args.genre_card[2]),
        font_size=float(args.font_size[:-1])/100.0,
        borderless=args.borderless,
        omit_gradient=args.no_gradient,
    ).create()

if hasattr(args, 'genre_card_batch'):
    for file in args.genre_card_batch.glob('*'):
        if file.suffix.lower() in GenreMaker.VALID_IMAGE_EXTENSIONS:
            GenreMaker(
                source=file,
                genre=file.stem.upper(),
                output=file.with_stem(f'{file.stem}-GenreCard'),
                font_size=float(args.font_size[:-1])/100.0,
                borderless=args.borderless,
                omit_gradient=args.no_gradient,
            ).create()

# Create show summaries
if hasattr(args, 'show_summary'):
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
    all_images = args.show_summary[0].glob('**/*.jpg')
    season, episode = 1, 1
    episodes = {}
    for file in all_images:
        # Attempt to get index from filename, if not just increment last number
        if (groups := match(r'.*s(\d+).*e(\d+)', file.name, IGNORECASE)):
            season, episode = map(int, groups.groups())
            info = EpisodeInfo(season, episode)
            episodes[f'{season}-{episode}'] = Episode(info, file)
        else:
            info = EpisodeInfo(season, episode)
            episodes[f'{season}-{episode}'] = Episode(info, file)
            episode += 1

    # Create pseudo "show" of these episodes
    show = Show(args.show_summary[1], args.show_summary[0], episodes)

    # Override minimum episode count
    pp.summary_minimum_episode_count = 0

    # Create Summary
    if args.summary_type.lower() == 'default':
        summary = pp.summary_class(show, args.background, args.created_by)
    elif args.summary_type.lower() == 'standard':
        summary = StandardSummary(show, args.background, args.created_by)
    elif args.summary_type.lower() == 'stylized':
        summary = StylizedSummary(show, args.background, args.created_by)
    else:
        log.warning(f'Invalid summary style - using default')
        summary = pp.summary_class(show, args.background, args.created_by)
    summary.create()

    # Log success/failure
    if summary.output.exists():
        log.info(f'Created "{summary.output.resolve()}"')
    else:
        log.warning(f'Failed to create "{summary.output.resolve()}"')
        summary.image_magick.print_command_history()

# Create season posters
if hasattr(args, 'season_poster'):
    if hasattr(args, 'season_poster_logo'):
        logo = args.season_poster_logo
    else:
        logo = None

    SeasonPoster(
        source=args.season_poster[0],
        destination=args.season_poster[1],
        logo=logo,
        season_text='\n'.join(args.season_text),
        font=args.season_font,
        font_color=args.season_font_color,
        font_size=float(args.season_font_size[:-1])/100.0,
        font_kerning=float(args.season_font_kerning[:-1])/100.0,
        font_vertical_shift=args.season_font_vertical_shift,
        logo_placement=args.logo_placement,
        omit_gradient=args.no_gradient,
        omit_logo=not hasattr(args, 'season_poster_logo'),
        text_placement=args.text_placement,
    ).create()
