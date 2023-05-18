from typing import Any

from sqlalchemy import Boolean, Column, Integer, Float, String, JSON

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.database.session import Base

class Font(Base):
    __tablename__ = 'font'

    # Referencial arguments
    id = Column(Integer, primary_key=True, index=True)
    episodes = relationship('Episode', back_populates='font')
    series = relationship('Series', back_populates='font')
    templates = relationship('Template', back_populates='font')

    name = Column(String)
    file = Column(String, default=None)
    color = Column(String, default=None)
    title_case = Column(String, default=None)
    size = Column(Float, default=1.0)
    kerning = Column(Float, default=1.0)
    stroke_width = Column(Float, default=1.0)
    interline_spacing = Column(Integer, default=0)
    vertical_shift = Column(Integer, default=0)
    validate_characters = Column(Boolean, default=None)
    delete_missing = Column(Boolean, default=True)
    replacements = Column(JSON, default=None)

    @hybrid_property
    def card_properties(self) -> dict[str, Any]:
        return {
            f'font_{key}': value
            for key, value in self.__dict__.items()
            if not key.startswith('_')
        }