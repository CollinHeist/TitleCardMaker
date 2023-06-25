from typing import Optional

from app.schemas.episode import Episode
from app.schemas.font import NamedFont
from app.schemas.series import Series

from modules.Debug import log


def get_effective_fonts(
        series: Series,
        episode: Optional[Episode] = None
    ) -> tuple[Optional[NamedFont], Optional[NamedFont]]:
    """
    Get the effective Series and Episode Fonts for the given Series and
    optional Episode. This evaluates the Episode Font overrides Series
    Font.

    Args:
        series: Series whose Font is being evaluated.
        episode: Episode whose Font is being evaluated.

    Returns:
        Tuple of the Series and Episode Font objects (or None). If an
        Episode is provided AND that Episode has a Font definition, then
        the Series Font is always None, and the Episode Font is
        returned. Otherwise the Series Font is returned, and the Episode
        Font is always None.
    """

    # No Episode OR Episode has no Font, return Series Font and None
    if episode is None or not episode.font:
        return series.font, None

    # Episode defines Font, return None and Episode Font
    return None, episode.font