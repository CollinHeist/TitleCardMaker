from sqlalchemy import Column, Integer, String

from app.database.session import Base


class User(Base):
    """
    SQL Table that defines a User.
    """

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    hashed_password = Column(String)
