from requests import get as req_get
from typing import Optional

from fastapi import HTTPException

from modules.Debug import log

def get_latest_version(raise_exc: bool = True) -> Optional[str]:
    """
    Get the latest version of TitleCardMaker available.

    Args:
        raise_exc: Whether to raise an HTTPException if getting the
            latest version fails for any reason.

    Returns:
        The string version number of the latest release. If unable to
        determine, and raise_exc is False, then None is returned.

    Raises:
        HTTPException (500) if raise_exc is True and the version number
            cannot be determined.
    """

    try:
        response = req_get(
            'https://api.github.com/repos/CollinHeist/'
            'TitleCardMaker/releases/latest'
        )
        assert response.ok
    except Exception as e:
        log.exception(f'Error checking for new release', e)
        if raise_exc:
            raise HTTPException(
                status_code=500,
                detail=f'Error checking for new release',
            )
        return None
    
    return response.json().get('name', '').strip()