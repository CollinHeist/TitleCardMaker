"""Initialize database

Revision ID: 693dd5aa47cd
Revises: 
Create Date: 2023-05-18 17:56:58.518419
"""

from alembic import op
import sqlalchemy as sa

from modules.Debug import contextualize

# revision identifiers, used by Alembic.
revision = '693dd5aa47cd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    log = contextualize()
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    op.create_table('font',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('file', sa.String(), nullable=True),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('title_case', sa.String(), nullable=True),
        sa.Column('size', sa.Float(), nullable=True),
        sa.Column('kerning', sa.Float(), nullable=True),
        sa.Column('stroke_width', sa.Float(), nullable=True),
        sa.Column('interline_spacing', sa.Integer(), nullable=True),
        sa.Column('vertical_shift', sa.Integer(), nullable=True),
        sa.Column('validate_characters', sa.Boolean(), nullable=True),
        sa.Column('delete_missing', sa.Boolean(), nullable=True),
        sa.Column('replacements', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_font_id'), ['id'], unique=False)

    op.create_table('sync',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('interface', sa.String(), nullable=False),
        sa.Column('required_tags', sa.JSON(), nullable=False),
        sa.Column('required_libraries', sa.JSON(), nullable=False),
        sa.Column('excluded_tags', sa.JSON(), nullable=False),
        sa.Column('excluded_libraries', sa.JSON(), nullable=False),
        sa.Column('downloaded_only', sa.Boolean(), nullable=True),
        sa.Column('monitored_only', sa.Boolean(), nullable=True),
        sa.Column('required_series_type', sa.String(), nullable=True),
        sa.Column('excluded_series_type', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_sync_id'), ['id'], unique=False)

    op.create_table('series',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('font_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('sync_id', sa.Integer(), nullable=True),
        sa.Column('monitored', sa.Boolean(), nullable=False),
        sa.Column('poster_file', sa.String(), nullable=True),
        sa.Column('poster_url', sa.String(), nullable=True),
        sa.Column('directory', sa.String(), nullable=True),
        sa.Column('emby_library_name', sa.String(), nullable=True),
        sa.Column('jellyfin_library_name', sa.String(), nullable=True),
        sa.Column('plex_library_name', sa.String(), nullable=True),
        sa.Column('card_filename_format', sa.String(), nullable=True),
        sa.Column('episode_data_source', sa.String(), nullable=True),
        sa.Column('sync_specials', sa.Boolean(), nullable=True),
        sa.Column('skip_localized_images', sa.Boolean(), nullable=True),
        sa.Column('translations', sa.JSON(), nullable=True),
        sa.Column('match_titles', sa.Boolean(), nullable=False),
        sa.Column('emby_id', sa.Integer(), nullable=True),
        sa.Column('imdb_id', sa.String(), nullable=True),
        sa.Column('jellyfin_id', sa.String(), nullable=True),
        sa.Column('sonarr_id', sa.String(), nullable=True),
        sa.Column('tmdb_id', sa.Integer(), nullable=True),
        sa.Column('tvdb_id', sa.Integer(), nullable=True),
        sa.Column('tvrage_id', sa.Integer(), nullable=True),
        sa.Column('font_color', sa.String(), nullable=True),
        sa.Column('font_title_case', sa.String(), nullable=True),
        sa.Column('font_size', sa.Float(), nullable=True),
        sa.Column('font_kerning', sa.Float(), nullable=True),
        sa.Column('font_stroke_width', sa.Float(), nullable=True),
        sa.Column('font_interline_spacing', sa.Integer(), nullable=True),
        sa.Column('font_vertical_shift', sa.Integer(), nullable=True),
        sa.Column('card_type', sa.String(), nullable=True),
        sa.Column('hide_season_text', sa.Boolean(), nullable=True),
        sa.Column('season_titles', sa.JSON(), nullable=True),
        sa.Column('hide_episode_text', sa.Boolean(), nullable=True),
        sa.Column('episode_text_format', sa.String(), nullable=True),
        sa.Column('unwatched_style', sa.String(), nullable=True),
        sa.Column('watched_style', sa.String(), nullable=True),
        sa.Column('extras', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['font_id'], ['font.id'], ),
        sa.ForeignKeyConstraint(['sync_id'], ['sync.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('font_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('filters', sa.JSON(), nullable=False),
        sa.Column('card_filename_format', sa.String(), nullable=True),
        sa.Column('episode_data_source', sa.String(), nullable=True),
        sa.Column('sync_specials', sa.Boolean(), nullable=True),
        sa.Column('skip_localized_images', sa.Boolean(), nullable=True),
        sa.Column('translations', sa.JSON(), nullable=False),
        sa.Column('card_type', sa.String(), nullable=True),
        sa.Column('hide_season_text', sa.Boolean(), nullable=True),
        sa.Column('season_titles', sa.JSON(), nullable=False),
        sa.Column('hide_episode_text', sa.Boolean(), nullable=True),
        sa.Column('episode_text_format', sa.String(), nullable=True),
        sa.Column('unwatched_style', sa.String(), nullable=True),
        sa.Column('watched_style', sa.String(), nullable=True),
        sa.Column('extras', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['font_id'], ['font.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('template', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_template_id'), ['id'], unique=False)

    op.create_table('episode',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('font_id', sa.Integer(), nullable=True),
        sa.Column('series_id', sa.Integer(), nullable=True),
        sa.Column('source_file', sa.String(), nullable=True),
        sa.Column('card_file', sa.String(), nullable=True),
        sa.Column('watched', sa.Boolean(), nullable=True),
        sa.Column('season_number', sa.Integer(), nullable=False),
        sa.Column('episode_number', sa.Integer(), nullable=False),
        sa.Column('absolute_number', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('match_title', sa.Boolean(), nullable=True),
        sa.Column('auto_split_title', sa.Boolean(), nullable=False),
        sa.Column('card_type', sa.String(), nullable=True),
        sa.Column('hide_season_text', sa.Boolean(), nullable=True),
        sa.Column('season_text', sa.String(), nullable=True),
        sa.Column('hide_episode_text', sa.Boolean(), nullable=True),
        sa.Column('episode_text', sa.String(), nullable=True),
        sa.Column('unwatched_style', sa.String(), nullable=True),
        sa.Column('watched_style', sa.String(), nullable=True),
        sa.Column('font_color', sa.String(), nullable=True),
        sa.Column('font_size', sa.Float(), nullable=True),
        sa.Column('font_kerning', sa.Float(), nullable=True),
        sa.Column('font_stroke_width', sa.Float(), nullable=True),
        sa.Column('font_interline_spacing', sa.Integer(), nullable=True),
        sa.Column('font_vertical_shift', sa.Integer(), nullable=True),
        sa.Column('emby_id', sa.Integer(), nullable=True),
        sa.Column('imdb_id', sa.String(), nullable=True),
        sa.Column('jellyfin_id', sa.String(), nullable=True),
        sa.Column('tmdb_id', sa.Integer(), nullable=True),
        sa.Column('tvdb_id', sa.Integer(), nullable=True),
        sa.Column('tvrage_id', sa.Integer(), nullable=True),
        sa.Column('airdate', sa.DateTime(), nullable=True),
        sa.Column('extras', sa.JSON(), nullable=True),
        sa.Column('translations', sa.JSON(), nullable=True),
        sa.Column('image_source_attempts', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['font_id'], ['font.id'], ),
        sa.ForeignKeyConstraint(['series_id'], ['series.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_episode_id'), ['id'], unique=False)

    op.create_table('series_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('series_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['series_id'], ['series.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['template.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('series_templates', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_series_templates_id'), ['id'], unique=False)

    op.create_table('sync_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('sync_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['sync_id'], ['sync.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['template.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('sync_templates', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_sync_templates_id'), ['id'], unique=False)

    op.create_table('card',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('series_id', sa.Integer(), nullable=True),
        sa.Column('episode_id', sa.Integer(), nullable=True),
        sa.Column('source_file', sa.String(), nullable=False),
        sa.Column('card_file', sa.String(), nullable=False),
        sa.Column('filesize', sa.Integer(), nullable=True),
        sa.Column('card_type', sa.String(), nullable=False),
        sa.Column('title_text', sa.String(), nullable=False),
        sa.Column('season_text', sa.String(), nullable=False),
        sa.Column('hide_season_text', sa.Boolean(), nullable=False),
        sa.Column('episode_text', sa.String(), nullable=False),
        sa.Column('hide_episode_text', sa.Boolean(), nullable=False),
        sa.Column('font_file', sa.String(), nullable=False),
        sa.Column('font_color', sa.String(), nullable=False),
        sa.Column('font_size', sa.Float(), nullable=False),
        sa.Column('font_kerning', sa.Float(), nullable=False),
        sa.Column('font_stroke_width', sa.Float(), nullable=False),
        sa.Column('font_interline_spacing', sa.Integer(), nullable=False),
        sa.Column('font_vertical_shift', sa.Integer(), nullable=False),
        sa.Column('blur', sa.Boolean(), nullable=False),
        sa.Column('grayscale', sa.Boolean(), nullable=False),
        sa.Column('extras', sa.JSON(), nullable=False),
        sa.Column('season_number', sa.Integer(), nullable=False),
        sa.Column('episode_number', sa.Integer(), nullable=False),
        sa.Column('absolute_number', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['episode_id'], ['episode.id'], ),
        sa.ForeignKeyConstraint(['series_id'], ['series.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_card_id'), ['id'], unique=False)

    op.create_table('episode_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('episode_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['episode_id'], ['episode.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['template.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('episode_templates', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_episode_templates_id'), ['id'], unique=False)

    op.create_table('loaded',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('series_id', sa.Integer(), nullable=True),
        sa.Column('episode_id', sa.Integer(), nullable=True),
        sa.Column('card_id', sa.Integer(), nullable=True),
        sa.Column('media_server', sa.String(), nullable=False),
        sa.Column('filesize', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['card_id'], ['card.id'], ),
        sa.ForeignKeyConstraint(['episode_id'], ['episode.id'], ),
        sa.ForeignKeyConstraint(['filesize'], ['card.filesize'], ),
        sa.ForeignKeyConstraint(['series_id'], ['series.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    op.drop_table('loaded')
    with op.batch_alter_table('episode_templates', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_episode_templates_id'))

    op.drop_table('episode_templates')
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_card_id'))

    op.drop_table('card')
    with op.batch_alter_table('sync_templates', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_sync_templates_id'))

    op.drop_table('sync_templates')
    with op.batch_alter_table('series_templates', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_series_templates_id'))

    op.drop_table('series_templates')
    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_episode_id'))

    op.drop_table('episode')
    with op.batch_alter_table('template', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_template_id'))

    op.drop_table('template')
    op.drop_table('series')
    with op.batch_alter_table('sync', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_sync_id'))

    op.drop_table('sync')
    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_font_id'))

    op.drop_table('font')
