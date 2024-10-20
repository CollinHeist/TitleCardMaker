from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response
from niquests import get
from niquests.exceptions import Timeout
from sqlalchemy.orm import Session

from app.database.query import get_connection
from app.dependencies import get_database
from app.internal.auth import get_current_user
from modules.Debug import log # noqa: F401


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
        interface_id: int = Query(...),
        db: Session = Depends(get_database),
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

    # Get Connection with this ID, raise 404 if DNE
    connection = get_connection(db, interface_id, raise_exc=True)

    # Raise 422 if the Connection doesn't have a defined URL
    if not connection.decrypted_url:
        raise HTTPException(
            status_code=422,
            detail=f'Connection[{interface_id}] does not have a defined URL'
        )

    return Response(content=get(
        f'{connection.decrypted_url.removesuffix("/")}/'
        f'{url.removeprefix("/")}?X-Plex-Token={connection.decrypted_api_key}',
        timeout=10,
    ).content)


@proxy_router.get(
    '/sonarr',
    responses = {200: {'content': {'image/jpeg': {}}}},
    response_class=Response
)
def redirect_sonarr_url(
        url: str = Query(...),
        interface_id: int = Query(...),
        SonarrAuth: str = Cookie(default=''),
        db: Session = Depends(get_database),
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

    # Get Connection with this ID, raise 404 if DNE
    connection = get_connection(db, interface_id, raise_exc=True)

    # Raise 422 if the Connection doesn't have a defined URL
    if not connection.decrypted_url:
        raise HTTPException(
            status_code=422,
            detail=f'Connection[{interface_id}] does not have a defined URL'
        )

    # Remove /api/ endpoint from URL if present; do not end in /
    if '/api' in connection.decrypted_url:
        server_url = connection.decrypted_url.split('/api')[0]
    elif connection.decrypted_url.endswith('/'):
        server_url = connection.decrypted_url[:-1]
    else:
        server_url = connection.decrypted_url

    # Start redirect URL in /
    url = url if url.startswith('/') else f'/{url}'
    redirected_url = f'{server_url}{url}'

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
