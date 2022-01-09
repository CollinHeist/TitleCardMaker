from argparse import ArgumentParser

from DatabaseInterface import DatabaseInterface
from PlexInterface import PlexInterface
import preferences
from SonarrInterface import SonarrInterface
from TitleCardManager import TitleCardManager

# Construct argument parser, adding required arguments
parser = ArgumentParser(description='Setup the TitleCardMaker')
parser.add_argument('config', type=str, 
                    help='Path to the config XML file defining how to create all title cards')

parser.add_argument('source', type=str,
                    help='Directory where all title card source data/images are stored')

# Add optional arguments
parser.add_argument('--archive', type=str, nargs='?',
                    metavar='DIRECTORY',
                    help='Archive directory where all types of title cards are stored')

parser.add_argument('--validate-fonts', action='store_true',
                    help='Check if a font has all the necessary characters before creating any title cards')

parser.add_argument('--interval', type=int, nargs='?', default=600,
                    metavar='INTERVAL',
                    help='How often to execute the main loop of the title card maker')

# Add arguments for Sonarr
sonarr_group = parser.add_argument_group('Sonarr', 'Sonarr options to automatically pull episode titles')
sonarr_group.add_argument('--sonarr', type=str, nargs=2, default=[None, None],
                          metavar=('URL', 'API_KEY'),
                          help='Sonarr URL and API Key - see Sonarr/Settings/General/Security')

# Add arguments for TheMovieDB
tmdb_group = parser.add_argument_group('TheMovieDatabase', 'TheMovieDatabase options to automatically pull title card source images')
tmdb_group.add_argument('--tmdb', type=str, default=None,
                        metavar='KEY',
                        help='TheMovieDB API key - see https://www.themoviedb.org/settings/api')

# Add arguments for Plex
plex_group = parser.add_argument_group('Plex', 'Plex options to automatically refresh title cards')
plex_group.add_argument('--plex', type=str, nargs=2, default=[None, None],
                        metavar=('URL', 'XTOKEN'),
                        help='Plex URL and X-Token - see https://support.plex.tv/articles/204059436')

# Add arguments for interfacing wtih ImageMagick
imagemagick_group = parser.add_argument_group('ImageMagick', 'Options for how to use ImageMagick')
imagemagick_group.add_argument('--magick-docker-id', type=str, default=None,
                               metavar='ID',
                               help='Docker ID of a container running Imagemagick - if unspecified, the host ImageMagick is used')

# Check given arguments
args = parser.parse_args()

# Update global preferences
if args.magick_docker_id:
    preferences.update_imagemagick_docker_id(args.magick_docker_id)
    
# Create TitleCardManager based on provided arguments
tcm = TitleCardManager(
    args.config,
    args.source,
    args.archive,
    SonarrInterface(*args.sonarr),
    DatabaseInterface(args.tmdb),
    PlexInterface(*args.plex),
)

tcm.main_loop(args.interval)