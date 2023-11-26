"""Support multiple interface connections
Create new Connections SQL table / Model
- Turn existing connection details from global Preferences into
  Connection objects which are assigned during SQL migration.
Modify Card table:
- Add new interface_id and library_name columns
- Perform data migration of existing Card objects and attempt to associate them
  with an existing/newly created Connection from the parent Series.
Modify Loaded table:
- Add new interface_id column tied to newly created Connection(s)
- Remove media_server column
- Perform data migration on existing Loaded assets and attempt to associate them
  with an existing/newly created Connection from the parent Series.
Modify Series table:
- Turn separate emby/jellyfin/plex _library_name columns into single
  libraries column that is a JSON list object like
  [{'media_server': (Emby/Jellyfin/Plex), 'interface_id': (int), 'name': (str)}]
- Perform data migration of existing Series libraries into the above
  objects
- Remove emby_library_name, jellyfin_library_name, and plex_library_name
  columns
- Migrate the emby_id, jellyfin_id, and sonarr_id columns into their new
  multi-connection DatabaseID equivalents (i.e.
  {interface_id}:{library}:{id}).
Modify Episode table:
- Migrate the emby_id, and jellyfin_id, columns into their new multi-
  connection DatabaseID equivalents (i.e. {interface_id}:{library}:{id}).
- Add new watched_statuses column which contains a dictionary mapping
interface IDs -> library names -> watched statuses
- Remove the watched column
- Migrate old watched column into new watched_statuses objects
Modify Sync table:
- Add new interface_id and connection columns / relationships as a Sync
  now must be tied to an existing Connection.
Modify Template table:
- Turn episode_data_source column into data_source column
- Convert server-type specific library filter conditions into library
  agnostic "contains" conditions

Revision ID: a61f373185d4
Revises: caec4f618689
Create Date: 2023-09-28 12:56:59.752356
"""
# pylint: disable
from alembic import op
import sqlalchemy as sa
from modules.Debug import contextualize

# revision identifiers, used by Alembic.
revision = 'a61f373185d4'
down_revision = 'caec4f618689'
branch_labels = None
depends_on = None

# Models necessary for data migration
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, Session, relationship
from app.database.session import PreferencesLocal

Base = declarative_base()

class Card(Base):
    __tablename__ = 'card'

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    # Existing columns
    series_id = sa.Column(sa.Integer, sa.ForeignKey('series.id'))
    episode_id = sa.Column(sa.Integer, sa.ForeignKey('episode.id'))
    loaded = relationship('Loaded', back_populates='card')
    # New Column(s)
    interface_id = sa.Column(sa.Integer, sa.ForeignKey('connection.id'))
    library_name = sa.Column(sa.String, default=None)

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

class Episode(Base):
    __tablename__ = 'episode'

    id = sa.Column(sa.Integer, primary_key=True)
    series_id = sa.Column(sa.Integer, sa.ForeignKey('series.id'))
    series = relationship('Series', back_populates='episodes')
    emby_id = sa.Column(sa.String)
    jellyfin_id = sa.Column(sa.String)
    # New column
    watched_statuses = sa.Column(MutableDict.as_mutable(sa.JSON), default={}, nullable=False)
    # Existing column to be removed
    watched = sa.Column(sa.Boolean)

class Loaded(Base):
    __tablename__ = 'loaded'

    id = sa.Column(sa.Integer, primary_key=True)
    # Existing Columns for migrating
    card_id = sa.Column(sa.Integer, sa.ForeignKey('card.id'))
    episode_id = sa.Column(sa.Integer, sa.ForeignKey('episode.id'))
    series_id = sa.Column(sa.Integer, sa.ForeignKey('series.id'))
    media_server = sa.Column(sa.String, nullable=False)
    card = relationship('Card', back_populates='loaded')
    series = relationship('Series', back_populates='loaded')
    # New column(s)
    interface_id = sa.Column(sa.Integer, sa.ForeignKey('connection.id'))
    library_name = sa.Column(sa.String, default=None)

class Series(Base):
    __tablename__ = 'series'

    id = sa.Column(sa.Integer, primary_key=True)
    # Existing Columns for migrating
    episode_data_source = sa.Column(sa.String)
    emby_library_name = sa.Column(sa.String)
    jellyfin_library_name = sa.Column(sa.String)
    plex_library_name = sa.Column(sa.String)
    emby_id = sa.Column(sa.String)
    jellyfin_id = sa.Column(sa.String)
    sonarr_id = sa.Column(sa.String)
    episodes: Mapped[list[Episode]] = relationship(Episode, back_populates='series')
    loaded: Mapped[list[Loaded]] = relationship(Loaded, back_populates='series')
    # New column(s)
    libraries = sa.Column(MutableList.as_mutable(sa.JSON), default=[])
    data_source_id = sa.Column(sa.Integer, sa.ForeignKey('connection.id'), default=None)

class Template(Base):
    __tablename__ = 'template'

    id = sa.Column(sa.Integer, primary_key=True)
    # Existing Columns for migrating
    episode_data_source = sa.Column(sa.String)
    filters = sa.Column(MutableList.as_mutable(sa.JSON), default=[], nullable=False)
    # New column(s)
    data_source_id = sa.Column(sa.Integer, sa.ForeignKey('connection.id'), default=None)

class Sync(Base):
    __tablename__ = 'sync'
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    interface = sa.Column(sa.String, nullable=False)
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

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.add_column(sa.Column('interface_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('library_name', sa.String(), nullable=True))
        batch_op.create_foreign_key('fk_connection_card', 'connection', ['interface_id'], ['id'])

    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.add_column(sa.Column('watched_statuses', sa.JSON(), server_default='{}', nullable=False))

    with op.batch_alter_table('loaded', schema=None) as batch_op:
        batch_op.add_column(sa.Column('library_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('interface_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_connection_loaded', 'connection', ['interface_id'], ['id'])

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('data_source_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('libraries', sa.JSON(), server_default='[]'))
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
            name='Emby',
            url=PreferencesLocal.emby_url,
            api_key=PreferencesLocal.emby_api_key,
            use_ssl=PreferencesLocal.emby_use_ssl,
            username=PreferencesLocal.emby_username,
        )
        session.add(emby)
        session.commit()
        log.info(f'Created Emby Connection[{emby.id}]')
    if PreferencesLocal.jellyfin_url:
        jellyfin = Connection(
            interface_type='Jellyfin',
            enabled=True,
            name='Jellyfin',
            url=PreferencesLocal.jellyfin_url,
            api_key=PreferencesLocal.jellyfin_api_key,
            use_ssl=PreferencesLocal.jellyfin_use_ssl,
            username=PreferencesLocal.jellyfin_username,
        )
        session.add(jellyfin)
        session.commit()
        log.info(f'Created Jellyfin Connection[{jellyfin.id}]')
    if PreferencesLocal.plex_url:
        plex = Connection(
            interface_type='Plex',
            enabled=True,
            name='Plex',
            url=PreferencesLocal.plex_url,
            api_key=PreferencesLocal.plex_token,
            use_ssl=PreferencesLocal.plex_use_ssl,
            integrate_with_pmm=PreferencesLocal.plex_integrate_with_pmm,
        )
        session.add(plex)
        session.commit()
        log.info(f'Created Plex Connection[{plex.id}]')
    if PreferencesLocal.sonarr_url:
        sonarr = Connection(
            interface_type='Sonarr',
            enabled=True,
            name='Sonarr',
            url=PreferencesLocal.sonarr_url,
            api_key=PreferencesLocal.sonarr_api_key,
            use_ssl=PreferencesLocal.sonarr_use_ssl,
            downloaded_only=PreferencesLocal.sonarr_downloaded_only,
        )
        session.add(sonarr)
        session.commit()
        log.info(f'Created Sonarr Connection[{sonarr.id}]')
        log.warning(f'Cannot migrate Sonarr Libraries data - resetting')
    if PreferencesLocal.tmdb_api_key:
        tmdb = Connection(
            interface_type='TMDb',
            enabled=True,
            name='TMDb',
            api_key=PreferencesLocal.tmdb_api_key,
            minimum_dimensions=f'{PreferencesLocal.tmdb_minimum_width}x{PreferencesLocal.tmdb_minimum_height}',
            skip_localized=PreferencesLocal.tmdb_skip_localized,
            logo_language_priority=PreferencesLocal.tmdb_logo_language_priority,
        )
        session.add(tmdb)
        session.commit()
        log.info(f'Created TMDb Connection[{tmdb.id}]')

    # Migrate the global Episode data source and image source priorities
    if emby and PreferencesLocal.episode_data_source in ('Emby', 'emby'):
        PreferencesLocal.episode_data_source = emby.id
    elif jellyfin and PreferencesLocal.episode_data_source in ('Jellyfin', 'jellyfin'):
        PreferencesLocal.episode_data_source = jellyfin.id
    elif sonarr and PreferencesLocal.episode_data_source in ('Sonarr', 'sonarr'):
        PreferencesLocal.episode_data_source = sonarr.id
    elif PreferencesLocal.episode_data_source in ('TMDb', 'tmdb'):
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

    # Migrate Loaded interface_id and library_name
    for loaded in session.query(Loaded).all():
        # Delete unassociated Loaded objects
        if not loaded.series_id or not loaded.episode_id:
            log.debug(f'Loaded[{loaded.id}] has no parent object - deleting')
            session.delete(loaded)
            continue
        # Migrate columns from associated Series' library
        if loaded.media_server == 'Emby' and emby:
            loaded.interface_id = emby.id
            if loaded.series.emby_library_name:
                loaded.library_name = loaded.series.emby_library_name
        elif loaded.media_server == 'Jellyfin' and jellyfin:
            loaded.interface_id = jellyfin.id
            if loaded.series.jellyfin_library_name:
                loaded.library_name = loaded.series.jellyfin_library_name
        elif loaded.media_server == 'Plex' and plex:
            loaded.interface_id = plex.id
            if loaded.series.plex_library_name:
                loaded.library_name = loaded.series.plex_library_name
    log.debug(f'Migrated Loaded.interface_id and Loaded.library_name')

    # Migrate Card interface_id and library_name
    for card in session.query(Card).all():
        # Delete unassociated Card objects
        if not card.series_id or not card.episode_id:
            log.debug(f'Card[{card.id}] has no parent Series/Episode - deleting')
            session.delete(card)
            continue
        # Migrate columns from associated Loaded object
        if card.loaded:
            card.interface_id = card.loaded[0].interface_id
            card.library_name = card.loaded[0].library_name
    log.debug(f'Migrated Card.interface_id and Card.library_name')

    # Migrate Sync interface_id
    for sync in session.query(Sync).all():
        if sync.interface == 'Emby' and emby:
            sync.interface_id = emby.id
        elif sync.interface == 'Jellyfin' and jellyfin:
            sync.interface_id = jellyfin.id
        elif sync.interface == 'Plex' and plex:
            sync.interface_id = plex.id
        elif sync.interface == 'Sonarr' and sonarr:
            sync.interface_id = sonarr.id
        else:
            log.debug(f'No valid Connection for Sync[{sync.id}] - deleting')
            session.delete(sync)

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

    # Migrate Template filter conditions
    for template in session.query(Template).all():
        # Skip if no filters
        if not template.filters:
            continue

        # Re-create Template filters
        new_filters = []
        for filter_ in template.filters:
            arg, op_, ref = filter_['argument'], filter_['operation'], filter_['reference']

            # Convert Episode watched filters
            if arg == 'Episode is Watched':
                new_filters.append({
                    'argument': 'Episode Watched Status',
                    'operation': op_, 'reference': ref,
                })
                continue

            # Convert library name filters
            if not arg.startswith('Series Library Name'):
                new_filters.append(filter_)
                continue

            # Convert Filter argument
            new_arg = 'Series Library Names'
            log.debug(f'Converting Template[{template.id}] Filter argument '
                      f'"{arg}" to "Series Library Names"')

            # Convert Filter operation to list-equivalent (or log if impossible)
            if op_ == 'equals':
                new_op = 'contains'
                log.debug(f'Converting Template[{template.id}] Filter '
                          f'operation "{op_}" to "contains"')
            elif op_ == 'does not equal':
                new_op = 'does not contain'
                log.debug(f'Converting Template[{template.id}] Filter '
                          f'operation "{op_}" to "does not contain"')
            elif op_ in ('starts with', 'does not start with', 'matches',
                         'does not match'):
                new_op = 'contains'
                log.error(f'Cannot perfectly convert Template[{template.id}] '
                          f'Filter operation "{op_}"')
            else:
                new_op = op_
                log.warning(f'Not converting Template[{template.id}] Filter '
                            f'operation "{op_}"')
                continue
   
            new_filters.append({
                'argument': new_arg, 'operation': new_op, 'reference': ref,
            })

        template.filters = new_filters

    # Migrate Episode watched statuses into new objects
    for series in session.query(Series).all():
        # Skip Series with no or >1 library
        if len(series.libraries) == 0:
            continue
        if len(series.libraries) > 1:
            log.debug(f'Cannot migrate Episode watched statuses for Series[{series.id}] - has conflicting libraries')
            continue

        for episode in series.episodes:
            if episode.watched is not None:
                library = series.libraries[0]
                key = f'{library["interface_id"]}:{library["name"]}'
                episode.watched_statuses = {key: episode.watched}
    log.debug(f'Initialized Episode.watched_statuses')

    # Migrate Series and Episode Emby and Jellyfin IDs; and Series Sonarr IDs
    for series in session.query(Series).all():
        # Migratate {id} -> {interface_id}:{library_name}:{id}
        if series.emby_id:
            if series.emby_library_name and emby:
                series.emby_id = f'{emby.id}:{series.emby_library_name}:{series.emby_id}'
                log.debug(f'Migrated Series[{series.id}].emby_id = {series.emby_id}')
            else:
                series.emby_id = ''
                log.warning(f'Unable to migrate Series[{series.id}].emby_id')
        else:
            series.emby_id = ''
        # Migrate {id} -> {interface_id}:{library_name}:{id}
        if series.jellyfin_id:
            if series.jellyfin_library_name and jellyfin:
                series.jellyfin_id = f'{jellyfin.id}:{series.jellyfin_library_name}:{series.jellyfin_id}'
                log.debug(f'Migrated Series[{series.id}].jellyfin_id = {series.jellyfin_id}')
            else:
                series.jellyfin_id = ''
                log.warning(f'Unable to migrate Series[{series.id}].jellyfin_id')
        else:
            series.jellyfin_id = ''
        # Migrate 0:{id} -> {interface_id}:{id}
        if series.sonarr_id:
            if sonarr:
                series.sonarr_id = f'{sonarr.id}:{series.sonarr_id.split("-")[1]}'
                log.debug(f'Migrated Series[{series.id}].sonarr_id = {series.sonarr_id}')
            else:
                series.sonarr_id = ''
                log.warning(f'Unable to migrate Series[{series.id}].sonarr_id')
        else:
            series.sonarr_id = ''

        # Migrate this Series' Episodes
        for episode in series.episodes:
            # Migratate {id} -> {interface_id}:{library_name}:{id}
            if episode.emby_id:
                if series.emby_library_name and emby:
                    episode.emby_id = f'{emby.id}:{series.emby_library_name}:{episode.emby_id}'
                    log.debug(f'Migrated Episode[{episode.id}].emby_id = {episode.emby_id}')
                else:
                    episode.emby_id = ''
                    log.warning(f'Unable to migrate Episode[{episode.id}].emby_id')
            else:
                episode.emby_id = ''
            # Migratate {id} -> {interface_id}:{library_name}:{id}
            if episode.jellyfin_id:
                if series.jellyfin_library_name and jellyfin:
                    episode.jellyfin_id = f'{jellyfin.id}:{series.jellyfin_library_name}:{episode.jellyfin_id}'
                    log.debug(f'Migrated Episode[{episode.id}].jellyfin_id = {episode.jellyfin_id}')
                else:
                    episode.jellyfin_id = ''
                    log.warning(f'Unable to migrate Episode[{episode.id}].jellyfin_id')
            else:
                episode.jellyfin_id = ''

    # Delete Episodes w/ null IDs
    for episode in session.query(Episode).filter(sa.or_(Episode.emby_id.is_(None),
                                                        Episode.jellyfin_id.is_(None))):
        log.debug(f'Deleting Episode{episode.id} - no valid ID conversion')
        session.delete(episode)

    # Commit changes
    session.commit()

    # Drop columns once migration is completed
    with op.batch_alter_table('loaded', schema=None) as batch_op:
        batch_op.drop_column('media_server')

    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.drop_column('watched')

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.drop_column('emby_library_name')
        batch_op.drop_column('jellyfin_library_name')
        batch_op.drop_column('plex_library_name')
        batch_op.drop_column('episode_data_source')

    with op.batch_alter_table('template', schema=None) as batch_op:
        batch_op.drop_column('episode_data_source')

    # Commit changes to Preferences
    PreferencesLocal.commit()

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_constraint('fk_connection_card', type_='foreignkey')
        batch_op.drop_column('library_name')
        batch_op.drop_column('interface_id')

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
