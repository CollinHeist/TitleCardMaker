# :material-plex:{ .plex } Plex

!!! info "Optional Step"

    This step is completely optional, and only those with Plex media
    servers should continue.

1. Toggle the `Enable Plex` checkbox.
2. Enter the _root_ URL of your Plex server (including the port).

    ??? example "Example URL"

        Although your local IP address will obviously be different, this
        IP should be _like_ `http://192.168.0.29:32400/`.

3. Follow [these instructions](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) and copy the
X-Plex-Token value.

    ??? warning "Security Warning"

        Keep this API key private, as it can be used to remotely access
        and modify Plex, and does not automatically expire.

4. Back within TitleCardMaker, paste the X-Plex-Token from Step 3 into
the Token input box.
5. If you use Plex Meta Manager episode overlays, toggle the `Integrate
with Plex Meta Manager` checkbox.
6. Click the `Save Changes` button.

*[Media Server]: Plex, Emby, or Jellyfin
*[Media Servers]: Plex, Emby, or Jellyfin
*[TCM]: TitleCardMaker
*[TMDb]: TheMovieDatabase