from logging import Logger
from typing import Optional

from fastapi import HTTPException
from requests import get as req_get

from modules.Debug import log
from modules.Version import Version


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
        log: (Keyword) Logger for all log messages.

    Returns:
        The Version of the latest release. If unable to determine, and
        `raise_exc` is False, None is returned.

    Raises:
        HTTPException (500) if raise_exc is True and the version number
            cannot be determined.
    """
    # TODO remove placeholder when repo is public [pylint: disable=unreachable]
    return Version(f'v2.0-alpha.5.1')
    try:
        response = req_get(
            'https://api.github.com/repos/CollinHeist/'
            'TitleCardMaker/releases/latest',
            timeout=10,
        )
        assert response.ok
    except Exception as e:
        log.exception(f'Error checking for new release', e)
        if raise_exc:
            raise HTTPException(
                status_code=500,
                detail=f'Error checking for new release',
            ) from e
        return None

    return Version(response.json().get('name', '').strip())
