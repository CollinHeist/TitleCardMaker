from datetime import datetime, timedelta
from logging import Logger
from typing import Optional

from fastapi import HTTPException
from requests import get as req_get

from app.models.preferences import Preferences
from app.schemas.card import LocalCardType, RemoteCardType
from modules.Debug import log
from modules.Version import Version


# URL for user card types
USER_CARD_TYPE_URL = (
    'https://raw.githubusercontent.com/CollinHeist/TitleCardMaker-CardTypes/'
    'hash-validation/cards.json'
)


def get_latest_version(
        raise_exc: bool = True,
        *,
        log: Logger = log,
    ) -> Optional[Version]:
    """
    Get the latest version of TitleCardMaker available.

    Args:
        raise_exc: Whether to raise an HTTPException if getting the
            latest version fails for any reason.
        log: Logger for all log messages.

    Returns:
        The Version of the latest release. If unable to determine, and
        `raise_exc` is False, None is returned.

    Raises:
        HTTPException (500): `raise_exc` is True and the version number
            cannot be determined.
    """

    # TODO remove placeholder when repo is public [pylint: disable=unreachable]
    return Version(f'v2.0-alpha.10.1')

    try:
        response = req_get(
            'https://api.github.com/repos/CollinHeist/'
            'TitleCardMaker/releases/latest',
            timeout=10,
        )
        assert response.ok
    except Exception as e:
        log.exception(f'Error checking for new release')
        if raise_exc:
            raise HTTPException(
                status_code=500,
                detail=f'Error checking for new release',
            ) from e
        return None

    return Version(response.json().get('name', '').strip())


def get_local_cards(preferences: Preferences) -> list[LocalCardType]:
    """
    Get the list of availably locally specified card types.

    Args:
        preferences: Global preferences.

    Returns:
        List of LocalCardType objects.
    """

    return [
        card_class.API_DETAILS
        for card_class in preferences.local_card_types.values()
    ]


_cache = {'content': [], 'expires': datetime.now()}
def get_remote_cards(*, log: Logger = log) -> list[RemoteCardType]:
    """
    Get the list of available RemoteCardTypes. This will cache results
    for 30 minutes. If the available data is older than 12 hours, the
    GitHub is re-queried.

    Args:
        log: Logger for all log messages.

    Returns:
        List of RemoteCardTypes.
    """

    # If the cached content has expired, request and update cache
    if _cache['expires'] <= datetime.now():
        log.debug(f'Refreshing cached RemoteCardTypes..')
        response = req_get(USER_CARD_TYPE_URL, timeout=30).json()
        _cache['content'] = response
        _cache['expires'] = datetime.now() + timedelta(hours=12)
    # Cache has not expired, use cached content
    else:
        response = _cache['content']

    return [RemoteCardType(**card) for card in response]


def get_remote_card_hash(identifier: str, *, log: Logger = log) ->Optional[str]:
    """
    Get the MD5 hash of the Card with the given identifier.

    Args:
        identifier: CardType identifier.
        log: Logger for all log messages.

    Returns:
        MD5 hash of the card with the given identifier. None if one is
        not available (e.g. unknown `identifier`).
    """

    for card_type in get_remote_cards(log=log):
        if card_type.identifier == identifier:
            return card_type.hash

    return None
