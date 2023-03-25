from sqlalchemy import Boolean, Column, Integer, String, ForeignKey

from app.database.session import Base

def default_source(context) -> str:
    params = context.get_current_parameters()
    return f's{params["season_number"]}e{params["episode_number"]}.jpg'

def default_card(context) -> str:
    params = context.get_current_parameters()
    return f'card-s{params["season_number"]}e{params["episode_number"]}.jpg'

class Episode(Base):
    __tablename__ = 'episode'

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey('series.id'))

    season_number = Column(Integer)
    episode_number = Column(Integer)
    absolute_number = Column(Integer, default=None)

    title = Column(String)
    match_title = Column(Boolean, default=False)

    source_path = Column(String, default=default_source)
    card_path = Column(String, default=default_card)

    emby_id = Column(Integer, default=None)
    imdb_id = Column(String, default=None)
    jellyfin_id = Column(String, default=None)
    # sonarr_id = Column(String, default=None)
    tmdb_id = Column(Integer, default=None)
    tvdb_id = Column(Integer, default=None)
    tvrage_id = Column(Integer, default=None)