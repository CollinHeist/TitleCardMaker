from argparse import ArgumentParser, ArgumentTypeError, SUPPRESS
from dataclasses import dataclass
from pathlib import Path

try:
    from yaml import dump

    from modules.DataFileInterface import DataFileInterface
    from modules.GenreMaker import GenreMaker
    from modules.PreferenceParser import PreferenceParser
    from modules.preferences import set_preference_parser
    from modules.ShowSummary import ShowSummary
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
    '--borderless',
    action='store_true',
    help='Make the specified Genre Card transparent')
genre_group.add_argument(
    '--genre-card-batch',
    type=Path,
    default=SUPPRESS,
    metavar=('SOURCE_DIRECTORY'),
    help='Create all genre cards for images in the given directory based on '
         'their file names')

# Argument group for ShowSummary creation
summary_group = parser.add_argument_group('ShowSummary')
summary_group.add_argument(
    '--show-summary',
    type=Path,
    nargs=2,
    default=SUPPRESS,
    metavar=('IMAGE_DIRECTORY', 'LOGO'),
    help='Create a ShowSummary for the given directory')

# Argument group for Sonarr
sonarr_group = parser.add_argument_group('Sonarr')
sonarr_group.add_argument(
    '--read-all-series',
    type=Path,
    default=SUPPRESS,
    metavar='FILE',
    help='Create a generic series YAML file for all the series in Sonarr')
sonarr_group.add_argument(
    '--sonarr-list-ids',
    action='store_true',
    help="List all the ID's for all shows within Sonarr")

# Argument group for TMDb
tmdb_group = parser.add_argument_group(
    'TheMovieDatabase',
    'Fixes for how the Maker interacts with TheMovieDatabase')
tmdb_group.add_argument(
    '--tmdb-download-images',
    nargs=5,
    default=SUPPRESS,
    action='append',
    metavar=('TITLE', 'YEAR', 'SEASON', 'EPISODES', 'DIRECTORY'),
    help='Download the title card source images for the given season of the '
         'given series')
tmdb_group.add_argument(
    '--delete-blacklist',
    action='store_true',
    help='Delete the existing TMDb blacklist file')
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
        blur=args.blur,
        vertical_shift=args.vertical_shift,
        interline_spacing=args.interline_spacing,
        kerning=float(args.kerning[:-1])/100.0,
        stroke_width=float(args.stroke_width[:-1])/100.0,
        **arbitrary_data,
    ).create()

# Execute genre card related options
if hasattr(args, 'genre_card'):
    GenreMaker(
        source=Path(args.genre_card[0]),
        genre=args.genre_card[1],
        output=Path(args.genre_card[2]),
        font_size=float(args.font_size[:-1])/100.0,
        borderless=args.borderless,
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

# Executer ShowSummary options
if hasattr(args, 'show_summary'):
    # Temporary classes
    @dataclass
    class Episode:
        destination: Path

    @dataclass
    class Show:
        logo: Path
        media_directory: Path
        episodes: dict

    # Get all images in folder
    all_images = args.show_summary[0].glob('**/*.jpg')
    episode = 1
    episodes = {f'1-{(episode := episode+1)}': Episode(f) for f in all_images}
    show = Show(args.show_summary[1], args.show_summary[0], episodes)

    # Create ShowSummary
    ShowSummary(show).create()

# Execute Sonarr related options
if hasattr(args, 'read_all_series'):
    # Create SonarrInterface
    si = SonarrInterface(pp.sonarr_url, pp.sonarr_api_key)

    # Create YAML
    yaml = {'libraries': {}, 'series': {}}
    for series_info, media_directory in si.get_all_series():
        # Add library section
        library = {'path': str(media_directory.parent.resolve())}
        yaml['libraries'][media_directory.parent.name] = library

        # Get series key for this series
        if series_info.name in yaml.get('series', {}):
            if series_info.full_name in yaml.get('series', {}):
                key = f'{series_info.name} ({series_info.tvdb_id})'
            else:
                key = series_info.full_name
        else:
            key = series_info.name

        # Create YAML entry for this series
        yaml['series'][key] = {
            'year': series_info.year,
            'library': media_directory.parent.name,
            'media_directory': str(media_directory.resolve()),
        }

    # Write YAML to the specified file
    with args.read_all_series.open('w', encoding='utf-8') as file_handle:
        dump(yaml, file_handle, allow_unicode=True)

    print(f'\nWrote {len(yaml["series"])} series to '
          f'{args.read_all_series.resolve()}')

if args.sonarr_list_ids:
    if not pp.use_sonarr:
        print("Cannot print Sonarr ID's if Sonarr is disabled")
    else:
        SonarrInterface(pp.sonarr_url, pp.sonarr_api_key).list_all_series_id()

# Execute TMDB related options
if hasattr(args, 'delete_blacklist'):
    if args.delete_blacklist:
        TMDbInterface.delete_blacklist()

if hasattr(args, 'tmdb_download_images'):
    for arg_set in args.tmdb_download_images:
        TMDbInterface.manually_download_season(
            api_key=pp.tmdb_api_key,
            title=arg_set[0],
            year=int(arg_set[1]),
            season=int(arg_set[2]),
            episode_count=int(arg_set[3]),
            directory=Path(arg_set[4]),
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

