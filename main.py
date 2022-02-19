from argparse import ArgumentParser
from pathlib import Path

from modules.Debug import *
from modules.PreferenceParser import PreferenceParser
from modules.preferences import set_preference_parser
from modules.Manager import Manager

# Default path for a preference file to parse
DEFAULT_PREFERENCE_FILE = Path('preferences.yml')

# Set up argument parser
parser = ArgumentParser(description='Start the TitleCardMaker')
parser.add_argument('-p', '--preference-file', type=Path,
                    default=DEFAULT_PREFERENCE_FILE,
                    help='Manually specify the preference file for the TitleCardMaker')
parser.add_argument('-r', '--run', action='count', default=0,
                    help='How many times to run the TitleCardMaker back-to-back')

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
for _ in range(args.run):
    tcm = Manager()
    tcm.run()