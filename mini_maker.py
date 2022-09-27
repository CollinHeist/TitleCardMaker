from argparse import ArgumentParser, SUPPRESS
from dataclasses import dataclass
from os import environ
from pathlib import Path
from re import match, IGNORECASE

try:
    from modules.CollectionPosterMaker import CollectionPosterMaker
    from modules.Debug import log
    from modules.GenreMaker import GenreMaker
    from modules.MoviePosterMaker import MoviePosterMaker
    from modules.PreferenceParser import PreferenceParser
    from modules.global_objects import set_preference_parser
    from modules.RemoteCardType import RemoteCardType
    from modules.RemoteFile import RemoteFile
    from modules.SeasonPoster import SeasonPoster
    from modules.StandardSummary import StandardSummary
    from modules.StylizedSummary import StylizedSummary
    from modules.TitleCard import TitleCard
except ImportError:
    print(f'Required Python packages are missing - execute "pipenv install"')
    exit(1)

# Environment Variables
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
title_card_group = parser.add_argument_group('Title Cards',
                                             'Manual TitleCardMaker interaction')
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
    help="The title text for this card")
title_card_group.add_argument(
    '--font', '--font-file',
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
    '--vertical-shift', '--shift',
    type=float,
    default=0.0,
    metavar='PIXELS',
    help='How many pixels to vertically shift the title text')
title_card_group.add_argument(
    '--interline-spacing', '--spacing',
    type=float,
    default=0.0,
    metavar='PIXELS',
    help='How many pixels to increase the interline spacing of the title text')
title_card_group.add_argument(
    '--kerning',
    type=str,
    default='100%',
    metavar='SCALE%',
    help='Specify the font kerning scale (as percentage)')
title_card_group.add_argument(
    '--stroke-width', '--stroke',
    type=str,
    default='100%',
    metavar='SCALE%',
    help='Specify the font black stroke scale (as percentage)')
    
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
    help='Summary type to create - must be "standard" or "sylized"')

# Argument group for season posters
season_poster_group = parser.add_argument_group(
    'Season Poster',
    'Manual SeasonPoster creation')
season_poster_group.add_argument(
    '--season-poster',
    type=Path,
    nargs=3,
    default=SUPPRESS,
    metavar=('SOURCE', 'LOGO', 'DESTINATION'),
    help='Create a season poster with the given assets')
season_poster_group.add_argument(
    '--season-text',
    type=str,
    default='SEASON ONE',
    metavar='SEASON_TEXT',
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
    help='Specify the font kerning scale (as percentage) for this season poster')
season_poster_group.add_argument(
    '--top-placement',
    action='store_true',
    help='Create the season poster with the logo and season text at the top')
         
# Parse given arguments
args, unknown = parser.parse_known_args()

# Create dictionary of unknown arguments
arbitrary_data = {}
if len(unknown) % 2 == 0 and len(unknown) > 1:
    arbitrary_data = {key: val for key, val in zip(unknown[::2], unknown[1::2])}

# Parse preference file for options that might need it
pp = PreferenceParser(args.preferences)
if not pp.valid:
    exit(1)
set_preference_parser(pp)

# Execute title card related options
if hasattr(args, 'title_card'):
    # Attempt to get local card type, if not, try RemoteCardType
    RemoteFile.reset_loaded_database(pp.database_directory)
    if args.card_type in TitleCard.CARD_TYPES.keys():
        CardClass = TitleCard.CARD_TYPES[args.card_type]
    elif (remote_card := RemoteCardType(args.card_type)).valid:
        CardClass = remote_card.card_class
    else:
        log.error(f'Cannot identify card type "{args.card_type}" as either '
                  f'local or remote card type')
        exit(1)

    # Override unspecified defaults with their class specific defaults
    if args.font == Path('__default'):
        args.font = Path(str(CardClass.TITLE_FONT))
    if args.font_color == '__default':
        args.font_color = CardClass.TITLE_COLOR
    
    # Create the given card
    CardClass(
        episode_text=args.episode,
        source=Path(args.title_card[0]), 
        output_file=Path(args.title_card[1]),
        season_text=('' if not args.season else args.season),
        title='\n'.join(args.title),
        font=args.font.resolve(),
        font_size=float(args.font_size[:-1])/100.0,
        title_color=args.font_color,
        hide_season=(not bool(args.season)),
        blur=args.blur,
        vertical_shift=args.vertical_shift,
        interline_spacing=args.interline_spacing,
        kerning=float(args.kerning[:-1])/100.0,
        stroke_width=float(args.stroke_width[:-1])/100.0,
        **arbitrary_data,
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
        font=args.movie_font,
        font_color=args.movie_font_color,
        font_size=float(args.movie_font_size[:-1])/100.0,
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
                output=Path(file.parent /f'{file.stem}-GenreCard{file.suffix}'),
                font_size=float(args.font_size[:-1])/100.0,
                borderless=args.borderless,
                omit_gradient=args.no_gradient,
            ).create()
            
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


if hasattr(args, 'season_poster'):
    SeasonPoster(
        source=args.season_poster[0],
        logo=args.season_poster[1],
        destination=args.season_poster[2],
        season_text=args.season_text,
        font=args.season_font,
        font_color=args.season_font_color,
        font_size=float(args.season_font_size[:-1])/100.0,
        font_kerning=float(args.season_font_kerning[:-1])/100.0,
        top_placement=args.top_placement,
        omit_gradient=args.no_gradient,
    ).create()