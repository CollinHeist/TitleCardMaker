# pylint: disable=missing-class-docstring,missing-function-docstring
# pyright: reportInvalidTypeForm=false
from pydantic import constr

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
