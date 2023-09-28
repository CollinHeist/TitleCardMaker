from pathlib import Path
from re import sub as re_sub, IGNORECASE
from typing import Any, Optional

from sqlalchemy import Boolean, Column, Integer, Float, String, JSON, func

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.dependencies import get_preferences


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

    name = Column(String, nullable=False)
    color = Column(String, default=None)
    delete_missing = Column(Boolean, default=True)
    file_name = Column(String, default=None)
    interline_spacing = Column(Integer, default=0, nullable=False)
    interword_spacing = Column(Integer, default=0, nullable=False)
    kerning = Column(Float, default=1.0, nullable=False)
    replacements = Column(JSON, default=None)
    size = Column(Float, default=1.0, nullable=False)
    stroke_width = Column(Float, default=1.0)
    title_case = Column(String, default=None)
    vertical_shift = Column(Integer, default=0, nullable=False)


    @hybrid_property
    def file(self) -> Optional[Path]:
        """
        Get the name of this Font's file, if indicated.

        Returns:
            Full path to the Font file, None if this Font has no file,
            or if the file does not exist.
        """

        if self.file_name is None:
            return None

        font_directory = get_preferences().asset_directory / 'fonts'
        if not (file := font_directory / str(self.id)/ self.file_name).exists():
            return None

        return file


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

        if (file := self.file) is None:
            return {
                f'font_{key}': value
                for key, value in self.__dict__.items()
                if not key.startswith('_')
            }

        return {
            f'font_{key}': value
            for key, value in self.__dict__.items()
            if not key.startswith('_')
        } | {'font_file': str(file)}


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
            'interword_spacing': self.interword_spacing or None,
            'kerning': None if self.kerning == 1.0 else self.kerning,
            'replacements_in': list(self.replacements.keys()),
            'replacements_out': list(self.replacements.values()),
            'size': None if self.size == 1.0 else self.size,
            'stroke_width': None if self.stroke_width == 1.0 else self.stroke_width,
            'title_case': self.title_case,
            'vertical_shift': self.vertical_shift or None,
        }
