from argparse import ArgumentParser, SUPPRESS
from dataclasses import dataclass
from os import environ
from pathlib import Path
from re import match, IGNORECASE

try:
    from modules.Debug import log, LOG_FILE
    from modules.EmbyInterface import EmbyInterface
    from modules.EpisodeInfo import EpisodeInfo
    from modules.ImageMaker import ImageMaker
    from modules.JellyfinInterface import JellyfinInterface
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
ENV_IS_DOCKER = 'TCM_IS_DOCKER'
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
parser.add_argument(
    '-ms', '--media-server',
    type=lambda s: str(s).lower(),
    default='plex',
    choices=('emby', 'jellyfin', 'plex'),
    metavar='SERVER',
    help='Which media server to perform Media Server arguments on')

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

# Argument group for the media server
media_server_group = parser.add_argument_group('Media Server')
media_server_group.add_argument(
    '--import-cards', '--import-archive', '--load-archive',
    type=str,
    nargs=2,
    default=SUPPRESS,
    metavar=('ARCHIVE_DIRECTORY', 'LIBRARY'),
    help='Import an archive of Title Cards into Emby/Jellyfin/Plex')
media_server_group.add_argument(
    '--import-series', '--load-series',
    type=str,
    nargs='+',
    default=SUPPRESS,
    metavar=('NAME', 'YEAR'),
    help='Override/set the name of the series imported with --import-archive')
media_server_group.add_argument(
    '--import-extension', '--import-ext',
    type=str,
    choices=ImageMaker.VALID_IMAGE_EXTENSIONS,
    default='.jpg',
    metavar='.EXT',
    help='Extension of images to look for alongside --import-cards')
media_server_group.add_argument(
    '--forget-cards', '--forget-loaded-cards',
    type=str,
    nargs=3,
    default=SUPPRESS,
    metavar=('LIBRARY', 'NAME', 'YEAR'),
    help='Remove records of the loaded cards for the given series/library')
media_server_group.add_argument(
    '--revert-series',
    type=str,
    nargs=3,
    default=SUPPRESS,
    metavar=('LIBRARY', 'NAME', 'YEAR'),
    help='Remove the cards for the given series within Emby/Jellyfin/Plex')
media_server_group.add_argument(
    '--id', '--series-id',
    type=str,
    nargs=2,
    default=[],
    action='append',
    metavar=('ID_TYPE', 'ID'),
    help='Specify database IDs of a series for importing/reloading cards')

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

# Parse given arguments
args = parser.parse_args()
is_docker = environ.get(ENV_IS_DOCKER, 'false').lower() == 'true'

# Parse preference file for options that might need it
if not (pp := PreferenceParser(args.preferences, is_docker)).valid:
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


# Execute Media Server options
if ((hasattr(args, 'import_cards') or hasattr(args, 'revert_series'))
    and any((pp.use_emby, pp.use_jellyfin, pp.use_plex))):
    # Temporary classes
    @dataclass
    class Episode: # pylint: disable=missing-class-docstring
        destination: Path
        episode_info: EpisodeInfo
        spoil_type: str

    # Create MediaServer Interface
    try:
        if args.media_server == 'emby':
            media_interface = EmbyInterface(**pp.emby_interface_kwargs)
        elif args.media_server == 'jellyfin':
            media_interface = JellyfinInterface(**pp.jellyfin_interface_kwargs)
        else:
            media_interface = PlexInterface(**pp.plex_interface_kwargs)
    except Exception as e:
        log.critical(f'Cannot connect to "{args.media_server}" Media Server')
        exit(1)

    # Get series/name + year from archive directory if unspecified
    if hasattr(args, 'import_cards'):
        archive = Path(args.import_cards[0])
        library = args.import_cards[1]
        if hasattr(args, 'import_series'):
            series_info = SeriesInfo(*args.import_series)
        else:
            # Try and identify Series from folder name, then parent name
            for folder_name in (archive.name, archive.parent.name):
                groups = match(
                    r'^(.*)\s+\((\d{4})\)(?:\s*[\{\[].*[\}\]])?$',
                    folder_name
                )
                if groups:
                    series_info = SeriesInfo(*groups.groups())
                    break
                else:
                    log.critical(f'Cannot identify series name/year; specify '
                                 f'with --import-series')
                    exit(1)
    else:
        series_info = SeriesInfo(args.revert_series[1], args.revert_series[2])
        archive = pp.source_directory / series_info.full_clean_name
        library = args.revert_series[0]

    # Get series database ID's
    if args.id:
        for id_type, id_ in args.id:
            try:
                getattr(series_info, f'set_{id_type}_id')(id_)
            except Exception as e:
                log.error(f'Unrecognized ID type "{id_type}" - {e}')
    media_interface.set_series_ids(library, series_info)

    # Forget cards associated with this series
    media_interface.remove_records(library, series_info)
            
    # Get all images from import archive
    ext = args.import_extension
    if len(all_images := list(archive.glob(f'**/*{ext}'))) == 0:
        log.warning(f'No images to import')
        exit(1)

    # For each image, fill out episode map to load into server
    episode_infos, episode_map = [], {}
    for image in all_images:
        if (groups := match(r'.*s(\d+).*e(\d+)', image.name, IGNORECASE)):
            season, episode = map(int, groups.groups())
        else:
            log.warning(f'Cannot identify index of {image.resolve()}, skipping')
            continue

        # Import image into library
        episode_infos.append((episode_info := EpisodeInfo('', season, episode)))
        ep = Episode(image, episode_info, 'spoiled')
        episode_map[f'{season}-{episode}'] = ep

    # Set EpisodeInfo database ID's
    media_interface.set_episode_ids(
        library_name=library, series_info=series_info,
        episode_infos=episode_infos, inplace=True
    )

    # Load images into server
    media_interface.set_title_cards(library, series_info, episode_map)

# Create interface and remove records for indicated series+library
if (hasattr(args, 'forget_cards')
    and any((pp.use_emby, pp.use_jellyfin, pp.use_plex))):
    series_info = SeriesInfo(args.forget_cards[1], args.forget_cards[2])
    if args.media_server == 'emby':
        EmbyInterface(**pp.emby_interface_kwargs).remove_records(
            args.forget_cards[0], series_info,
        )
    elif args.media_server == 'jellyfin':
        JellyfinInterface(**pp.jellyfin_interface_kwargs).remove_records(
            args.forget_cards[0], series_info,
        )
    else:
        PlexInterface(**pp.plex_interface_kwargs).remove_records(
            args.forget_cards[0], series_info,
        )


# Execute Sonarr related options
if args.sonarr_list_ids and pp.use_sonarr:
    SonarrInterface(**pp.sonarr_kwargs[0]).list_all_series_id()

# Execute TMDB related options
if hasattr(args, 'unblacklist'):
    TMDbInterface.unblacklist(
        SeriesInfo(args.unblacklist[0], args.unblacklist[1])
    )

if hasattr(args, 'delete_blacklist') and args.delete_blacklist:
    TMDbInterface.delete_blacklist(pp.database_directory)

if hasattr(args, 'tmdb_download_images') and pp.use_tmdb:
    for arg_set in args.tmdb_download_images:
        try:
            start, end = map(int, arg_set[3].split('-'))
            episode_range = range(start, end+1)
        except ValueError:
            log.error(f'Invalid episode range, specify like "START-END", e.g. '
                      f'2-10 for episodes 2 through 10')
            continue

        tmdb_interface = TMDbInterface(**pp.tmdb_interface_kwargs)
        tmdb_interface.manually_download_season(
            title=arg_set[0],
            year=int(arg_set[1]),
            season_number=int(arg_set[2]),
            episode_range=episode_range,
            directory=Path(arg_set[4]),
        )
