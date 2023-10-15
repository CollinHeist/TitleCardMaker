# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from datetime import datetime
from json import loads
from re import sub as re_sub, IGNORECASE
from typing import Any, Optional

from pydantic import Field, root_validator, validator # pylint: disable=no-name-in-module

from app.schemas.base import Base
from app.schemas.font import TitleCase
from app.schemas.series import Condition, SeasonTitleRange, Translation

from modules.CleanPath import CleanPath

"""
Base classes
"""
class BlueprintBase(Base):
    @root_validator(skip_on_failure=True)
    def delete_null_args(cls, values):
        delete_keys = [key for key, value in values.items() if value is None]
        for key in delete_keys:
            del values[key]

        return values

class ConfigBase(BlueprintBase): # Base of Series, Episodes, and Templates
    font_id: Optional[int] = None
    card_type: Optional[str] = None
    hide_season_text: Optional[bool] = None
    hide_episode_text: Optional[bool] = None
    episode_text_format: Optional[str] = None
    translations: Optional[list[Translation]] = None
    season_title_ranges: Optional[list[SeasonTitleRange]] = None
    season_title_values: Optional[list[str]] = None
    extra_keys: Optional[list[str]] = None
    extra_values: Optional[list[Any]] = None
    skip_localized_images: Optional[bool] = None

class BaseSeriesEpisode(ConfigBase): # Base of Series and Episodes
    template_ids: list[int] = []
    match_titles: Optional[bool] = None
    font_color: Optional[str] = None
    font_title_case: Optional[TitleCase] = None
    font_size: Optional[float] = None
    font_kerning: Optional[float] = None
    font_stroke_width: Optional[float] = None
    font_interline_spacing: Optional[int] = None
    font_interword_spacing: Optional[int] = None
    font_vertical_shift: Optional[int] = None

"""
Creation classes
"""
class BlueprintSeries(BaseSeriesEpisode):
    source_files: list[str] = []

class BlueprintEpisode(BaseSeriesEpisode):
    title: Optional[str] = None
    match_title: Optional[bool] = None
    auto_split_title: Optional[bool] = None
    season_text: Optional[str] = None
    episode_text: Optional[str] = None

class BlueprintFont(BlueprintBase):
    name: str
    color: Optional[str] = None
    delete_missing: bool = None
    file: Optional[str] = None
    kerning: float = None
    interline_spacing: int = None
    interword_spacing: int = None
    replacements_in: list[str] = None
    replacements_out: list[str] = None
    size: float = None
    stroke_width: float = None
    title_case: Optional[TitleCase] = None
    vertical_shift: int = None

class BlueprintTemplate(ConfigBase):
    name: str
    filters: list[Condition] = []

class Blueprint(Base):
    series: BlueprintSeries
    episodes: dict[str, BlueprintEpisode] = {}
    templates: list[BlueprintTemplate] = []
    fonts: list[BlueprintFont] = []
    previews: list[str] = []
    description: list[str] = []

"""
Update classes
"""

"""
Return classes
"""
class DownloadableFile(Base):
    url: str
    filename: str

class ExportBlueprint(Blueprint):
    ...

class ImportBlueprint(Blueprint):
    ...

class RemoteBlueprintFont(BlueprintFont):
    file_download_url: Optional[str] = None

class RemoteBlueprintSeries(Base):
    name: str
    year: int
    imdb_id: Optional[str]
    tmdb_id: Optional[int]
    tvdb_id: Optional[int]

class RemoteBlueprint(Base):
    id: int
    blueprint_number: int
    creator: str
    created: datetime
    series: RemoteBlueprintSeries
    json_: Blueprint = Field(alias='json') # Any = Field(alias='json')#

    @validator('json_', pre=True)
    def parse_blueprint_json(cls, v):
        return v if isinstance(v, dict) else loads(v)

    @root_validator(skip_on_failure=True)
    def finalize_preview_urls(cls, values):
        # Remove illegal path characters
        full_name = f'{values["series"].name} ({values["series"].year})'
        clean_name = CleanPath.sanitize_name(full_name)

        # Remove prefix words like A/An/The
        sort_name = re_sub(r'^(a|an|the)(\s)', '', clean_name, flags=IGNORECASE)

        # Add base repo URL to all preview filenames
        values['json_'].previews = [
            preview
            if preview.startswith('https://') else
            (f'https://github.com/CollinHeist/TCM-Blueprints-v2/raw'
             + f'/master/blueprints/{sort_name[0].upper()}/{clean_name}/'
             + f'{values["blueprint_number"]}/{preview}')
            for preview in values['json_'].previews
        ]

        return values
