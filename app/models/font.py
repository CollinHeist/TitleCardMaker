from pathlib import Path
from re import sub as re_sub, IGNORECASE
from typing import Any, Iterable, Optional, TYPE_CHECKING

from sqlalchemy import JSON, String, func

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.dependencies import get_preferences
from app.schemas.font import TitleCase

if TYPE_CHECKING:
    from app.models.episode import Episode
    from app.models.series import Series
    from app.models.template import Template


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
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    episodes: Mapped[list['Episode']] = relationship(back_populates='font')
    series: Mapped[list['Series']] = relationship(back_populates='font')
    templates: Mapped[list['Template']] = relationship(back_populates='font')

    name: Mapped[str]
    color: Mapped[Optional[str]]
    delete_missing: Mapped[bool] = mapped_column(default=True)
    file_name: Mapped[Optional[str]]
    interline_spacing: Mapped[int] = mapped_column(default=0)
    interword_spacing: Mapped[int] = mapped_column(default=0)
    kerning: Mapped[float] = mapped_column(default=1.0)
    replacements_in: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON),
        default=[],
    )
    replacements_out: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON),
        default=[],
    )
    size: Mapped[float] = mapped_column(default=1.0)
    stroke_width: Mapped[float] = mapped_column(default=1.0)
    title_case: Mapped[Optional[TitleCase]] = mapped_column(String,default=None)
    vertical_shift: Mapped[int] = mapped_column(default=0)
    line_split_modifier: Mapped[int] = mapped_column(default=0)


    def __repr__(self) -> str:
        return f'Font[{self.id}] "{self.name}"'


    @property
    def file(self) -> Optional[Path]:
        """
        Get the name of this Font's file, if indicated.  None if this
        Font has no file, or if the file does not exist.
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
        The sort-friendly name of this Font. This is lowercase with any
        prefix a/an/the removed.
        """

        return regex_replace(r'^(a|an|the)(\s)', '', self.name.lower())

    @sort_name.expression
    def sort_name(cls: 'Font'): # pylint: disable=no-self-argument
        """Class-expression of `sort_name` property."""

        return func.regex_replace(r'^(a|an|the)(\s)', '', func.lower(cls.name))


    @staticmethod
    def apply_replacements(
            text: str,
            in_: Iterable[str],
            out_: Iterable[str],
            *,
            pre: bool,
        ) -> str:
        """
        Apply the given paired lists of character replacements to the
        given text.

        Args:
            text: Input text to apply replacements to.
            in_: List of input strings to sequentially replace.
            out_: List of output strings to replace with.
            pre: Whether this is a pre-replacement. If True, all `post:`
                prefixed replacements are skipped; if False all `pre:`
                replacements are skipped.

        Returns:
            Modified text.
        """

        for repl_in, repl_out in zip(in_, out_):
            # Skip replacements from pre if post; post if pre
            if ((pre and repl_in.startswith('post:'))
                or (not pre and repl_in.startswith('pre:'))):
                continue

            # Skip pre: and post: prefix in replacement
            if repl_in.startswith('pre:'):
                repl_in = repl_in[4:]
            elif repl_in.startswith('post:'):
                repl_in = repl_in[5:]

            text = text.replace(repl_in, repl_out)

        return text


    @property
    def card_properties(self) -> dict[str, Any]:
        """
        Properties to utilize and merge in Title Card creation.
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


    @property
    def export_properties(self) -> dict[str, Any]:
        """
        Properties to export in Blueprints. These properties can be used
        in a NewNamedFont model to recreate this object.
        """

        if self.line_split_modifier == 0:
            modifier = None
        else:
            modifier = self.line_split_modifier

        return {
            'name': self.name,
            'color': self.color,
            'delete_missing': None if self.delete_missing else False,
            'file': self.file_name,
            'interline_spacing': self.interline_spacing or None,
            'interword_spacing': self.interword_spacing or None,
            'kerning': None if self.kerning == 1.0 else self.kerning,
            'line_split_modifier': modifier,
            'replacements_in': self.replacements_in,
            'replacements_out': self.replacements_out,
            'size': None if self.size == 1.0 else self.size,
            'stroke_width': None if self.stroke_width == 1.0 else self.stroke_width,
            'title_case': self.title_case,
            'vertical_shift': self.vertical_shift or None,
        }
