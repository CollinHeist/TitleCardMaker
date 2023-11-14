"""
Use ORM mappings where applicable.
Finalize nullability of each table's columns.

Revision ID: 5318f59eadbf
Revises: a61f373185d4
Create Date: 2023-11-14 12:38:23.264714

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from modules.Debug import contextualize

from modules.Debug import contextualize

# revision identifiers, used by Alembic.
revision = '5318f59eadbf'
down_revision = 'a61f373185d4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    log = contextualize()
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.alter_column('series_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('episode_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('filesize',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('model_json',
            existing_type=sqlite.JSON(),
            server_default=None,
            existing_nullable=False)

    with op.batch_alter_table('connection', schema=None) as batch_op:
        batch_op.alter_column('filesize_limit',
            existing_type=sa.VARCHAR(),
            nullable=False)

    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.alter_column('series_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('watched_statuses',
            existing_type=sqlite.JSON(),
            server_default=None,
            existing_nullable=False)
        batch_op.alter_column('emby_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('jellyfin_id',
            existing_type=sa.VARCHAR(),
            nullable=False)
        batch_op.alter_column('translations',
            existing_type=sqlite.JSON(),
            nullable=False)
        batch_op.alter_column('image_source_attempts',
            existing_type=sqlite.JSON(),
            nullable=False)

    with op.batch_alter_table('episode_templates', schema=None) as batch_op:
        batch_op.alter_column('template_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('episode_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('order',
            existing_type=sa.INTEGER(),
            nullable=False)

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.alter_column('delete_missing',
            existing_type=sa.BOOLEAN(),
            nullable=False)
        batch_op.alter_column('stroke_width',
            existing_type=sa.FLOAT(),
            nullable=False)

    with op.batch_alter_table('loaded', schema=None) as batch_op:
        batch_op.alter_column('card_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('episode_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('interface_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('series_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('filesize',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('library_name',
            existing_type=sa.VARCHAR(),
            nullable=False)

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.alter_column('poster_file',
            existing_type=sa.VARCHAR(),
            nullable=False)
        batch_op.alter_column('poster_url',
            existing_type=sa.VARCHAR(),
            nullable=False)
        batch_op.alter_column('libraries',
            existing_type=sqlite.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False)

    with op.batch_alter_table('series_templates', schema=None) as batch_op:
        batch_op.alter_column('template_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('series_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('order',
            existing_type=sa.INTEGER(),
            nullable=False)

    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.alter_column('interface_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('downloaded_only',
            existing_type=sa.BOOLEAN(),
            nullable=False)
        batch_op.alter_column('monitored_only',
            existing_type=sa.BOOLEAN(),
            nullable=False)

    with op.batch_alter_table('sync_templates', schema=None) as batch_op:
        batch_op.alter_column('template_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('sync_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('order',
            existing_type=sa.INTEGER(),
            nullable=False)

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('username',
            existing_type=sa.VARCHAR(),
            nullable=False)
        batch_op.alter_column('hashed_password',
            existing_type=sa.VARCHAR(),
            nullable=False)

    # ### end Alembic commands ###
    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize()
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('hashed_password',
            existing_type=sa.VARCHAR(),
            nullable=True)
        batch_op.alter_column('username',
            existing_type=sa.VARCHAR(),
            nullable=True)

    with op.batch_alter_table('sync_templates', schema=None) as batch_op:
        batch_op.alter_column('order',
            existing_type=sa.INTEGER(),
            nullable=True)
        batch_op.alter_column('sync_id',
            existing_type=sa.INTEGER(),
            nullable=True)
        batch_op.alter_column('template_id',
            existing_type=sa.INTEGER(),
            nullable=True)

    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.alter_column('monitored_only',
            existing_type=sa.BOOLEAN(),
            nullable=True)
        batch_op.alter_column('downloaded_only',
            existing_type=sa.BOOLEAN(),
            nullable=True)
        batch_op.alter_column('interface_id',
            existing_type=sa.INTEGER(),
            nullable=True)

    with op.batch_alter_table('series_templates', schema=None) as batch_op:
        batch_op.alter_column('order',
            existing_type=sa.INTEGER(),
            nullable=True)
        batch_op.alter_column('series_id',
            existing_type=sa.INTEGER(),
            nullable=True)
        batch_op.alter_column('template_id',
            existing_type=sa.INTEGER(),
            nullable=True)

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.alter_column('libraries',
            existing_type=sqlite.JSON(),
            server_default=sa.text("'[]'"),
            nullable=True)
        batch_op.alter_column('poster_url',
            existing_type=sa.VARCHAR(),
            nullable=True)
        batch_op.alter_column('poster_file',
            existing_type=sa.VARCHAR(),
            nullable=True)

    with op.batch_alter_table('loaded', schema=None) as batch_op:
        batch_op.alter_column('library_name',
            existing_type=sa.VARCHAR(),
            nullable=True)
        batch_op.alter_column('filesize',
            existing_type=sa.INTEGER(),
            nullable=True)
        batch_op.alter_column('series_id',
            existing_type=sa.INTEGER(),
            nullable=True)
        batch_op.alter_column('interface_id',
            existing_type=sa.INTEGER(),
            nullable=True)
        batch_op.alter_column('episode_id',
            existing_type=sa.INTEGER(),
            nullable=True)
        batch_op.alter_column('card_id',
            existing_type=sa.INTEGER(),
            nullable=True)

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.alter_column('stroke_width',
            existing_type=sa.FLOAT(),
            nullable=True)
        batch_op.alter_column('delete_missing',
            existing_type=sa.BOOLEAN(),
            nullable=True)

    with op.batch_alter_table('episode_templates', schema=None) as batch_op:
        batch_op.alter_column('order',
            existing_type=sa.INTEGER(),
            nullable=True)
        batch_op.alter_column('episode_id',
            existing_type=sa.INTEGER(),
            nullable=True)
        batch_op.alter_column('template_id',
            existing_type=sa.INTEGER(),
            nullable=True)

    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.alter_column('image_source_attempts',
            existing_type=sqlite.JSON(),
            nullable=True)
        batch_op.alter_column('translations',
            existing_type=sqlite.JSON(),
            nullable=True)
        batch_op.alter_column('jellyfin_id',
            existing_type=sa.VARCHAR(),
            nullable=True)
        batch_op.alter_column('emby_id',
            existing_type=sa.INTEGER(),
            nullable=True)
        batch_op.alter_column('watched_statuses',
            existing_type=sqlite.JSON(),
            server_default=sa.text("'{}'"),
            existing_nullable=False)
        batch_op.alter_column('series_id',
            existing_type=sa.INTEGER(),
            nullable=True)

    with op.batch_alter_table('connection', schema=None) as batch_op:
        batch_op.alter_column('filesize_limit',
            existing_type=sa.VARCHAR(),
            nullable=True)

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.alter_column('model_json',
            existing_type=sqlite.JSON(),
            server_default=sa.text("'{}'"),
            existing_nullable=False)
        batch_op.alter_column('filesize',
            existing_type=sa.INTEGER(),
            nullable=True)
        batch_op.alter_column('episode_id',
            existing_type=sa.INTEGER(),
            nullable=True)
        batch_op.alter_column('series_id',
            existing_type=sa.INTEGER(),
            nullable=True)

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
