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
    def log_str(self) -> str:
        return f'Font[{self.id}] "{self.name}"'

    @hybrid_property
    def card_properties(self) -> dict[str, Any]:
        return {
            f'font_{key}': value
            for key, value in self.__dict__.items()
            if not key.startswith('_')
        }
    
    @hybrid_property
    def export_properties(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'color': self.color,
            'title_case': self.title_case,
            'size': None if self.size == 1.0 else self.size,
            'kerning': None if self.kerning == 1.0 else self.kerning,
            'stroke_width': None if self.stroke_width == 1.0 else self.stroke_width,
            'interline_spacing': None if self.interline_spacing == 0 else self.interline_spacing,
            'vertical_shift': None if self.vertical_shift == 0 else self.vertical_shift,
            'delete_missing': self.delete_missing,
            'replacements_in': list(self.replacements.keys()),
            'replacements_out': list(self.replacements.values()),
        }