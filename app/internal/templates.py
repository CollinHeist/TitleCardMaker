from typing import Literal, Optional, Union, overload

from sqlalchemy.orm import Session

from app.database.query import get_template
from app.dependencies import get_preferences
from app.models.episode import Episode
from app.models.preferences import Preferences
from app.models.series import Library, Series
from app.models.template import Template


@overload
def get_effective_template(
        obj: Union[Preferences, Series, Episode],
        series: Series,
        episode: Optional[Episode] = None,
        library: Optional[Library] = None,
        *,
        as_dict: Literal[True] = False,
    ) -> dict:
    ...

@overload
def get_effective_template(
        obj: Union[Preferences, Series, Episode],
        series: Series,
        episode: Optional[Episode] = None,
        library: Optional[Library] = None,
        *,
        as_dict: Literal[False] = False,
    ) -> Optional[Template]:
    ...

def get_effective_template(
        obj: Union[Preferences, Series, Episode],
        series: Series,
        episode: Optional[Episode] = None,
        library: Optional[Library] = None,
        *,
        as_dict: bool = False
    ) -> Union[dict, Optional[Template]]:
    """
    Get the effective Template for the given object, evaluated with the
    given Series and optional Episode. This evaluates all Template
    conditions.

    Args:
        obj: Object whose Templates are being evaluated.
        series: Series being used in the Template Condition evaluation.
        episode: Episode that can be used in the Template Condition
            evaluation.
        as_dict: Whether to return the dictionary of the given Template.

    Returns:
        The first Template of the given object whose Conditions are all
        met. None (or an empty dictionary if `as_dict` is True) if no
        Template criteria are satisfied, or no Templates are defined.
    """

    # Object is global Preferences, query for each Template as evaluated
    if isinstance(obj, Preferences) and obj.default_templates:
        db = Session.object_session(series)
        for template_id in obj.default_templates:
            if ((template := get_template(db, template_id, raise_exc=False))
                and template.meets_filter_criteria(obj, series, episode, library)):
                return template.__dict__ if as_dict else template
    # Object is Series or Episode, iterate and evaluate
    elif isinstance(obj, (Series, Episode)):
        preferences = get_preferences()
        for template in obj.templates:
            if template.meets_filter_criteria(preferences, series, episode, library):
                return template.__dict__ if as_dict else template

    return {} if as_dict else None


@overload
def get_effective_templates(
        series: Series,
        episode: Literal[None] = None,
        library: Optional[Library] = None,
    ) -> Union[tuple[Optional[Template], None, None],
               tuple[None, Optional[Template], None]]:
    ...

@overload
def get_effective_templates(
        series: Series,
        episode: Episode = None,
        library: Optional[Library] = None,
    ) -> Union[tuple[Optional[Template], None, None],
               tuple[None, Optional[Template], None],
               tuple[None, None, Optional[Template]]]:
    ...

def get_effective_templates(
        series: Series,
        episode: Optional[Episode] = None,
        library: Optional[Library] = None,
    ) -> Union[tuple[Optional[Template], None, None],
               tuple[None, Optional[Template], None],
               tuple[None, None, Optional[Template]]]:
    """
    Get the effective Global, Series, and Episode Templates for the given
    Series and optional Episode. This evaluates all Template conditions
    and assumes all Series or Episode Templates override global
    Templates, and all Episode Templates override Series Templates.

    Args:
        series: Series whose Templates are being evaluated.
        episode: Episode whose Templates are being evaluated.

    Returns:
        Tuple of the global, Series and Episode Template objects (or
        None). If an Episode is provided AND that Episode has Template
        definitions, then the Series Template is always None, while the
        Episode Template is determined by the Filter criteria. Otherwise
        the Series Template is determined by the Filter critera, and the
        Episode Template is always None.
    """

    # Episode defines Templates, return Episode Template
    if episode and episode.templates:
        return (
            None,
            None,
            get_effective_template(episode, series, episode, library)
        )

    # No Episode OR Episode has no Templates, return Series Template
    if series.templates:
        return (
            None,
            get_effective_template(series, series, episode, library),
            None
        )

    # No Series or Episode Templates, return global Template
    return (
        get_effective_template(get_preferences(), series, episode, library),
        None,
        None,
    )
