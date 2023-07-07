from typing import Any, Optional

from pydantic import Field, root_validator

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
    font_id: Optional[int] = Field(default=None)
    card_type: Optional[str] = Field(default=None)
    hide_season_text: Optional[bool] = Field(default=None)
    hide_episode_text: Optional[bool] = Field(default=None)
    episode_text_format: Optional[str] = Field(default=None)
    template_ids: Optional[list[int]] = Field(default=None)
    translations: Optional[list[Translation]] = Field(default=None)
    season_title_ranges: Optional[list[SeasonTitleRange]] = Field(default=None)
    season_title_values: Optional[list[str]] = Field(default=None)
    extra_keys: Optional[list[str]] = Field(default=None)
    extra_values: Optional[list[Any]] = Field(default=None)

class BlueprintSeries(SeriesBase):
    font_color: Optional[str] = Field(default=None)
    font_title_case: Optional[TitleCase] = Field(default=None)
    font_size: Optional[float] = Field(default=None)
    font_kerning: Optional[float] = Field(default=None)
    font_stroke_width: Optional[float] = Field(default=None)
    font_interline_spacing: Optional[int] = Field(default=None)
    font_vertical_shift: Optional[int] = Field(default=None)
    
class BlueprintEpisode(BlueprintSeries):
    season_text: Optional[str] = Field(default=None)
    episode_text: Optional[str] = Field(default=None)

class BlueprintFont(BlueprintBase):
    name: str
    color: Optional[str] = Field(default=None)
    delete_missing: bool = Field(default=None)
    file: Optional[str] = Field(default=None)
    kerning: float = Field(default=None)
    interline_spacing: int = Field(default=None)
    replacements_in: list[str] = Field(default=None)
    replacements_out: list[str] = Field(default=None)
    size: float = Field(default=None)
    stroke_width: float = Field(default=None)
    title_case: Optional[TitleCase] = Field(default=None)
    vertical_shift: int = Field(default=None)

class BlueprintTemplate(SeriesBase):
    name: str
    filters: list[Condition] = Field(default=[])

"""
Creation classes
"""
class Blueprint(Base):
    series: BlueprintSeries
    episodes: dict[str, BlueprintEpisode] = Field(default={})
    templates: list[BlueprintTemplate] = Field(default=[])
    fonts: list[BlueprintFont] = Field(default=[])

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
    description: list[str] = Field(default=['Descriptive information about this Blueprint'])
    creator: str = Field(default='Your (user)name here')
    preview: str = Field(default='Name of preview file here')

class RemoteBlueprintFont(BlueprintFont):
    file_download_url: Optional[str] = Field(default=None)

class RemoteBlueprint(Blueprint):
    id: int
    description: list[str]
    preview: str
    creator: str
    
class RemoteMasterBlueprint(RemoteBlueprint):
    series_full_name: str