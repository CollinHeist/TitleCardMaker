"""Add Series level title split toggle
Modify Series table:
- Add Series.auto_split_title which defaults to True

Modify Episode table:
- Make Episode.auto_split_title nullable
- Migrate all Episode.auto_split_title values which are True to None

Revision ID: f1692007cf8a
Revises: 3122c0553b1e
Create Date: 2024-03-10 11:41:30.812809
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from modules.Debug import contextualize
from modules.Debug2 import logger 

# Revision identifiers, used by Alembic.
revision = 'f1692007cf8a'
down_revision = '3122c0553b1e'
branch_labels = None
depends_on = None

# Models necessary for data migration
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()

class Episode(Base):
    __tablename__ = 'episode'

    # Columns not being modified
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    auto_split_title = sa.Column(sa.Boolean, nullable=True, default=None)


def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.alter_column('auto_split_title',
            existing_type=sa.BOOLEAN(),
            nullable=True
        )

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'auto_split_title',
            sa.Boolean(),
            nullable=False,
            server_default=str(True),
        ))

    # Perform data migration
    session = Session(bind=op.get_bind())

    # Convert all Episode.auto_split_title = True -> None
    # This is because the Series-level default is now True; so Episodes should
    # default to pass through. False stays as override.
    count = 0
    for episode in session.query(Episode).all():
        if episode.auto_split_title:
            episode.auto_split_title = None
            count += 1
    log.debug(f'Nullified {count} Episode.auto_split_title entries')

    # Commit changes
    session.commit()

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.drop_column('auto_split_title')

    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.alter_column('auto_split_title',
            existing_type=sa.BOOLEAN(),
            nullable=False
        )

    # Perform reverse data migration
    session = Session(bind=op.get_bind())

    # Reverse migration and set all Episode.auto_split_title = None -> True
    count = 0
    for episode in session.query(Episode).all():
        if episode.auto_split_title is None:
            episode.auto_split_title = True
            count += 1
    log.debug(f'Reset {count} Episode.auto_split_title entries')

    # Commit changes
    session.commit()

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
