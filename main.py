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
    from modules.preferences import set_preference_parser, set_font_validator
    from modules.Manager import Manager
except ImportError:
    print(f'Required Python packages are missing - execute "pipenv install"')
    exit(1)

# Environment variables
RUNTIME_ENV = 'TCM_RUNTIME'
FREQUENCY_ENV = 'TCM_FREQUENCY'

# Default path for the preference file to parse
DEFAULT_PREFERENCE_FILE = Path(__file__).parent / 'preferences.yml'

# Default path for the missing file to write to
DEFAULT_MISSING_FILE = Path(__file__).parent / 'missing.yml'

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
        interval, unit = match(r'(\d+)(m|h|d|w)', arg).groups()
        interval, unit = int(interval), unit.lower()
        assert interval > 0 and unit in ('m', 'h', 'd', 'w')
        return {
            'interval': interval,
            'unit': {'m':'minutes', 'h':'hours', 'd':'days', 'w':'weeks'}[unit]
        }
    except Exception:
        raise ArgumentTypeError(f'Invalid frequency, specify as FREQUENCY[unit]'
                                f', i.e. 12h -> 12 hours, 1d -> 1 day')

# Set up argument parser
parser = ArgumentParser(description='Start the TitleCardMaker')
parser.add_argument(
    '-p', '--preference-file',
    type=Path,
    default=DEFAULT_PREFERENCE_FILE,
    metavar='FILE',
    help='Specify the global preferences file')
parser.add_argument(
    '-r', '--run',
    action='store_true',
    help='Run the TitleCardMaker')
parser.add_argument(
    '-t', '--time', '--runtime',
    dest='runtime',
    type=runtime,
    default=environ.get(RUNTIME_ENV, SUPPRESS),
    metavar='HH:MM',
    help='When to first run the TitleCardMaker (in 24-hour time)')
parser.add_argument(
    '-f', '--frequency',
    type=frequency,
    default=environ.get(FREQUENCY_ENV, '12h'),
    metavar='FREQUENCY[unit]',
    help='How often to run the TitleCardMaker (default "12h"). Units can be '
         'm/h/d/w for minutes/hours/days/weeks')
parser.add_argument(
    '-m', '--missing', 
    type=Path,
    default=DEFAULT_MISSING_FILE,
    metavar='FILE',
    help='File to write the list of missing assets to')
parser.add_argument(
    '-l', '--log',
    choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
    default='INFO',
    help='Level of logging verbosity to use')
parser.add_argument(
    '-nc', '--no-color',
    action='store_true',
    help='Whether to omit color from all print messages')

# Parse given arguments
args = parser.parse_args()

# Set global log level and coloring
log.setLevel(args.log)
if args.no_color:
    apply_no_color_formatter(log)

# Check if preference file exists
if not args.preference_file.exists():
    log.critical(f'Preference file "{args.preference_file.resolve()}" does not '
                 f'exist')
    exit(1)

# Read the preference file, verify it is valid and exit if not
if not (pp := PreferenceParser(args.preference_file)).valid:
    exit(1)

# Store the PreferenceParser and FontValidator in the global namespace
set_preference_parser(pp)
set_font_validator(FontValidator())

# Function to create and run Manager object
def run():
    # Create Manager, run, and write missing report
    tcm = Manager()
    tcm.run()
    tcm.report_missing(args.missing)

# Run immediately if specified
if args.run:
    from cProfile import Profile
    from pstats import Stats

    with Profile() as pr:
        run()

    stats = Stats(pr)
    stats.dump_stats(filename='all.prof')   

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

