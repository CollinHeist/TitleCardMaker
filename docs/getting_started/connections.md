# Configuring Connections
TitleCardMaker can communicate directly with Emby, Jellyfin, Plex,
Sonarr, Tautulli, and TMDb to get episode data, download images, add
translations, and load Title Cards.

Although not required to run TCM, enabling whichever connections that
are applicable to your setup will improve TCM's operation.

!!! warning "Using Multiple Media Servers"

    Although using multiple media servers together - e.g. any two of
    Emby, Jellyfin, and Plex - is _possible_, using [watch-specific
    styles]() will not integrate well if the two Servers have different
    watch statuses.

## Emby

1. Toggle the `Enable Emby` checkbox.
2. Enter the _root_ URL to your Emby server (including the port).

    ??? example "Example URL"

        Although your local IP address will obviously be different, this
        IP should be _like_ `http://192.168.0.29:8096/`.

3. Open the Emby WebUI, and open your server Dashboard by clicking the
gear icon in the top right.
4. Scroll to the bottom of the left navigation bar, open `Api Keys`
under `Advanced`.
5. Click `+ New Api Key`, and enter the name `TitleCardMaker`.
6. Copy the created key, it should be a 32-character long string of
numbers and the letters between A and F.
7. Back within TitleCardMaker, paste the API key from Step 6 into the
API key input box and then click the `Save Changes` button.

    !!! tip "Tip"

        If your username does not appear, reload the page.

8. Select the username of the account you would like Episode watch-
statuses to be queried from.
9. Click the `Save Changes` button.

## Jellyfin

1. Toggle the `Enable Jellyfin` checkbox.
2. Enter the _root_ URL to your Jellyfin server (including the port).

    ??? example "Example URL"

        Although your local IP address will obviously be different, this
        IP should be _like_ `http://192.168.0.29:8096/`.

3. Open the Jellyfin WebUI, and open your server settings by clicking
the hamburger icon in the top left.
4. Scroll to the bottom, click Dashboard, and then open `Api Keys` under
`Advanced`.
5. Click the `+` icon, and enter the name `TitleCardMaker`.
6. Copy the created key, it should be a 32-character long string of
numbers and the letters between A and F.
7. Back within TitleCardMaker, paste the API key from Step 6 into the
API key input box and then click the `Save Changes` button.

    !!! tip "Tip"

        If your username does not appear, reload the page.

8. Select the username of the account you would like Episode watch-
statuses to be queried from.
9. Click the `Save Changes` button.

## Plex

1. Toggle the `Enable Plex` checkbox.
2. Enter the _root_ URL of your Plex server (including the port).

    ??? example "Example URL"

        Although your local IP address will obviously be different, this
        IP should be _like_ `http://192.168.0.29:32400/`.

3. Follow [these instructions](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) and copy the
X-Plex-Token value.
4. Back within TitleCardMaker, paste the X-Plex-Token from Step 3 into
the Token input box.
5. If you use Plex Meta Manager episode overlays, toggle the `Integrate
with Plex Meta Manager` checkbox.
6. Click the `Save Changes` button.

## Sonarr

1. ...

*[TCM]: TitleCardMaker
*[TMDb]: TheMovieDatabase