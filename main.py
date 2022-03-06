from argparse import ArgumentParser
from pathlib import Path

from modules.Debug import *
from modules.PreferenceParser import PreferenceParser
from modules.preferences import set_preference_parser
from modules.Manager import Manager

# Default path for a preference file to parse
DEFAULT_PREFERENCE_FILE = Path('preferences.yml')

# Default path for a missing file
DEFAULT_MISSING_FILE = Path('missing.yml')

# Set up argument parser
parser = ArgumentParser(description='Start the TitleCardMaker')
parser.add_argument('-p', '--preference-file', type=Path,
                    default=DEFAULT_PREFERENCE_FILE,
                    metavar='FILE',
                    help='Specify the preference file for the TitleCardMaker')
parser.add_argument('-r', '--run', action='count', default=0,
                    help='Run the TitleCardMaker')
parser.add_argument('-m', '--missing', type=Path, default=DEFAULT_MISSING_FILE,
                    metavar='FILE',
                    help='File to write a list of missing assets to')

# Parse given arguments
args = parser.parse_args()

# Check if preference file exists
if not args.preference_file.exists():
    error(f'Preference file "{args.preference_file.resolve()}" does not exist')
    exit(1)

# Read the preference file, verify it is valid and exit if not
pp = PreferenceParser(args.preference_file)
if not pp.valid:
    exit(1)

# Store the valid preference parser in the global namespace
set_preference_parser(pp)

# Create and run the manager --run many times
tcm = None
for _ in range(args.run):
    tcm = Manager()
    tcm.run()

# Write missing assets
if tcm != None:
    tcm.report_missing(args.missing)
