# pylint: disable=missing-class-docstring,missing-function-docstring
from pydantic import constr # pylint: disable=no-name-in-module

from app.schemas.base import Base

"""
Update classes
"""
class UpdateUser(Base):
    username: constr(min_length=1)
    password: constr(min_length=1)

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