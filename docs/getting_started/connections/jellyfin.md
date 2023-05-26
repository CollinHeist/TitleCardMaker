# :simple-jellyfin: Jellyfin

!!! info "Optional Step"

    This step is completely optional, and only those with Jellyfin media
    servers should continue.

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

8. Select the username of the account you would like Episode
watch-statuses to be queried from.
9. Click the `Save Changes` button.

*[Media Server]: Plex, Emby, or Jellyfin
*[Media Servers]: Plex, Emby, or Jellyfin
*[TCM]: TitleCardMaker
*[TMDb]: TheMovieDatabase