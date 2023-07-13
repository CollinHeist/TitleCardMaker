from pathlib import Path
from typing import Any, Optional

from sqlalchemy import Boolean, Column, Integer, Float, String, JSON

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.database.session import Base

class Font(Base):
    """
    SQL Table that defines a Named Font. This contains Font
    customizations, as well as relational objects to linked Episodes,
    Series, and Templates.
    """

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
    def file_name(self) -> Optional[str]:
        """
        Get the name of this Font's file, if indicated.

        Returns:
            Name of the file, None if this Font has no file, or that
            file does not exist.
        """

        if self.file is None or not (file := Path(self.file)).exists():
            return None

        return file.name


    @hybrid_property
    def log_str(self) -> str:
        """
        Loggable string that defines this object (i.e. `__repr__`).
        """

        return f'Font[{self.id}] "{self.name}"'


    @hybrid_property
    def card_properties(self) -> dict[str, Any]:
        """
        Properties to utilize and merge in Title Card creation.

        Returns:
            Dictionary of properties.
        """

        return {
            f'font_{key}': value
            for key, value in self.__dict__.items()
            if not key.startswith('_')
        }


    @hybrid_property
    def export_properties(self) -> dict[str, Any]:
        """
        Properties to export in Blueprints.

        Returns:
            Dictionary of the properties that can be used in a
            NewNamedFont model to recreate this object.
        """

        return {
            'name': self.name,
            'color': self.color,
            'delete_missing': self.delete_missing,
            'file': self.file_name,
            'interline_spacing': self.interline_spacing or None,
            'kerning': None if self.kerning == 1.0 else self.kerning,
            'replacements_in': list(self.replacements.keys()),
            'replacements_out': list(self.replacements.values()),
            'size': None if self.size == 1.0 else self.size,
            'stroke_width': None if self.stroke_width == 1.0 else self.stroke_width,
            'title_case': self.title_case,
            'vertical_shift': self.vertical_shift or None,
        }
