---
title: Connecting to Plex
description: >
    How to connect TitleCardMaker to Plex.
tags:
    - Tutorial
    - Plex
---

# :material-plex:{ .plex } Plex

!!! info "Optional Step"

    This step is completely optional, and only those with Plex media servers
    should continue.

As a Media Server, Plex can serve as an
[Episode Data Source](../../user_guide/settings.md#episode-data-source),
[Image Source](../../user_guide/settings.md#image-source-priority), and as a
location where Title Cards are uploaded to.

1. Under the Plex section, click the
<span class="example md-button">Add Connection</span> button.

2. Give this Connection some descriptive name - e.g. `Plex` - and enter the
_root_ URL to your Plex server __including the port__.

    ??? example "Example URL"

        Although your local IP address will obviously be different, this IP
        should be _like_ `http://192.168.0.29:32400/`.

3. Follow [these instructions](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) and copy the
X-Plex-Token value.

4. Back within TitleCardMaker, paste the X-Plex-Token from Step 3 into the Token
input box.

5. If you use Kometa (formerly PMM) episode overlays, toggle the `Integrate with
Kometa` checkbox.

6. Click <span class="example md-button">Create</span>. TCM will reload the
page.

7. If you would like to utilize Webhooks or Tautulli to quickly create and load
Cards into Plex for new or watched content, see
[here](../../user_guide/integrations.md).

The above process can be repeated for as many Plex Media Servers as you have. I
do recommend specifying a _unique_ name for each Connection so they can be
easily distinguished within the UI.
