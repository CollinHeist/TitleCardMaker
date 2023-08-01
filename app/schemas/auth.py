# pylint: disable=missing-class-docstring,missing-function-docstring
from pydantic import constr

from app.schemas.base import Base


"""
Return classes
"""
class Token(Base):
    access_token: str
    token_type: str

class NewUser(Base):
    username: constr(min_length=1)
    password: constr(min_length=1)

class User(Base):
    username: str
    hashed_password: str
