from argparse import ArgumentParser, ArgumentTypeError, SUPPRESS
from dataclasses import dataclass
from pathlib import Path
from re import match, IGNORECASE

try:
    from yaml import dump

    from modules.Debug import log
    from modules.DataFileInterface import DataFileInterface
    from modules.EpisodeInfo import EpisodeInfo
    from modules.PlexInterface import PlexInterface
    from modules.PreferenceParser import PreferenceParser
    from modules.preferences import set_preference_parser
    from modules.SeriesInfo import SeriesInfo
    from modules.ShowSummary import ShowSummary
    from modules.SonarrInterface import SonarrInterface
    from modules.TMDbInterface import TMDbInterface
except ImportError:
    print(f'Required Python packages are missing - execute "pipenv install"')
    exit(1)

# Default path for the preference file to parse
DEFAULT_PREFERENCE_FILE = Path(__file__).parent / 'preferences.yml'

# Old commands that have moved to mini_maker to warn user about
OLD_COMMANDS = ('--title-card', '--genre-card', '--show-summary')

# Create ArgumentParser object 
parser = ArgumentParser(description='Manual fixes for the TitleCardMaker')
parser.add_argument(
    '-p', '--preference-file',
    type=Path, 
    default=DEFAULT_PREFERENCE_FILE,
    metavar='PREFERENCE_FILE',
    help='Preference YAML file for global options')

# Argument group for Miscellaneous functions
misc_group = parser.add_argument_group('Miscellaneous')
misc_group.add_argument(
    '--import-archive', '--load-archive',
    type=str,
    nargs=2,
    default=SUPPRESS,
    metavar=('ARCHIVE_DIRECTORY', 'PLEX_LIBRARY'),
    help='Import an archive of Title Cards into Plex')
misc_group.add_argument(
    '--import-series', '--load-series',
    type=str,
    nargs=2,
    default=SUPPRESS,
    metavar=('NAME', 'YEAR'),
    help='Override/set the name of the series imported with --import-archive')
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

# Argument group for Sonarr
sonarr_group = parser.add_argument_group('Sonarr')
sonarr_group.add_argument(
    '--read-all-series',
    type=Path,
    default=SUPPRESS,
    metavar='FILE',
    help='Create a generic series YAML file for all the series in Sonarr')
sonarr_group.add_argument(
    '--read-tags',
    nargs='+',
    type=str,
    default=[],
    metavar='TAG',
    help='Any number of Sonarr tags to filter series of --read-all-series by')
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
if any(old_arg in unknown for old_arg in OLD_COMMANDS):
    log.warning(f'Manual card creation has moved to "mini_maker.py"')

# Parse preference file for options that might need it
pp = PreferenceParser(args.preference_file)
if not pp.valid:
    exit(1)
set_preference_parser(pp)

# Execute Miscellaneous options
if hasattr(args, 'import_archive') and pp.use_plex:
    # Temporary classes
    @dataclass
    class Episode:
        destination: Path
        episode_info: EpisodeInfo
        spoil_type: str
        
    # Create PlexInterface
    if not pp.use_plex:
        log.critical(f'Cannot import archive if Plex is disabled')
        exit(1)
    plex_interface = PlexInterface(pp.plex_url, pp.plex_token)

    # Get series/name + year from archive directory if unspecified
    archive = Path(args.import_archive[0])
    if hasattr(args, 'import_series'):
    	series_info = SeriesInfo(*args.import_series)
    else:
        if (groups := match(r'^(.*) \((\d+)\)$', archive.parent.name)):
            series_info = SeriesInfo(*groups.groups())
        else:
            log.critical(f'Cannot identify series name/year; specify with '
                         f'--import-series')
            exit(1)
            
    # Get all images from import archive
    if len(all_images := list(archive.glob('**/*.jpg'))) == 0:
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
    	args.import_archive[1],
    	series_info,
    	episode_map
    )
    
    
for directory in args.delete_cards:
    # Get all images in this directory
    directory = Path(directory)
    images = tuple(directory.glob(f'**/*{args.delete_extension}'))

    # If no images to delete, skip
    if len(images) == 0:
        log.info(f'No images to delete from "{directory.resolve()}"')
        continue

    # Ask user to confirm deletion
    log.warning(f'Deleting {len(images)} images from "{directory.resolve()}"')
    confirmation = input(f'  Continue [Y/N]?  ')
    if confirmation in ('y', 'Y', 'yes', 'YES'):
        # Delete each image returned by glob
        for image in images:
            image.unlink()
            log.debug(f'Deleted {image.resolve()}')

# Execute Sonarr related options
if hasattr(args, 'read_all_series') and pp.use_sonarr:
    # Create SonarrInterface
    si = SonarrInterface(pp.sonarr_url, pp.sonarr_api_key)

    # Create YAML
    yaml = {'libraries': {}, 'series': {}}
    for series_info, media_directory in si.get_series(args.read_tags):
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

    log.info(f'Wrote {len(yaml["series"])} series to '
             f'{args.read_all_series.resolve()}')

if args.sonarr_list_ids and pp.use_sonarr:
    SonarrInterface(pp.sonarr_url, pp.sonarr_api_key).list_all_series_id()

# Execute TMDB related options
if hasattr(args, 'delete_blacklist'):
    if args.delete_blacklist:
        TMDbInterface.delete_blacklist()

if hasattr(args, 'tmdb_download_images') and pp.use_tmdb:
    for arg_set in args.tmdb_download_images:
        TMDbInterface.manually_download_season(
            api_key=pp.tmdb_api_key,
            title=arg_set[0],
            year=int(arg_set[1]),
            season=int(arg_set[2]),
            episode_count=int(arg_set[3]),
            directory=Path(arg_set[4]),
        )

if hasattr(args, 'add_translation') and pp.use_tmdb:
    dfi = DataFileInterface(Path(args.add_translation[2]))
    tmdbi = TMDbInterface(pp.tmdb_api_key)

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

