from pathlib import Path

ANGLE = 78.5 # Degrees
bounds = {
    'small': [10, 30],
    'medium': [150, 300],
    'large': [700, 1000],
}

from modules.cards.StripedTitleCard import StripedTitleCard

StripedTitleCard(
    source_file=Path('./config/s2e11.jpg'),
    card_file=Path('./test.jpg'),
    title_text='Example',
    season_text='Season 1',
    episode_text='Episode 1',
).create()



# from plexapi.server import PlexServer
# from plexapi.library import Library as PlexLibrary
# from requests import get

# server = PlexServer('http://192.168.0.29:32400/', 'pzfzWxW-ygxzJJc-t_Pw')
# library: PlexLibrary = server.library.section('Anime')
# print(library.listFields())
# eps = library.searchEpisodes(
#     filters={
#         'and': [
#             {'label': 'TCM'}, # Does not contain TCM
#             {
#                 'or': [
#                     # {'show.title': '86: Eighty-Six'},
#                     {'show.id': 15606},
#                 ]
#             },
#         ]
#     },
#     limit=10,
# )
# print(eps)

# DATA_FILE = Path('./jellyfin_id.json')


# data = {}
# if DATA_FILE.exists():
#     with DATA_FILE.open('r') as fh:
#         data = load(fh)

# url = 'http://192.168.0.29:8096'
# api_key = '7bde0685217c417e870532da7833d526'
# response = get(
#     f'{url}/Items',
#     params= {
#         'api_key': api_key,
#         'recursive': True,
#         'includeItemTypes': 'Series',
#         # 'searchTerm': 'Stone',
#         'fields': 'ProviderIds,Overview',
#         'enableImages': False,
#     },
#     timeout=10,
# ).json()
# # print(dumps(response['Items'], indent=2))

# for series in response['Items']:
#     if series['Name'] in data:
#         data[series['Name']][str(datetime.now())] = series['Id']
#     else:
#         data[series['Name']] = {str(datetime.now()): series['Id']}

# DATA_FILE.unlink(missing_ok=True)
# with DATA_FILE.open('w') as fh:
#     dump(data, fh, indent=2)
