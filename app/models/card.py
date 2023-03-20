from sqlalchemy import Boolean, Column, Integer, String, ForeignKey

from app.database.session import Base

class Card(Base):
    __tablename__ = 'card'

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey('series.id'))
    episode_id = Column(Integer, ForeignKey('episode.id'))
    font_id = Column(Integer, ForeignKey('font.id'))

    source = Column(String)
    output = Column(String)
    card_type = Column(String)

    blur = Column(Boolean)
    grayscale = Column(Boolean)

    title = Column(String)
    season_text = Column(String)
    episode_text = Column(String)
    hide_season = Column(Boolean)

    extras = Column(String, nullable=True)