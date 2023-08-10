from pathlib import Path
from re import sub as re_sub, IGNORECASE
from typing import Any, Optional

from sqlalchemy import Boolean, Column, Integer, Float, String, JSON, func

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.database.session import Base


def regex_replace(pattern, replacement, string):
    """Perform a Regex replacement with the given arguments"""

    return re_sub(pattern, replacement, string, IGNORECASE)


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
    color = Column(String, default=None)
    delete_missing = Column(Boolean, default=True)
    file = Column(String, default=None)
    kerning = Column(Float, default=1.0)
    interline_spacing = Column(Integer, default=0)
    replacements = Column(JSON, default=None)
    size = Column(Float, default=1.0)
    stroke_width = Column(Float, default=1.0)
    title_case = Column(String, default=None)
    validate_characters = Column(Boolean, default=None)
    vertical_shift = Column(Integer, default=0)


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
    def sort_name(self) -> str:
        """
        The sort-friendly name of this Font.

        Returns:
            Sortable name. This is lowercase with any prefix a/an/the
            removed.
        """

        return regex_replace(r'^(a|an|the)(\s)', '', self.name.lower())

    @sort_name.expression
    def sort_name(cls: 'Font'): # pylint: disable=no-self-argument
        """Class-expression of `sort_name` property."""

        return func.regex_replace(r'^(a|an|the)(\s)', '', func.lower(cls.name))


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
