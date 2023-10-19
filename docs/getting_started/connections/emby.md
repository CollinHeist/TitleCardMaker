# :material-emby:{.emby} Emby

!!! info "Optional Step"

    This step is completely optional, and only those with Emby media servers
    should continue.

1. Toggle the `Enable Emby` checkbox.
2. Enter the _root_ URL to your Emby server (including the port).

    ??? example "Example URL"

        Although your local IP address will obviously be different, this IP
        should be _like_ `http://192.168.0.29:8096/`.

3. Open the Emby WebUI, and open your server Dashboard by clicking the gear icon
in the top right.
4. Scroll to the bottom of the left navigation bar, open `Api Keys` under
`Advanced`.
5. Click `+ New Api Key`, and enter the name `TitleCardMaker`.
6. Copy the created key, it should be a 32-character long string of numbers and
the letters between A and F.
7. Back within TitleCardMaker, paste the API key from Step 6 into the API key
input box and then click the `Save Changes` button.

    !!! tip "Tip"

        If your username does not appear, reload the page.

8. Select the username of the account you would like Episode watch-statuses to
be queried from.
9. Click the `Save Changes` button.