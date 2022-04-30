# SETUP = """
# from modules.Episode import Episode
# from modules.EpisodeInfo import EpisodeInfo
# from pathlib import Path

# ei = EpisodeInfo('Title', 1, 1, 1)
# source = Path('source')
# destination = Path('destination')
# """

# TIMED_CODE = """
# e = Episode(ei, 'card_type', source, destination, extra_1='abc', extra_2='def')
# """

SETUP = """
from modules.EpisodeInfo import EpisodeInfo
"""

TIMED_CODE = """
ei = EpisodeInfo('title', 1, 1, 1)
"""

from timeit import repeat
times = repeat(setup=SETUP, stmt=TIMED_CODE, repeat=10, number=100000)

print(f'{times=}\n\naverage={sum(times)/len(times)}')