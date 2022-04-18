from argparse import ArgumentParser
from pathlib import Path

try:
    from modules.Debug import log, apply_no_color_formatter
    from modules.FontValidator import FontValidator
    from modules.PreferenceParser import PreferenceParser
    from modules.preferences import set_preference_parser, set_font_validator
    from modules.Manager import Manager
except ImportError:
    print(f'Required Python packages are missing - execute "pipenv install"')
    exit(1)

# Default path for the preference file to parse
DEFAULT_PREFERENCE_FILE = Path(__file__).parent / 'preferences.yml'

# Default path for the missing file to write to
DEFAULT_MISSING_FILE = Path(__file__).parent / 'missing.yml'

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
    action='count',
    default=0,
    help='Run the TitleCardMaker')
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

# Create and run the manager --run many times
tcm = None
for _ in range(args.run):
    tcm = Manager()
    tcm.run()

# Write missing assets
if tcm != None:
    tcm.report_missing(args.missing)
