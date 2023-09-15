from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response
from requests import get
from requests.exceptions import Timeout

from app.dependencies import get_preferences
from app.internal.auth import get_current_user
from app.models.preferences import Preferences


# Create sub router for all /proxy API requests
proxy_router = APIRouter(
    prefix='/proxy',
    tags=['Proxy'],
    dependencies=[Depends(get_current_user)],
)


@proxy_router.get(
        '/plex',
        responses = {200: {'content': {'image/jpeg': {}}}},
        response_class=Response
    )
def redirect_plex_url(
        url: str = Query(...),
        interface_id: int = Query(default=0),
        preferences: Preferences = Depends(get_preferences),
    ) -> Response:
    """
    Get the content at the given URL for the Plex server. For example if
    `url` is `/library/metadata/123/poster`, then the contents of
    `http://{plex_url}:{plex_port}/library/metadata/123/poster?X-Plex-Token={plex_token}`
    are returned. This obfuscates the actual endpoint and server token
    from the API. The actual contents (bytes) of the image are returned.

    - url: Plex-based URL to get the content of.
    - interface_id: ID of the Plex Interface to redirect to.
    """

    redirected_url = (
        f'{preferences.plex_args[interface_id]["url"][:-1]}{url}?X-Plex-Token='
        f'{preferences.plex_args[interface_id]["token"]}'
    )

    return Response(content=get(redirected_url, timeout=10).content)


@proxy_router.get(
        '/sonarr',
        responses = {200: {'content': {'image/jpeg': {}}}},
        response_class=Response
    )
def redirect_sonarr_url(
        url: str = Query(...),
        interface_id: int = Query(default=0),
        SonarrAuth: str = Cookie(default=''),
        preferences: Preferences = Depends(get_preferences),
    ) -> Response:
    """
    Get the content at the given URL for the Sonarr server. For example
    if `url` is `/MediaCoverProxy/abcdef/98765.jpg`, then the contents of
    `http://{sonarr_url}:{sonarr_port}/MediaCoverProxy/abcdef/98765.jpg`
    are returned. This obfuscates the actual endpoint and server token
    from the API. The actual contents (bytes) of the image are returned.
    This uses the client's `SonarrAuth` cookies in the request.

    - url: Sonarr-based URL to get the content of.
    - interface_id: ID of the Plex Interface to redirect to.
    """

    base_url = preferences.sonarr_args[interface_id]["url"]
    redirected_url = f'{base_url.scheme}://{base_url.host}:{base_url.port}{url}'

    # Query for content, ensure the local `SonarrAuth` cookies are
    # utilized in the request
    try:
        content = get(
            redirected_url,
            cookies={'SonarrAuth': SonarrAuth},
            timeout=5,
        ).content
    except Timeout as exc:
        raise HTTPException(
            status_code=400,
            detail=f'Sonarr redirect timed out'
        ) from exc

    # Return Response of this content
    return Response(content)
