from argparse import ArgumentParser, ArgumentTypeError, SUPPRESS
from dataclasses import dataclass
from os import environ
from pathlib import Path
from re import match, IGNORECASE

try:
    from yaml import dump

    from modules.Debug import log, LOG_FILE
    from modules.DataFileInterface import DataFileInterface
    from modules.EpisodeInfo import EpisodeInfo
    from modules.ImageMaker import ImageMaker
    from modules.PlexInterface import PlexInterface
    from modules.PreferenceParser import PreferenceParser
    from modules.global_objects import set_preference_parser
    from modules.SeriesInfo import SeriesInfo
    from modules.SonarrInterface import SonarrInterface
    from modules.TMDbInterface import TMDbInterface
except ImportError:
    print(f'Required Python packages are missing - execute "pipenv install"')
    exit(1)

# Environment Variables
ENV_PREFERENCE_FILE = 'TCM_PREFERENCES'

# Default values
DEFAULT_PREFERENCE_FILE = Path(__file__).parent / 'preferences.yml'

# Create ArgumentParser object 
parser = ArgumentParser(description='Manual fixes for the TitleCardMaker')
parser.add_argument(
    '-p', '--preferences', '--preference-file',
    type=Path,
    default=environ.get(ENV_PREFERENCE_FILE, DEFAULT_PREFERENCE_FILE),
    metavar='FILE',
    help=f'File to read global preferences from. Environment variable '
         f'{ENV_PREFERENCE_FILE}. Defaults to '
         f'"{DEFAULT_PREFERENCE_FILE.resolve()}"')

# Argument group for Miscellaneous functions
misc_group = parser.add_argument_group('Miscellaneous')
misc_group.add_argument(
    '--delete-cards',
    nargs='+',
    default=[],
    metavar='DIRECTORY',
    help='Delete all images with the specified directory(ies)')
misc_group.add_argument(
    '--delete-extension',
    type=str,
    default='.jpg',
    metavar='EXTENSION',
    help='Extension of images to delete with --delete-cards')
misc_group.add_argument(
    '--print-log',
    action='store_true',
    default=SUPPRESS,
    help='Print the last log file')

# Argument group for Plex
plex_group = parser.add_argument_group('Plex')
plex_group.add_argument(
    '--import-cards', '--import-archive', '--load-archive',
    type=str,
    nargs=2,
    default=SUPPRESS,
    metavar=('ARCHIVE_DIRECTORY', 'PLEX_LIBRARY'),
    help='Import an archive of Title Cards into Plex')
plex_group.add_argument(
    '--import-series', '--load-series',
    type=str,
    nargs='+',
    default=SUPPRESS,
    metavar=('NAME', 'YEAR'),
    help='Override/set the name of the series imported with --import-archive')
plex_group.add_argument(
    '--import-extension', '--import-ext',
    type=str,
    choices=ImageMaker.VALID_IMAGE_EXTENSIONS,
    default='.jpg',
    metavar='.EXT',
    help='Extension of images to look for alongside --import-cards')
plex_group.add_argument(
    '--forget-cards', '--forget-loaded-cards',
    type=str,
    nargs=3,
    default=SUPPRESS,
    metavar=('PLEX_LIBRARY', 'NAME', 'YEAR'),
    help='Remove records of the loaded cards for the given series/library')

# Argument group for Sonarr
sonarr_group = parser.add_argument_group('Sonarr')
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
    metavar=('TITLE', 'YEAR', 'SEASON', 'EPISODE_RANGE', 'DIRECTORY'),
    help='Download the title card source images for the given season of the '
         'given series')
tmdb_group.add_argument(
    '--unblacklist',
    nargs=2,
    type=str,
    default=SUPPRESS,
    metavar=('TITLE', 'YEAR'),
    help='Unblacklist all requests for the given series')
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
args = parser.parse_args()

# Parse preference file for options that might need it
pp = PreferenceParser(args.preferences)
if not pp.valid:
    exit(1)
set_preference_parser(pp)

# Execute miscellaneous arguments
for directory in args.delete_cards:
    # Get all images in this directory
    directory = Path(directory)
    images = tuple(directory.glob(f'**/*{args.delete_extension}'))

    # If no images to delete, skip
    if len(images) == 0:
        log.info(f'No images to delete from "{directory.resolve()}"')
        continue

    # Log each image to be deleted
    base_length = len(str(directory.resolve()))
    for image in images:
        log.info(f'Identified [...]{str(image.resolve())[base_length:]}')

    # Ask for confirmation
    log.warning(f'Deleting {len(images)} images from "{directory.resolve()}"')
    confirmation = input(f'  Continue [Y/N]? ')

    # Delete each image
    if confirmation in ('y', 'Y', 'yes', 'YES'):
        for image in images:
            image.unlink()
            log.debug(f'Deleted {image.resolve()}')
    else:
        log.info(f'Not deleting any images')

if hasattr(args, 'print_log') and args.print_log:
    if LOG_FILE.exists():
        with LOG_FILE.open('r') as file_handle:
            print(file_handle.read())


# Execute Plex options
if hasattr(args, 'import_cards') and pp.use_plex:
    # Temporary classes
    @dataclass
    class Episode:
        destination: Path
        episode_info: EpisodeInfo
        spoil_type: str
        
    # Create PlexInterface
    plex_interface = PlexInterface(**pp.plex_interface_kwargs)

    # Get series/name + year from archive directory if unspecified
    archive = Path(args.import_cards[0])
    if hasattr(args, 'import_series'):
        series_info = SeriesInfo(*args.import_series)
    else:
        if (groups := match(r'^(.*)\s+\((\d{4})\)$', archive.parent.name)):
            series_info = SeriesInfo(*groups.groups())
        else:
            log.critical(f'Cannot identify series name/year; specify with '
                         f'--import-series')
            exit(1)

    # Forget cards associated with this series
    plex_interface.remove_records(args.import_cards[1], series_info)
            
    # Get all images from import archive
    ext = args.import_extension
    if len(all_images := list(archive.glob(f'**/*{ext}'))) == 0:
        log.warning(f'No images to import')
        exit(1)
    
    # For each image, fill out episode map to load into Plex
    episode_map = {}
    for image in all_images:
        if (groups := match(r'.*s(\d+).*e(\d+)', image.name, IGNORECASE)):
            season, episode = map(int, groups.groups())
        else:
            log.warning(f'Cannot identify index of {image.resolve()}, skipping')
            continue
            
        # Import image into library
        ep = Episode(image, EpisodeInfo('', season, episode), 'spoiled')
        episode_map[f'{season}-{episode}'] = ep
        
    # Load images into Plex
    plex_interface.set_title_cards_for_series(
    	args.import_cards[1], series_info, episode_map
    )

if hasattr(args, 'forget_cards') and pp.use_plex:
    # Create PlexInterface and remove records for indicated series+library
    series_info = SeriesInfo(args.forget_cards[1], args.forget_cards[2])
    PlexInterface(**pp.plex_interface_kwargs).remove_records(
        args.forget_cards[0], series_info,
    )


# Execute Sonarr related options
if args.sonarr_list_ids and pp.use_sonarr:
    SonarrInterface(**pp.sonarr_interface_kwargs).list_all_series_id()

# Execute TMDB related options
if hasattr(args, 'unblacklist'):
    TMDbInterface.unblacklist(
        pp.database_directory,
        SeriesInfo(args.unblacklist[0], int(args.unblacklist[1]))
    )

if hasattr(args, 'delete_blacklist') and args.delete_blacklist:
    TMDbInterface.delete_blacklist(pp.database_directory)

if hasattr(args, 'tmdb_download_images') and pp.use_tmdb:
    for arg_set in args.tmdb_download_images:
        try:
            start, end = map(int, arg_set[3].split('-'))
            episode_range = range(start, end+1)
        except ValueError:
            log.error(f'Invalid episode range, specify like "START-END", i.e. '
                      f'2-10 for episodes 2 through 10')
            continue

        tmdb_interface = TMDbInterface(pp.database_directory, pp.tmdb_api_key)
        tmdb_interface.manually_download_season(
            title=arg_set[0],
            year=int(arg_set[1]),
            season_number=int(arg_set[2]),
            episode_range=episode_range,
            directory=Path(arg_set[4]),
        )

if hasattr(args, 'add_translation') and pp.use_tmdb:
    dfi = DataFileInterface(Path(args.add_translation[2]))
    tmdbi = TMDbInterface(**pp.tmdb_interface_kwargs)

    for entry in dfi.read():
        if args.add_translation[4] in entry:
            continue

        new_title = tmdbi.get_episode_title(
            title=args.add_translation[0],
            year=args.add_translation[1],
            season=entry['season_number'],
            episode=entry['episode_number'],
            language_code=args.add_translation[3],
        )

        if new_title == None:
            continue

        dfi.modify_entry(**entry, **{args.add_translation[4]: new_title})