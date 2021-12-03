from argparse import ArgumentParser, SUPPRESS
from pathlib import Path

from DatabaseInterface import DatabaseInterface
from TitleCardMaker import TitleCardMaker

parser = ArgumentParser(description='Setup the TitleCardMaker')

# Argument group for 'manual' title card creation
title_card_group = parser.add_argument_group('Title Cards', 'Manual title card creation')
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
title_card_group.add_argument('--font-size', type=str, default='100%',
                              metavar='SCALE%',
                              help='Specify a custom font scale, as percentage, to use for this card')
title_card_group.add_argument('--color', type=str, default=TitleCardMaker.TITLE_DEFAULT_COLOR,
                              metavar='#HEX',
                              help='Specify a custom font color to use for this card')

# Argument group for fixes relating to TheMovieDatabase
tmdb_group = parser.add_argument_group('TheMovieDatabase', 'Fixes for how the maker interacts with TheMovieDatabase')
tmdb_group.add_argument('--tmdb-force-id', type=str, nargs=3, default=SUPPRESS, action='append',
                        metavar=('TITLE', 'YEAR', 'TMDB_ID'),
                        help='Manually specify an ID for a show (to fix mismatches)')

# Check given arguments
args = parser.parse_args()

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
        title_color=args.color,
        hide_season=not bool(args.season),
    ).create()

# Execute TMDB related options
if hasattr(args, 'tmdb_force_id'):
    for arg_set in args.tmdb_force_id:
        DatabaseInterface.manually_specify_id(*arg_set)
