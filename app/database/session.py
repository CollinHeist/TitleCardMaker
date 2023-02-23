from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    # TODO https://github.com/ChristopherGS/ultimate-fastapi-tutorial/blob/main/part-08-structure-and-versioning/app/db/session.py
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)