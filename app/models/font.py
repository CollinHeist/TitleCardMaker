from sqlalchemy import Boolean, Column, Integer, Float, String, ForeignKey

from json import dumps, loads
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy import PickleType

from app.database.session import Base

class Font(Base):
    __tablename__ = 'font'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    file_path = Column(String, default=None)
    color = Column(String, default=None)
    title_case = Column(String, default=None)
    size = Column(Float, default=1.0)
    kerning = Column(Float, default=1.0)
    stroke_width = Column(Float, default=1.0)
    interline_spacing = Column(Integer, default=0)
    vertical_shift = Column(Integer, default=0)
    validate_characters = Column(Boolean, default=None)
    delete_missing = Column(Boolean, default=True)
    replacements = Column(MutableDict.as_mutable(PickleType), default=None)