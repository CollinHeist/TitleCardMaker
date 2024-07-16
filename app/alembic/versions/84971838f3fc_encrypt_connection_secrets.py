"""Encrypt Connection server URLs and API keys

Revision ID: 84971838f3fc
Revises: 0a5f4764cd10
Create Date: 2024-07-14 22:31:47.681441
"""

from alembic import op
import sqlalchemy as sa

from app.internal.auth import decrypt, encrypt
from modules.Debug import contextualize
from modules.Debug2 import logger 

# Revision identifiers, used by Alembic.
revision = '84971838f3fc'
down_revision = '0a5f4764cd10'
branch_labels = None
depends_on = None

# Models necessary for data migration
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()

class Connection(Base):
    __tablename__ = 'connection'

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    api_key = sa.Column(sa.String, nullable=False)
    url = sa.Column(sa.String, nullable=True)


def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    # Perform data migration
    session = Session(bind=op.get_bind())

    # Encrypt all URLs and API keys in the database
    for connection in session.query(Connection).all():
        if connection.url:
            connection.url = encrypt(connection.url)
            log.debug(f'Encrypted URL for Connection[{connection.id}]')
        if connection.api_key:
            connection.api_key = encrypt(connection.api_key)
            log.debug(f'Encrypted API key for Connection[{connection.id}]')

    # Commit changes
    session.commit()

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    # Perform data migration
    session = Session(bind=op.get_bind())

    # Decrypt all URLs and API keys in the database
    for connection in session.query(Connection).all():
        if connection.url:
            connection.url = decrypt(connection.url)
            log.debug(f'Decrypted URL for Connection[{connection.id}]')
        if connection.api_key:
            connection.api_key = decrypt(connection.api_key)
            log.debug(f'Decrypted API key for Connection[{connection.id}]')

    # Commit changes
    session.commit()

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
