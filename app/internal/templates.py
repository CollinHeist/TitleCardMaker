from typing import Any, Optional

from app.dependencies import get_preferences
from app.schemas.episode import Episode
from app.schemas.series import Series, Template

from modules.Debug import log


def get_effective_series_template(
        series: Series,
        episode: Optional[Episode] = None, *,
        as_dict: bool = False) -> Optional[Template]:
    """
    Get the effective Series Template for the given Series and optional
    Episode. This evaluates all Template conditions.

    Args:
        series: Series whose Templates are being evaluated.
        episode: Episode that can be used in the Template Condition
            evaluation.
        as_dict: Whether to return the dictionary of the given Template.
            If None would be returned, then an empty dict is returned.

    Returns:
        The first Template of the given Series whose Conditions are all
        met. None (or an empty dictionary if as_dict is True) if no
        Template criteria are satisfied, or no Templates are defined.
    """

    # Evaluate each Series Template
    preferences = get_preferences()
    for template in series.templates:
        if template.meets_filter_criteria(preferences, series, episode):
            return template.__dict__ if as_dict else template
        
    return {} if as_dict else None


def get_effective_episode_template(
        series: Series,
        episode: Episode) -> Optional[Template]:
    """
    Get the effective Episode Template for the given Series and Episode.
    This evaluates all Template conditions.

    Args:
        series: Series used in the Template Condition evaluation.
        episode: Episode whose Templates are being evluated.

    Returns:
        The first Template of the given SEpisodeeries whose Conditions
        are all met. None if no Template criteria are satisfied, or no
        Templates are defined.
    """

    # Evaluate each Episode Template
    for template in episode.templates:
        if template.meets_filter_criteria(series, episode):
            return template
        
    return None


def get_effective_templates(
        series: Series,
        episode: Optional[Episode] = None
        ) -> tuple[Optional[Template], Optional[Template]]:
    """
    Get the effective Series and Episode Templates for the given Series
    and optional Episode. This evaluates all Template conditions and
    assumes all Episode Templates overrides Series Templates.

    Args:
        series: Series whose Templates are being evaluated.
        episode: Episode whose Templates are being evaluated.

    Returns:
        Tuple of the Series and Episode Template objects (or None). If
        an Episode is provided AND that Episode has Template
        definitions, then the Series Template is always None, while the
        Episode Template is determined by the Filter criteria. Otherwise
        the Series Template is determined by the Filter critera, and the
        Episode Template is always None.
    """

    # No Episode OR Episode has no Templates, return Series Template and None
    if episode is None or not episode.templates:
        return get_effective_series_template(series, episode), None

    # Episode defines Templates, return None and Episode Template
    return None, get_effective_episode_template(series, episode)