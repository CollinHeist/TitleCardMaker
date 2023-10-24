---
title: Connecting to Plex
description: >
    How to connect TitleCardMaker to Plex.
---

# :material-plex:{ .plex } Plex

!!! info "Optional Step"

    This step is completely optional, and only those with Plex media servers
    should continue.

As a Media Server, Plex can serve as an
[Episode Data Source](../../user_guide/settings.md#episode-data-source),
[Image Source](../../user_guide/settings.md#image-source-priority), and
(obviously) as a location where Title Cards are uploaded to.

1. Toggle the `Enable Plex` checkbox.
2. Enter the _root_ URL of your Plex server (including the port).

    ??? example "Example URL"

        Although your local IP address will obviously be different, this IP
        should be _like_ `http://192.168.0.29:32400/`.

3. Follow [these instructions](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) and copy the
X-Plex-Token value.
4. Back within TitleCardMaker, paste the X-Plex-Token from Step 3 into the Token
input box.
5. If you use Plex Meta Manager episode overlays, toggle the `Integrate with
Plex Meta Manager` checkbox.
6. Click the `Save Changes` button.
