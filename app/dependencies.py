from typing import Generator

from app.database.session import SessionLocal

def get_database() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()