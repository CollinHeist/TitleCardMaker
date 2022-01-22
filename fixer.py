from argparse import ArgumentParser, ArgumentTypeError, SUPPRESS
from pathlib import Path

from modules.DatabaseInterface import DatabaseInterface
from modules.GenreMaker import GenreMaker
import modules.preferences as preferences
from modules.SonarrInterface import SonarrInterface
from modules.TitleCardMaker import TitleCardMaker

parser = ArgumentParser(description='Manual fixes for the TitleCardMaker')

# Argument group for 'manual' title card creation
title_card_group = parser.add_argument_group('Title Cards', 'Manual title card creation')
title_card_group.add_argument('--magick-docker-id', type=str, default=None,
                               metavar='ID',
                               help='Docker ID of a container running Imagemagick - if unspecified, the host ImageMagick is used')
title_card_group.add_argument('--title-card', type=str, nargs=3, default=SUPPRESS, 
                              metavar=('EPISODE', 'SOURCE', 'DESTINATION'),
                              help='Manually create a title card using these parameters')
title_card_group.add_argument('--season', type=str, default=None,
                              metavar='SEASON_TEXT',
                              help='Specify the season text to use for this card')
title_card_group.add_argument('--title', type=str, nargs='+', default=(' ', ' '),
                              metavar=('LINE1', 'LINE2'),
                              help='Specify the title text to use for this card')
title_card_group.add_argument('--font', type=str, default=TitleCardMaker.TITLE_DEFAULT_FONT.resolve(),
                              metavar='FONT_FILE',
                              help='Specify a custom font to use for this card')
title_card_group.add_argument('--font-size', '--size', type=str, default='100%',
                              metavar='SCALE%',
                              help='Specify a custom font scale, as percentage, to use for this card')
title_card_group.add_argument('--font-color', '--color', type=str, default=TitleCardMaker.TITLE_DEFAULT_COLOR,
                              metavar='#HEX',
                              help='Specify a custom font color to use for this card')

# Argument group for genre maker
genre_group = parser.add_argument_group('Genre Cards', 'Manual genre card creation')
genre_group.add_argument('--genre-card', type=str, nargs=3, default=SUPPRESS,
                         metavar=('SOURCE', 'GENRE', 'DESTINATION'),
                         help='Create a genre card with the given text')
genre_group.add_argument('--genre-card-batch', type=Path, default=SUPPRESS,
                         metavar=('SOURCE_DIRECTORY'),
                         help='Create all genre cards for images in the given directory based on their file names')

# Argument group for fixes relating to Sonarr
sonarr_group = parser.add_argument_group('Sonarr', 'Fixes for how the maker interacts with Sonarr')
sonarr_group.add_argument('--sonarr-list-ids', type=str, nargs=2, default=SUPPRESS,
                          metavar=('URL', 'API_KEY'),
                          help='List all internal IDs used by Sonarr (to then manually specify)')
sonarr_group.add_argument('--sonarr-force-id', type=str, nargs=3, default=SUPPRESS, action='append',
                          metavar=('TITLE', 'YEAR', 'SONARR_ID'),
                          help='Manually specify an ID for a show')

# Argument group for fixes relating to TheMovieDatabase
tmdb_group = parser.add_argument_group('TheMovieDatabase', 'Fixes for how the Maker interacts with TheMovieDatabase')
tmdb_group.add_argument('--tmdb-force-id', type=str, nargs=3, default=SUPPRESS, action='append',
                        metavar=('TITLE', 'YEAR', 'TMDB_ID'),
                        help='Manually specify an ID for a show')
tmdb_group.add_argument('--tmdb-download-images', nargs=6, default=SUPPRESS, action='append',
                        metavar=('API_KEY', 'TITLE', 'YEAR', 'SEASON', 'EPISODES', 'DIRECTORY'),
                        help='Download the best title card source image for the given episode')
tmdb_group.add_argument('--delete-blacklist', action='store_true',
                        help='Whether to delete the existing TMDb blacklist (executed first)')

# Check given arguments
args = parser.parse_args()

if args.magick_docker_id:
    preferences.update_imagemagick_docker_id(args.magick_docker_id)

# Execute title card related options
if hasattr(args, 'title_card'):
    TitleCardMaker(
        episode_text=args.title_card[0],
        source=Path(args.title_card[1]), 
        output_file=Path(args.title_card[2]),
        season_text=('' if not args.season else args.season),
        title_top_line=args.title[0] if len(args.title) == 2 else '',
        title_bottom_line=args.title[1 if len(args.title) == 2 else 0],
        font=args.font,
        font_size=float(args.font_size[:-1])/100.0,
        title_color=args.font_color,
        hide_season=not bool(args.season),
    ).create()

# Execute genre card related options
if hasattr(args, 'genre_card'):
    GenreMaker(
        source=Path(args.genre_card[0]),
        genre=args.genre_card[1],
        output=Path(args.genre_card[2]),
    ).create()

if hasattr(args, 'genre_card_batch'):
    for file in args.genre_card_batch.glob('*'):
        if file.suffix.lower() in ('.jpg', '.jpeg', '.png', '.tiff', '.gif'):
            GenreMaker(
                source=file,
                genre=file.stem.upper(),
                output=Path(file.parent / f'{file.stem}-GenreCard{file.suffix}'),
            ).create()

# Execute Sonarr related options
if hasattr(args, 'sonarr_list_ids'):
    SonarrInterface(args.sonarr_list_ids[0], args.sonarr_list_ids[1]).list_all_series_id()

if hasattr(args, 'sonarr_force_id'):
    for arg_set in args.sonarr_force_id:
        SonarrInterface.manually_specify_id(*arg_set)

# Execute TMDB related options
if hasattr(args, 'delete_blacklist'):
    if args.delete_blacklist:
        DatabaseInterface.delete_blacklist()

if hasattr(args, 'tmdb_force_id'):
    for arg_set in args.tmdb_force_id:
        DatabaseInterface.manually_specify_id(
            title=arg_set[0], year=arg_set[1], id_=arg_set[2]
        )

if hasattr(args, 'tmdb_download_images'):
    for arg_set in args.tmdb_download_images:
        DatabaseInterface.manually_download_season(
            api_key=arg_set[0],
            title=arg_set[1],
            year=int(arg_set[2]),
            season=int(arg_set[3]),
            episode_count=int(arg_set[4]),
            directory=Path(arg_set[5]),
        )

