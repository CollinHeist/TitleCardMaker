from argparse import ArgumentParser, ArgumentTypeError, SUPPRESS
from pathlib import Path
from os import environ
from re import match
from time import sleep

try:
    from datetime import datetime, timedelta
    import schedule

    from modules.Debug import log, apply_no_color_formatter
    from modules.FontValidator import FontValidator
    from modules.PreferenceParser import PreferenceParser
    from modules.RemoteFile import RemoteFile
    from modules.global_objects import set_preference_parser, set_font_validator
    from modules.Manager import Manager
except ImportError:
    print(f'Required Python packages are missing - execute "pipenv install"')
    exit(1)

# Environment variables
ENV_PREFERENCE_FILE = 'TCM_PREFERENCES'
ENV_RUNTIME = 'TCM_RUNTIME'
ENV_FREQUENCY = 'TCM_FREQUENCY'
ENV_MISSING_FILE = 'TCM_MISSING'
ENV_LOG_LEVEL = 'TCM_LOG'

# Default values
DEFAULT_PREFERENCE_FILE = Path(__file__).parent / 'preferences.yml'
DEFAULT_MISSING_FILE = Path(__file__).parent / 'missing.yml'
DEFAULT_FREQUENCY = '12h'

# Pseudo-type functions for argument runtime and frequency
def runtime(arg: str) -> dict:
    try:
        hour, minute = map(int, arg.split(':'))
        assert hour in range(0, 24) and minute in range(0, 60)
        return {'hour': hour, 'minute': minute}
    except Exception:
        raise ArgumentTypeError(f'Invalid time, specify as HH:MM')

def frequency(arg: str) -> dict:
    try:
        interval, unit = match(r'(\d+)(s|m|h|d|w)', arg).groups()
        interval, unit = int(interval), unit.lower()
        assert interval > 0 and unit in ('s', 'm', 'h', 'd', 'w')
        return {
            'interval': interval,
            'unit': {'s': 'seconds', 'm':'minutes', 'h':'hours', 'd':'days',
                     'w':'weeks'}[unit],
        }
    except Exception:
        raise ArgumentTypeError(f'Invalid frequency, specify as FREQUENCY[unit]'
                                f', i.e. 12h -> 12 hours, 1d -> 1 day')

# Set up argument parser
parser = ArgumentParser(description='Start the TitleCardMaker')
parser.add_argument(
    '-p', '--preferences', '--preference-file',
    type=Path,
    default=environ.get(ENV_PREFERENCE_FILE, DEFAULT_PREFERENCE_FILE),
    metavar='FILE',
    help=f'File to read global preferences from. Environment variable '
         f'{ENV_PREFERENCE_FILE}. Defaults to '
         f'"{DEFAULT_PREFERENCE_FILE.resolve()}"')
parser.add_argument(
    '-r', '--run',
    action='store_true',
    help='Run the TitleCardMaker')
parser.add_argument(
    '-t', '--runtime', '--time', 
    type=runtime,
    default=environ.get(ENV_RUNTIME, SUPPRESS),
    metavar='HH:MM',
    help=f'When to first run the TitleCardMaker (in 24-hour time). Environment '
         f'variable {ENV_RUNTIME}')
parser.add_argument(
    '-f', '--frequency',
    type=frequency,
    default=environ.get(ENV_FREQUENCY, DEFAULT_FREQUENCY),
    metavar='FREQUENCY[unit]',
    help=f'How often to run the TitleCardMaker. Units can be s/m/h/d/w for '
         f'seconds/minutes/hours/days/weeks. Environment variable '
         f'{ENV_FREQUENCY}. Defaults to "{DEFAULT_FREQUENCY}"')
parser.add_argument(
    '-m', '--missing', '--missing-file',
    type=Path,
    default=environ.get(ENV_MISSING_FILE, DEFAULT_MISSING_FILE),
    metavar='FILE',
    help=f'File to write the list of missing assets to. Environment variable '
         f'{ENV_MISSING_FILE}. Defaults to "{DEFAULT_MISSING_FILE.resolve()}"')
parser.add_argument(
    '-l', '--log',
    choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
    default=environ.get(ENV_LOG_LEVEL, 'INFO'),
    help=f'Level of logging verbosity to use. Environment variable '
         f'{ENV_LOG_LEVEL}. Defaults to "INFO"')
parser.add_argument(
    '-nc', '--no-color',
    action='store_true',
    help='Omit color from all print messages')

# Parse given arguments
args = parser.parse_args()

# Set global log level and coloring
log.handlers[0].setLevel(args.log)
if args.no_color:
    apply_no_color_formatter(log)

# Check if preference file exists
if not args.preferences.exists():
    log.critical(f'Preference file "{args.preferences.resolve()}" does not exist')
    exit(1)

# Read the preference file, verify it is valid and exit if not
if not (pp := PreferenceParser(args.preferences)).valid:
    exit(1)

# Store the PreferenceParser and FontValidator in the global namespace
set_preference_parser(pp)
set_font_validator(FontValidator())

# Function to create and run Manager object
def run():
    # Reset previously loaded assets
    RemoteFile.LOADED.truncate()

    # Create Manager, run, and write missing report
    try:
        tcm = Manager()
        tcm.run()
        tcm.report_missing(args.missing)
    except PermissionError as error:
        log.critical(f'Invalid permissions - {error}')
        exit(1)

# Run immediately if specified
if args.run:
    run()

# Schedule subsequent runs if specified
if hasattr(args, 'runtime'):
    # Get current time and first run before starting schedule
    today = datetime.today()
    first_run = datetime(today.year, today.month, today.day, **args.runtime)
    first_run += timedelta(days=int(first_run < today))

    # Sleep until first run
    sleep_seconds = (first_run - today).total_seconds()
    log.info(f'Starting first run in {int(sleep_seconds)} seconds')
    sleep(sleep_seconds)
    run()

    # Set schedule to execute based on given frequency
    interval, unit = args.frequency['interval'], args.frequency['unit']
    getattr(schedule.every(interval), unit).do(run)

    # Infinite loop of TCM Execution
    while True:
        # Run schedule, sleep until next run
        schedule.run_pending()
        next_run = schedule.next_run().strftime("%H:%M:%S %Y-%m-%d")
        log.info(f'Sleeping until {next_run}')
        sleep(max(0, (schedule.next_run()-datetime.today()).total_seconds()))

