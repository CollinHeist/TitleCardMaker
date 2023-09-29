"""Create Connections Table
Create new Connections SQL table / Model
Modify Series table:
- Turn separate emby,jellyfin,plex_library_name columns into single libraries
  column that is a JSON list object like
  [{'media_server': (Emby/Jellyfin/Plex), 'interface_id': (int), 'name': (str)}]
- Perform data migration of existing Series libraries into the above objects
- Remove emby_library_name, jellyfin_library_name, and plex_library_name
  columns.
Modify Sync table:
- Add new interface_id and connection columns / relationships as a Sync now must
be tied to an existing Connection.
Modify Template table:
- Turn episode_data_source column into data_source column

Revision ID: a61f373185d4
Revises: 4d7cb48238be
Create Date: 2023-09-28 12:56:59.752356

"""
from alembic import op
import sqlalchemy as sa
from modules.Debug import contextualize

# revision identifiers, used by Alembic.
revision = 'a61f373185d4'
down_revision = '4d7cb48238be'
branch_labels = None
depends_on = None

# Models necessary for data migration
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Session, relationship
from app.database.session import PreferencesLocal

Base = declarative_base()

class Connection(Base):
    __tablename__ = 'connection'

    id = sa.Column(sa.Integer, primary_key=True, index=True)

    series = relationship('Series', back_populates='data_source')
    syncs = relationship('Sync', back_populates='connection')
    templates = relationship('Template', back_populates='data_source')

    interface = sa.Column(sa.String, nullable=False)
    enabled = sa.Column(sa.Boolean, default=False, nullable=False)
    name = sa.Column(sa.String, nullable=False)

    url = sa.Column(sa.String, nullable=False)
    api_key = sa.Column(sa.String, nullable=False)
    use_ssl = sa.Column(sa.Boolean, default=True, nullable=False)

    username = sa.Column(sa.String, default=None)
    filesize_limit = sa.Column(sa.String, default='5 Megabytes')
    integrate_with_pmm = sa.Column(sa.Boolean, default=False, nullable=False)
    downloaded_only = sa.Column(sa.Boolean, default=True, nullable=False)
    libraries = sa.Column(MutableList.as_mutable(sa.JSON), default=[], nullable=False)

class Series(Base):
    __tablename__ = 'series'

    id = sa.Column(sa.Integer, primary_key=True)
    # Existing Columns for migrating
    episode_data_source = sa.Column(sa.String)
    emby_library_name = sa.Column(sa.String)
    jellyfin_library_name = sa.Column(sa.String)
    plex_library_name = sa.Column(sa.String)
    # New column
    libraries = sa.Column(MutableList.as_mutable(sa.JSON), default=[], nullable=False)
    data_source_id = sa.Column(sa.Integer, sa.ForeignKey('connection.id'), default=None)
    data_source = relationship('Connection', back_populates='series')

class Template(Base):
    __tablename__ = 'template'

    id = sa.Column(sa.Integer, primary_key=True)
    # Existing Columns for migrating
    episode_data_source = sa.Column(sa.String)
    # New column
    data_source_id = sa.Column(sa.Integer, sa.ForeignKey('connection.id'), default=None)
    data_source = relationship('Connection', back_populates='templates')

class Sync(Base):
    __tablename__ = 'sync'
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    connection = relationship('Connection', back_populates='syncs')
    interface_id = sa.Column(sa.Integer, sa.ForeignKey('connection.id'))


def upgrade() -> None:
    log = contextualize()
    log.debug(f'Upgrading SQL to Revision[{revision}]..')

    op.create_table('connection',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('interface', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('api_key', sa.String(), nullable=False),
        sa.Column('use_ssl', sa.Boolean(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('filesize_limit', sa.String(), nullable=True),
        sa.Column('integrate_with_pmm', sa.Boolean(), nullable=False),
        sa.Column('downloaded_only', sa.Boolean(), nullable=False),
        sa.Column('libraries', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('connection', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_connection_id'), ['id'], unique=False)

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
    emby, jellyfin, plex, sonarr = None, None, None, None
    if PreferencesLocal.emby_url:
        emby = Connection(
            interface='Emby',
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
            interface='Jellyfin',
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
            interface='Plex',
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

    # Migrate the global Episode data source and image source priorities
    if emby and PreferencesLocal.episode_data_source == 'Emby':
        PreferencesLocal.episode_data_source = {'interface': 'Emby', 'interface_id': emby.id}
    elif jellyfin and PreferencesLocal.episode_data_source == 'Jellyfin':
        PreferencesLocal.episode_data_source = {'interface': 'Jellyfin', 'interface_id': jellyfin.id}
    elif sonarr and PreferencesLocal.episode_data_source == 'Sonarr':
        PreferencesLocal.episode_data_source = {'interface': 'Sonarr', 'interface_id': sonarr.id}
    elif PreferencesLocal.episode_data_source == 'TMDb':
        PreferencesLocal.episode_data_source = {'interface': 'TMDb', 'interface_id': 0}
    else:
        PreferencesLocal.episode_data_source = PreferencesLocal.DEFAULT_EPISODE_DATA_SOURCE
    log.debug(f'Migrated Global Episode data source to {PreferencesLocal.episode_data_source}')

    isp = []
    for source in PreferencesLocal.image_source_priority:
        if emby and source == 'Emby':
            isp.append({'interface': source, 'interface_id': emby.id})
        elif jellyfin and source == 'Jellyfin':
            isp.append({'interface': source, 'interface_id': jellyfin.id})
        elif plex and source == 'Plex':
            isp.append({'interface': source, 'interface_id': plex.id})
        elif source == 'TMDb':
            isp.append({'interface': source, 'interface_id': 0})
    PreferencesLocal.image_source_priority = isp
    log.debug(f'Migrated Global Image Source Priority to {isp}')

    # Migrate Series *_library_name into libraries list
    for series in session.query(Series).all():
        libraries = []
        if series.emby_library_name and emby:
            libraries.append({
                'media_server': 'Emby',
                'interface_id': emby.id,
                'name': series.emby_library_name,
            })
        if series.jellyfin_library_name and jellyfin:
            libraries.append({
                'media_server': 'Jellyfin',
                'interface_id': jellyfin.id,
                'name': series.jellyfin_library_name,
            })
        if series.plex_library_name and plex:
            libraries.append({
                'media_server': 'Plex',
                'interface_id': plex.id,
                'name': series.plex_library_name,
            })
        series.libraries = libraries
        if libraries:
            log.debug(f'Initialized Series[{series.id}].libraries = {libraries}')

    # Migrate Series and Template episode_data_source into data_source
    for series in session.query(Series).all():
        if emby and series.episode_data_source in ('Emby', 'emby'):
            series.data_source = emby
        elif jellyfin and series.episode_data_source in ('Jellyfin', 'jellyfin'):
            series.data_source = jellyfin
        elif plex and series.episode_data_source in ('Plex', 'plex'):
            series.data_source = plex
        elif sonarr and series.episode_data_source in ('Sonarr', 'sonarr'):
            series.data_source = sonarr

        if series.data_source:
            log.debug(f'Initialized Series[{series.id}].data_source = {series.data_source}')
    for template in session.query(Template).all():
        if emby and template.episode_data_source in ('Emby', 'emby'):
            template.data_source = emby
        elif jellyfin and template.episode_data_source in ('Jellyfin', 'jellyfin') :
            template.data_source = jellyfin
        elif plex and template.episode_data_source in ('Plex', 'plex'):
            template.data_source = plex
        elif sonarr and template.episode_data_source in ('Sonarr', 'sonarr'):
            template.data_source = sonarr

        if template.data_source:
            log.debug(f'Initialized Template[{template.id}].data_source = {template.data_source}')

    # Drop columns once migration is completed

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
