from argparse import ArgumentParser, ArgumentTypeError, SUPPRESS
from pathlib import Path
from dataclasses import dataclass

try:
    from modules.Debug import log
    from modules.GenreMaker import GenreMaker
    from modules.PreferenceParser import PreferenceParser
    from modules.preferences import set_preference_parser
    from modules.RemoteCardType import RemoteCardType
    from modules.ShowSummary import ShowSummary
    from modules.TitleCard import TitleCard
except ImportError:
    print(f'Required Python packages are missing - execute "pipenv install"')
    exit(1)

parser = ArgumentParser(description='Manually make cards')
parser.add_argument('-p', '--preference-file', type=Path, 
                    default='preferences.yml', metavar='PREFERENCE_FILE',
                    help='Preference YAML file for parsing '
                         'ImageMagick/Sonarr/TMDb options')

# Argument group for 'manual' title card creation
title_card_group = parser.add_argument_group('Title Cards',
                                             'Manual TitleCardMaker interaction')
title_card_group.add_argument(
    '--title-card',
    type=Path,
    nargs=2,
    default=SUPPRESS,
    metavar=('SOURCE', 'DESTINATION'),
    help='Create a title card with the given source image, written to the given'
         ' destination')
title_card_group.add_argument(
    '--card-type',
    type=str,
    default='standard',
    metavar='TYPE',
    help='Create a title card of a specific type')
title_card_group.add_argument(
    '--blur',
    action='store_true',
    help='Blur the source image for this card')
title_card_group.add_argument(
    '--episode',
    type=str,
    default='EPISODE',
    metavar='EPISODE_TEXT',
    help='The episode text for this card')
title_card_group.add_argument(
    '--season',
    type=str,
    default=None,
    metavar='SEASON_TEXT',
    help='The season text for this card')
title_card_group.add_argument(
    '--title',
    type=str,
    nargs='+',
    default='',
    metavar=('TITLE_LINE'),
    help="The title text for this card")
title_card_group.add_argument(
    '--font', '--font-file',
    type=Path,
    default='__default',
    metavar='FONT_FILE',
    help="A custom font file for this card")
title_card_group.add_argument(
    '--font-size', '--size',
    type=str,
    default='100%',
    metavar='SCALE%',
    help='A font scale (as percentage) for this card')
title_card_group.add_argument(
    '--font-color', '--color',
    type=str, 
    default='__default',
    metavar='#HEX',
    help='A custom font color for this card')
title_card_group.add_argument(
    '--vertical-shift', '--shift',
    type=float,
    default=0.0,
    metavar='PIXELS',
    help='How many pixels to vertically shift the title text')
title_card_group.add_argument(
    '--interline-spacing', '--spacing',
    type=float,
    default=0.0,
    metavar='PIXELS',
    help='How many pixels to increase the interline spacing of the title text')
title_card_group.add_argument(
    '--kerning',
    type=str,
    default='100%',
    metavar='SCALE%',
    help='Specify the font kerning scale (as percentage)')
title_card_group.add_argument(
    '--stroke-width', '--stroke',
    type=str,
    default='100%',
    metavar='SCALE%',
    help='Specify the font black stroke scale (as percentage)')
    
# Argument group for genre cards
genre_group = parser.add_argument_group(
    'Genre Cards',
    'Manual genre card creation')
genre_group.add_argument(
    '--genre-card',
    type=str,
    nargs=3,
    default=SUPPRESS,
    metavar=('SOURCE', 'GENRE', 'DESTINATION'),
    help='Create a genre card with the given text')
genre_group.add_argument(
    '--borderless',
    action='store_true',
    help='Make the specified Genre Card transparent')
genre_group.add_argument(
    '--genre-card-batch',
    type=Path,
    default=SUPPRESS,
    metavar=('SOURCE_DIRECTORY'),
    help='Create all genre cards for images in the given directory based on '
         'their file names')
         
# Argument group for show summaries
show_summary_group = parser.add_argument_group(
    'Show Summaries',
    'Manual ShowSummary creation')
show_summary_group.add_argument(
    '--show-summary',
    type=Path,
    nargs=2,
    default=SUPPRESS,
    metavar=('IMAGE_DIRECTORY', 'LOGO'),
    help='Create a ShowSummary for the given directory')
show_summary_group.add_argument(
    '--background-color',
    type=str,
    default=ShowSummary.BACKGROUND_COLOR,
    metavar='COLOR',
    help='Specify background color for the created ShowSummary')
         
# Parse given arguments
args, unknown = parser.parse_known_args()

# Create dictionary of unknown arguments
arbitrary_data = {}
if len(unknown) % 2 == 0 and len(unknown) > 1:
    arbitrary_data = {key: val for key, val in zip(unknown[::2], unknown[1::2])}

# Parse preference file for options that might need it
pp = PreferenceParser(args.preference_file)
if not pp.valid:
    exit(1)
set_preference_parser(pp)

# Execute title card related options
if hasattr(args, 'title_card'):
    # Attempt to get local card type, if not, try RemoteCardType
    if args.card_type in TitleCard.CARD_TYPES.keys():
        CardClass = TitleCard.CARD_TYPES[args.card_type]
    elif (remote_card := RemoteCardType(args.card_type)).valid:
        CardClass = remote_card.card_class
    else:
        log.error(f'Cannot identify card type "{args.card_type}" as either '
                  f'local or remote card type')
        exit(1)

    # Override unspecified defaults with their class specific defaults
    if args.font == Path('__default'):
        args.font = Path(str(CardClass.TITLE_FONT))
    if args.font_color == '__default':
        args.font_color = CardClass.TITLE_COLOR

    # Create the given card
    CardClass(
        episode_text=args.episode,
        source=Path(args.title_card[0]), 
        output_file=Path(args.title_card[1]),
        season_text=('' if not args.season else args.season),
        title='\n'.join(args.title),
        font=args.font.resolve(),
        font_size=float(args.font_size[:-1])/100.0,
        title_color=args.font_color,
        hide_season=(not bool(args.season)),
        blur=args.blur,
        vertical_shift=args.vertical_shift,
        interline_spacing=args.interline_spacing,
        kerning=float(args.kerning[:-1])/100.0,
        stroke_width=float(args.stroke_width[:-1])/100.0,
        **arbitrary_data,
    ).create()

# Execute genre card related options
if hasattr(args, 'genre_card'):
    GenreMaker(
        source=Path(args.genre_card[0]),
        genre=args.genre_card[1],
        output=Path(args.genre_card[2]),
        font_size=float(args.font_size[:-1])/100.0,
        borderless=args.borderless,
    ).create()

if hasattr(args, 'genre_card_batch'):
    for file in args.genre_card_batch.glob('*'):
        if file.suffix.lower() in GenreMaker.VALID_IMAGE_EXTENSIONS:
            GenreMaker(
                source=file,
                genre=file.stem.upper(),
                output=Path(file.parent /f'{file.stem}-GenreCard{file.suffix}'),
                font_size=float(args.font_size[:-1])/100.0,
            ).create()
            
if hasattr(args, 'show_summary'):
    # Temporary classes
    @dataclass
    class Episode:
        destination: Path

    @dataclass
    class Show:
        logo: Path
        media_directory: Path
        episodes: dict

    # Get all images in folder
    all_images = args.show_summary[0].glob('**/*.jpg')
    episode = 1
    episodes = {f'1-{(episode := episode+1)}': Episode(f) for f in all_images}
    show = Show(args.show_summary[1], args.show_summary[0], episodes)

    # Create ShowSummary
    ShowSummary(show, args.background_color).create()