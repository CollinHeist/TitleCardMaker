from argparse import ArgumentParser, ArgumentTypeError, SUPPRESS
from pathlib import Path

try:
    from modules.DataFileInterface import DataFileInterface
    from modules.GenreMaker import GenreMaker
    from modules.PreferenceParser import PreferenceParser
    from modules.preferences import set_preference_parser
    from modules.SonarrInterface import SonarrInterface
    from modules.TitleCard import TitleCard
    from modules.TMDbInterface import TMDbInterface
except ImportError:
    print(f'Required Python packages are missing - execute "pipenv install"')
    exit(1)

parser = ArgumentParser(description='Manual fixes for the TitleCardMaker')
parser.add_argument('-p', '--preference-file', type=Path, 
                    default='preferences.yml', metavar='PREFERENCE_FILE',
                    help='Preference YAML file for parsing '
                         'ImageMagick/Sonarr/TMDb options')

# Argument group for 'manual' title card creation
title_card_group = parser.add_argument_group('Title Cards',
                                             'Manual TitleCardMaker interaction')
title_card_group.add_argument(
    '--card-type',
    type=str,
    default='standard',
    choices=TitleCard.CARD_TYPES.keys(),
    metavar='TYPE',
    help='Create a title card of a specific type')
title_card_group.add_argument(
    '--title-card',
    type=Path,
    nargs=2,
    default=SUPPRESS,
    metavar=('SOURCE', 'DESTINATION'),
    help='Create a title card with the given source image, written to the given'
         ' destination')
title_card_group.add_argument(
    '--episode',
    type=str,
    default='EPISODE',
    metavar='EPISODE_TEXT',
    help="Specify this card's episode text")
title_card_group.add_argument(
    '--season',
    type=str,
    default=None,
    metavar='SEASON_TEXT',
    help="Specify this card's season text")
title_card_group.add_argument(
    '--title',
    type=str,
    nargs='+',
    default='',
    metavar=('TITLE_LINE'),
    help="Specify this card's title text")
title_card_group.add_argument(
    '--font', '--font-file',
    type=Path,
    default='__default',
    metavar='FONT_FILE',
    help="Specify this card's custom font")
title_card_group.add_argument(
    '--font-size', '--size',
    type=str,
    default='100%',
    metavar='SCALE%',
    help='Specify a custom font scale (as percentage)')
title_card_group.add_argument(
    '--font-color', '--color',
    type=str, 
    default='__default',
    metavar='#HEX',
    help='Specify a custom font color to use for this card')
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
    help='How many pixels to increase the interline spacing of for title text')

# Argument group for genre maker
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

# Argument group for fixes relating to Sonarr
sonarr_group = parser.add_argument_group('Sonarr')
sonarr_group.add_argument(
    '--sonarr-list-ids',
    action='store_true',
    help="Whether to list all the ID's for all shows within Sonarr")

# Argument group for fixes relating to TheMovieDatabase
tmdb_group = parser.add_argument_group(
    'TheMovieDatabase',
    'Fixes for how the Maker interacts with TheMovieDatabase')
tmdb_group.add_argument(
    '--tmdb-download-images',
    nargs=6,
    default=SUPPRESS,
    action='append',
    metavar=('API_KEY', 'TITLE', 'YEAR', 'SEASON', 'EPISODES', 'DIRECTORY'),
    help='Download the best title card source image for the given episode')
tmdb_group.add_argument(
    '--delete-blacklist',
    action='store_true',
    help='Whether to delete the existing TMDb blacklist')
tmdb_group.add_argument(
    '--add-translation',
    nargs=5,
    default=SUPPRESS,
    metavar=('TITLE', 'YEAR', 'DATAFILE', 'LANGUAGE_CODE', 'LABEL'),
    help='Add title translations from TMDb to the given datafile')

# Parse given arguments
args, unknown = parser.parse_known_args()

# Create dictionary of unknown arguments
arbitrary_data = {}
if len(unknown) % 2 == 0 and len(unknown) > 1:
    arbitrary_data = {key: val for key, val in zip(unknown[::2], unknown[1::2])}

# Parse preference file for options that might need it
pp = PreferenceParser(args.preference_file)
if not pp.valid:
    exit(1)
set_preference_parser(pp)

# Override unspecified defaults with their class specific defaults
if args.font == Path('__default'):
    args.font = Path(TitleCard.CARD_TYPES[args.card_type].TITLE_FONT)
if args.font_color == '__default':
    args.font_color = TitleCard.CARD_TYPES[args.card_type].TITLE_COLOR

# Execute title card related options
if hasattr(args, 'title_card'):
    TitleCard.CARD_TYPES[args.card_type](
        episode_text=args.episode,
        source=Path(args.title_card[0]), 
        output_file=Path(args.title_card[1]),
        season_text=('' if not args.season else args.season),
        title='\n'.join(args.title),
        font=args.font.resolve(),
        font_size=float(args.font_size[:-1])/100.0,
        title_color=args.font_color,
        hide_season=(not bool(args.season)),
        vertical_shift=args.vertical_shift,
        interline_spacing=args.interline_spacing,
        **arbitrary_data,
    ).create()

# Execute genre card related options
if hasattr(args, 'genre_card'):
    GenreMaker(
        source=Path(args.genre_card[0]),
        genre=args.genre_card[1],
        output=Path(args.genre_card[2]),
        font_size=float(args.font_size[:-1])/100.0,
    ).create()

if hasattr(args, 'genre_card_batch'):
    for file in args.genre_card_batch.glob('*'):
        if file.suffix.lower() in GenreMaker.VALID_IMAGE_EXTENSIONS:
            GenreMaker(
                source=file,
                genre=file.stem.upper(),
                output=Path(file.parent /f'{file.stem}-GenreCard{file.suffix}'),
                font_size=float(args.font_size[:-1])/100.0,
            ).create()

# Execute Sonarr related options
if args.sonarr_list_ids:
    if not pp.use_sonarr:
        log.warning("Cannot print Sonarr ID's if Sonarr is disabled")
    else:
        SonarrInterface(pp.sonarr_url, pp.sonarr_api_key).list_all_series_id()

# Execute TMDB related options
if hasattr(args, 'delete_blacklist'):
    if args.delete_blacklist:
        TMDbInterface.delete_blacklist()

if hasattr(args, 'tmdb_download_images'):
    for arg_set in args.tmdb_download_images:
        TMDbInterface.manually_download_season(
            api_key=arg_set[0],
            title=arg_set[1],
            year=int(arg_set[2]),
            season=int(arg_set[3]),
            episode_count=int(arg_set[4]),
            directory=Path(arg_set[5]),
        )

if hasattr(args, 'add_language'):
    dfi = DataFileInterface(Path(args.add_language[2]))
    tmdbi = TMDbInterface(pp.tmdb_api_key)

    for entry in dfi.read():
        if args.add_language[4] in entry:
            continue

        new_title = tmdbi.get_episode_title(
            title=args.add_language[0],
            year=args.add_language[1],
            season=entry['season_number'],
            episode=entry['episode_number'],
            language_code=args.add_language[3],
        )

        if new_title == None:
            continue

        dfi.modify_entry(**entry, **{args.add_language[4]: new_title})

