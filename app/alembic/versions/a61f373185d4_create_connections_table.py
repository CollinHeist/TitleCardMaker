"""Create Connections Table
Create new Connections SQL table / Model
- Turn existing connection details from global Preferences into Connection
  objects which are assigned during SQL migration.
Modify Loaded table:
- Add new interface_id column tied to newly created Connection(s)
- Remove media_server column
Modify Series table:
- Turn separate emby/jellyfin/plex _library_name columns into single libraries
  column that is a JSON list object like
  [{'media_server': (Emby/Jellyfin/Plex), 'interface_id': (int), 'name': (str)}]
- Perform data migration of existing Series libraries into the above objects
- Remove emby_library_name, jellyfin_library_name, and plex_library_name
  columns
Modify Sync table:
- Add new interface_id and connection columns / relationships as a Sync now must
  be tied to an existing Connection.
Modify Template table:
- Turn episode_data_source column into data_source column

Revision ID: a61f373185d4
Revises: 4d7cb48238be
Create Date: 2023-09-28 12:56:59.752356
"""
# pylint: disable
from alembic import op
import sqlalchemy as sa
from modules.Debug import contextualize

# revision identifiers, used by Alembic.
revision = 'a61f373185d4'
down_revision = '25490125daaf'
branch_labels = None
depends_on = None

# Models necessary for data migration
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Session
from app.database.session import PreferencesLocal

Base = declarative_base()

class Connection(Base):
    __tablename__ = 'connection'

    id = sa.Column(sa.Integer, primary_key=True, index=True)

    interface_type = sa.Column(sa.String, nullable=False)
    enabled = sa.Column(sa.Boolean, default=False, nullable=False)
    name = sa.Column(sa.String, nullable=False)
    api_key = sa.Column(sa.String, nullable=False)

    url = sa.Column(sa.String, default=None, nullable=True)
    use_ssl = sa.Column(sa.Boolean, default=True, nullable=False)

    username = sa.Column(sa.String, default=None)
    filesize_limit = sa.Column(sa.String, default='5 Megabytes')
    integrate_with_pmm = sa.Column(sa.Boolean, default=False, nullable=False)
    downloaded_only = sa.Column(sa.Boolean, default=True, nullable=False)
    libraries = sa.Column(MutableList.as_mutable(sa.JSON), default=[], nullable=False)

    minimum_dimensions = sa.Column(sa.String, default=None)
    skip_localized = sa.Column(sa.Boolean, default=True, nullable=False)
    logo_language_priority = sa.Column(MutableList.as_mutable(sa.JSON), default=[], nullable=False)

class Loaded(Base):
    __tablename__ = 'loaded'

    id = sa.Column(sa.Integer, primary_key=True)
    # Existing Columns for migrating
    media_server = sa.Column(sa.String, nullable=False)
    # New column(s)
    interface_id = sa.Column(sa.Integer, sa.ForeignKey('connection.id'))

class Series(Base):
    __tablename__ = 'series'

    id = sa.Column(sa.Integer, primary_key=True)
    # Existing Columns for migrating
    episode_data_source = sa.Column(sa.String)
    emby_library_name = sa.Column(sa.String)
    jellyfin_library_name = sa.Column(sa.String)
    plex_library_name = sa.Column(sa.String)
    # New column(s)
    libraries = sa.Column(MutableList.as_mutable(sa.JSON), default=[], nullable=False)
    data_source_id = sa.Column(sa.Integer, sa.ForeignKey('connection.id'), default=None)

class Template(Base):
    __tablename__ = 'template'

    id = sa.Column(sa.Integer, primary_key=True)
    # Existing Columns for migrating
    episode_data_source = sa.Column(sa.String)
    # New column(s)
    data_source_id = sa.Column(sa.Integer, sa.ForeignKey('connection.id'), default=None)

class Sync(Base):
    __tablename__ = 'sync'
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    interface_id = sa.Column(sa.Integer, sa.ForeignKey('connection.id'))


def upgrade() -> None:
    log = contextualize()
    log.debug(f'Upgrading SQL to Revision[{revision}]..')

    op.create_table('connection',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('interface_type', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('api_key', sa.String(), nullable=False),
        sa.Column('use_ssl', sa.Boolean(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('filesize_limit', sa.String(), nullable=True),
        sa.Column('integrate_with_pmm', sa.Boolean(), nullable=False),
        sa.Column('downloaded_only', sa.Boolean(), nullable=False),
        sa.Column('libraries', sa.JSON(), nullable=False),
        sa.Column('minimum_dimensions', sa.String(), nullable=True),
        sa.Column('skip_localized', sa.Boolean(), nullable=False),
        sa.Column('logo_language_priority', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('connection', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_connection_id'), ['id'], unique=False)

    with op.batch_alter_table('loaded', schema=None) as batch_op:
        batch_op.add_column(sa.Column('library_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('interface_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_connection_loaded', 'connection', ['interface_id'], ['id'])

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('data_source_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('libraries', sa.JSON(), nullable=False))
        batch_op.create_foreign_key('fk_connection_series', 'connection', ['data_source_id'], ['id'])

    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.add_column(sa.Column('interface_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_connection_sync', 'connection', ['interface_id'], ['id'])

    with op.batch_alter_table('template', schema=None) as batch_op:
        batch_op.add_column(sa.Column('data_source_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_connection_template', 'connection', ['data_source_id'], ['id'])

    # Perform data migration
    session = Session(bind=op.get_bind())

    # Turn existing connections from Preferences into Connection objects
    emby, jellyfin, plex, sonarr, tmdb = None, None, None, None, None
    if PreferencesLocal.emby_url:
        emby = Connection(
            interface_type='Emby',
            enabled=True,
            name='Emby Server',
            url=PreferencesLocal.emby_url,
            api_key=PreferencesLocal.emby_api_key,
            use_ssl=PreferencesLocal.emby_use_ssl,
            username=PreferencesLocal.emby_username,
        )
        session.add(emby)
        log.info(f'Created Emby Connection[{emby.id}]')
    if PreferencesLocal.jellyfin_url:
        jellyfin = Connection(
            interface_type='Jellyfin',
            enabled=True,
            name='Jellyfin Server',
            url=PreferencesLocal.jellyfin_url,
            api_key=PreferencesLocal.jellyfin_api_key,
            use_ssl=PreferencesLocal.jellyfin_use_ssl,
            username=PreferencesLocal.jellyfin_username,
        )
        session.add(jellyfin)
        log.info(f'Created Jellyfin Connection[{jellyfin.id}]')
    if PreferencesLocal.plex_url:
        plex = Connection(
            interface_type='Plex',
            enabled=True,
            name='Plex Server',
            url=PreferencesLocal.plex_url,
            api_key=PreferencesLocal.plex_token,
            use_ssl=PreferencesLocal.plex_use_ssl,
            username=PreferencesLocal.plex_username,
            integrate_with_pmm=PreferencesLocal.plex_integrate_with_pmm,
        )
        session.add(plex)
        log.info(f'Created Plex Connection[{plex.id}]')
    if PreferencesLocal.sonarr_url:
        sonarr = Connection(
            interface='Sonarr',
            enabled=True,
            name='Sonarr Server',
            url=PreferencesLocal.sonarr_url,
            api_key=PreferencesLocal.sonarr_api_key,
            use_ssl=PreferencesLocal.sonarr_use_ssl,
            downloaded_only=PreferencesLocal.sonarr_downloaded_only,
        )
        session.add(sonarr)
        log.info(f'Created Sonarr Connection[{sonarr.id}]')
    if PreferencesLocal.tmdb_api_key:
        tmdb = Connection(
            interface_type='TMDb',
            enabled=True,
            name='TMDb',
            minimum_dimensions=f'{PreferencesLocal.tmdb_minimum_width}x{PreferencesLocal.tmdb_minimum_height}',
            skip_localized=PreferencesLocal.tmdb_skip_localized,
            logo_language_priority=PreferencesLocal.tmdb_logo_language_priority,
        )

    # Migrate the global Episode data source and image source priorities
    if emby and PreferencesLocal.episode_data_source == 'Emby':
        PreferencesLocal.episode_data_source = emby.id
    elif jellyfin and PreferencesLocal.episode_data_source == 'Jellyfin':
        PreferencesLocal.episode_data_source = jellyfin.id
    elif sonarr and PreferencesLocal.episode_data_source == 'Sonarr':
        PreferencesLocal.episode_data_source = sonarr.id
    elif PreferencesLocal.episode_data_source == 'TMDb':
        PreferencesLocal.episode_data_source = tmdb.id
    else:
        PreferencesLocal.episode_data_source = None
    log.debug(f'Migrated Global Episode data source to {PreferencesLocal.episode_data_source}')

    isp = []
    for source in PreferencesLocal.image_source_priority:
        if emby and source == 'Emby':
            isp.append(emby.id)
        elif jellyfin and source == 'Jellyfin':
            isp.append(jellyfin.id)
        elif plex and source == 'Plex':
            isp.append(plex.id)
        elif source == 'TMDb':
            isp.append(tmdb.id)
    PreferencesLocal.image_source_priority = isp
    log.debug(f'Migrated Global Image Source Priority to {isp}')

    # Migrate Loaded media_server into interface_id
    for loaded in session.query(Loaded).all():
        if loaded.media_server == 'Emby' and emby:
            loaded.interface_id = emby.id
        elif loaded.media_server == 'Jellyfin' and jellyfin:
            loaded.interface_id = jellyfin.id
        elif loaded.media_server == 'Plex' and plex:
            loaded.interface_id = plex.id

    # Migrate Series *_library_name into libraries list
    for series in session.query(Series).all():
        libraries = []
        if series.emby_library_name and emby:
            libraries.append({
                'interface': 'Emby',
                'interface_id': emby.id,
                'name': series.emby_library_name,
            })
        if series.jellyfin_library_name and jellyfin:
            libraries.append({
                'interface': 'Jellyfin',
                'interface_id': jellyfin.id,
                'name': series.jellyfin_library_name,
            })
        if series.plex_library_name and plex:
            libraries.append({
                'interface': 'Plex',
                'interface_id': plex.id,
                'name': series.plex_library_name,
            })
        series.libraries = libraries
        if libraries:
            log.debug(f'Initialized Series[{series.id}].libraries = {libraries}')

    # Migrate Series and Template episode_data_source into data_source
    for series in session.query(Series).all():
        if emby and series.episode_data_source in ('Emby', 'emby'):
            series.data_source_id = emby.id
        elif jellyfin and series.episode_data_source in ('Jellyfin', 'jellyfin'):
            series.data_source_id = jellyfin.id
        elif plex and series.episode_data_source in ('Plex', 'plex'):
            series.data_source_id = plex.id
        elif sonarr and series.episode_data_source in ('Sonarr', 'sonarr'):
            series.data_source_id = sonarr.id
        elif tmdb and series.episode_data_source in ('TMDb', 'tmdb'):
            series.data_source_id = tmdb.id

        if series.data_source_id:
            log.debug(f'Initialized Series[{series.id}].data_source_id = {series.data_source_id}')
    for template in session.query(Template).all():
        if emby and template.episode_data_source in ('Emby', 'emby'):
            template.data_source_id = emby.id
        elif jellyfin and template.episode_data_source in ('Jellyfin', 'jellyfin') :
            template.data_source_id = jellyfin.id
        elif plex and template.episode_data_source in ('Plex', 'plex'):
            template.data_source_id = plex.id
        elif sonarr and template.episode_data_source in ('Sonarr', 'sonarr'):
            template.data_source_id = sonarr.id
        elif tmdb and template.episode_data_source in ('TMDb', 'tmdb'):
            template.data_source_id = tmdb.id

        if template.data_source_id:
            log.debug(f'Initialized Template[{template.id}].data_source_id = {template.data_source_id}')

    # Commit changes
    session.commit()

    # Drop columns once migration is completed
    with op.batch_alter_table('loaded', schema=None) as batch_op:
        batch_op.drop_column('media_server')

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.drop_column('emby_library_name')
        batch_op.drop_column('jellyfin_library_name')
        batch_op.drop_column('plex_library_name')
        batch_op.drop_column('episode_data_source')

    with op.batch_alter_table('template', schema=None) as batch_op:
        batch_op.drop_column('episode_data_source')

    # Commit changes to Preferences
    PreferencesLocal.commit(log=log)

    log.info(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    with op.batch_alter_table('loaded', schema=None) as batch_op:
        batch_op.add_column(sa.Column('media_server', sa.VARCHAR(), nullable=False))
        batch_op.drop_constraint('fk_connection_loaded', type_='foreignkey')
        batch_op.drop_column('interface_id')
        batch_op.drop_column('library_name')

    with op.batch_alter_table('template', schema=None) as batch_op:
        batch_op.add_column(sa.Column('episode_data_source', sa.VARCHAR(), nullable=True))
        batch_op.drop_constraint('fk_connection_template', type_='foreignkey')
        batch_op.drop_column('data_source_id')

    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.drop_constraint('fk_connection_sync', type_='foreignkey')
        batch_op.drop_column('interface_id')

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('episode_data_source', sa.VARCHAR(), nullable=True))
        batch_op.add_column(sa.Column('plex_library_name', sa.VARCHAR(), nullable=True))
        batch_op.add_column(sa.Column('jellyfin_library_name', sa.VARCHAR(), nullable=True))
        batch_op.add_column(sa.Column('emby_library_name', sa.VARCHAR(), nullable=True))
        batch_op.drop_constraint('fk_connection_series', type_='foreignkey')
        batch_op.drop_column('libraries')
        batch_op.drop_column('data_source_id')

    with op.batch_alter_table('connection', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_connection_id'))

    op.drop_table('connection')
