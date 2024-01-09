from typing import Literal, Optional, Union, overload

from app.dependencies import get_preferences
from app.models.episode import Episode
from app.models.series import Library, Series
from app.models.template import Template


@overload
def get_effective_series_template(
        series: Series,
        episode: Optional[Episode] = None,
        library: Optional[Library] = None,
        *,
        as_dict: Literal[True] = False,
    ) -> dict:
    ...

@overload
def get_effective_series_template(
        series: Series,
        episode: Optional[Episode] = None,
        library: Optional[Library] = None,
        *,
        as_dict: Literal[False] = False,
    ) -> Optional[Template]:
    ...

def get_effective_series_template(
        series: Series,
        episode: Optional[Episode] = None,
        library: Optional[Library] = None,
        *,
        as_dict: bool = False
    ) -> Union[dict, Optional[Template]]:
    """
    Get the effective Series Template for the given Series and optional
    Episode. This evaluates all Template conditions.

    Args:
        series: Series whose Templates are being evaluated.
        episode: Episode that can be used in the Template Condition
            evaluation.
        as_dict: Whether to return the dictionary of the given Template.

    Returns:
        The first Template of the given Series whose Conditions are all
        met. None (or an empty dictionary if `as_dict` is True) if no
        Template criteria are satisfied, or no Templates are defined.
    """

    # Evaluate each Series Template
    preferences = get_preferences()
    for template in series.templates:
        if template.meets_filter_criteria(preferences, series, episode, library):
            return template.__dict__ if as_dict else template

    return {} if as_dict else None


def get_effective_episode_template(
        series: Series,
        episode: Episode,
        library: Optional[Library] = None,
    ) -> Optional[Template]:
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
    preferences = get_preferences()
    for template in episode.templates:
        if template.meets_filter_criteria(preferences, series, episode, library):
            return template

    return None


def get_effective_templates(
        series: Series,
        episode: Optional[Episode] = None,
        library: Optional[Library] = None,
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
        return get_effective_series_template(series, episode, library), None

    # Episode defines Templates, return None and Episode Template
    return None, get_effective_episode_template(series, episode, library)


def get_all_effective_templates(
        series: Series,
        episode: Episode,
    ) -> list[tuple[Optional[Template], Optional[Template]]]:
    """
    _summary_

    Args:
        series: _description_
        episode: _description_. Defaults to None.

    Returns:
        _description_
    """

    if not episode.templates:
        return [
            (get_effective_series_template(series, episode, library), None)
            for library in series.libraries
        ]

    return [
        (None, get_effective_episode_template(series, episode, library))
        for library in series.libraries
    ]
