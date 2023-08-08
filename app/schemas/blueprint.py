# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from datetime import datetime
from typing import Any, Optional

from pydantic import root_validator

from app.schemas.base import Base
from app.schemas.font import TitleCase
from app.schemas.series import Condition, SeasonTitleRange, Translation

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

class SeriesBase(BlueprintBase):
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

class BlueprintSeries(SeriesBase):
    template_ids: Optional[list[int]] = None
    font_color: Optional[str] = None
    font_title_case: Optional[TitleCase] = None
    font_size: Optional[float] = None
    font_kerning: Optional[float] = None
    font_stroke_width: Optional[float] = None
    font_interline_spacing: Optional[int] = None
    font_vertical_shift: Optional[int] = None

class BlueprintEpisode(BlueprintSeries):
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
    replacements_in: list[str] = None
    replacements_out: list[str] = None
    size: float = None
    stroke_width: float = None
    title_case: Optional[TitleCase] = None
    vertical_shift: int = None

class BlueprintTemplate(SeriesBase):
    name: str
    filters: list[Condition] = []

"""
Creation classes
"""
class Blueprint(Base):
    series: BlueprintSeries
    episodes: dict[str, BlueprintEpisode] = {}
    templates: list[BlueprintTemplate] = []
    fonts: list[BlueprintFont] = []

"""
Update classes
"""

"""
Return classes
"""
class DownloadableFile(Base):
    url: str
    filename: str

class BlankBlueprint(Blueprint):
    preview: str = 'Name of preview file here'

class RemoteBlueprintFont(BlueprintFont):
    file_download_url: Optional[str] = None

class RemoteBlueprint(Blueprint):
    id: int
    description: list[str]
    preview: str
    creator: str
    created: datetime

class RemoteMasterBlueprint(RemoteBlueprint):
    series_full_name: str
