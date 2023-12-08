---
title: Connecting to Sonarr
description: >
    How to connect TitleCardMaker to Sonarr and enable the new-Episode Webhook.
tags:
    - Tutorial
    - Sonarr
---

# Sonarr

!!! info "Optional Step"

    This step is completely optional, and only those with Sonarr servers should
    continue.

Although Sonarr can only serve as an
[Episode Data Source](../../user_guide/settings.md#episode-data-source), it is
typically much faster than the other alternatives (especially Emby, Jellyfin, or
Plex) and is generally the recommended option for most users.

## Connecting

1. Click the <span class="example md-button">Add Connection</span> button to
create a blank Connection.

2. Give this Connection some descriptive name - e.g. `Sonarr 4K` - and enter the
_root_ URL to your Sonarr server __including the port__.

    ??? example "Example URL"

        Although your local IP address will obviously be different, this IP
        should be _like_ `http://192.168.0.29:8989/`.

3. Open the Sonarr WebUI, then open your settings from the left navigation bar.

4. Towards the bottom of the Settings sub-menu, open `General`.

5. Under the Security subsection, and find and copy the API key - it should be a
32-character long string of numbers and the letters between A and F.

    ??? danger "Security Warning"

        Keep this API key private, as it can be used to remotely access and
        modify Sonarr.

6. Back within TitleCardMaker, paste the API key from Step 5 into the API key
input box and then click <span class="example md-button">Create</span>. TCM will
reload the page.

7. The next step is to add the top-level directories for each of your Television
libraries to that TitleCardMaker can automatically detect a Series' Library when
[Syncing](../first_sync/sonarr.md) from Sonarr. The paths listed here __must__
be as they appear __within Sonarr__ - not Emby, Jellyfin, or Plex. See the
following examples for help.

    !!! tip "Quick Setup"

        For most users, simply listing the paths, library names, and associated
        servers for the folders in Sonarr under
        `Settings` > `Media Management` > `Root Folders` is sufficient.

    ??? example "Example Library Paths"

        === "Example 1"

            Within Plex, I have two libraries called `Anime` and `TV` located at
            `/data/media/Anime` and `/data/media/TV` respectively. My Library
            Paths setting should look like:

            | Media Server | Library Name | Path               |
            | :----------- | :----------- | :----------------- |
            | Plex         | Anime        | /data/media/Anime/ |
            | Plex         | TV           | /data/media/TV/    |

        === "Example 2"

            Within Jellyfin, I have four libraries called `Anime`, `Anime 4K`,
            `TV Shows`, and `TV Shows 4K` - they are located at
            `/data/media/anime`, `/data/media/anime 4k/`, `/data/media/tv/`, and
            `/data/media/tv 4k` respectively. The Library Paths setting should
            look like:

            | Media Server | Library Name | Path                  |
            | :----------- | :----------- | :-------------------- |
            | Jellyfin     | Anime        | /data/media/anime/    |
            | Jellyfin     | Anime 4K     | /data/media/anime 4k/ |
            | Jellyfin     | TV           | /data/media/TV/       |
            | Jellyfin     | TV 4K        | /data/media/TV 4k/    |

        === "Example 3"

            Within Emby I have two libraries: `TV`, and `Reality TV` located at
            `C:\TV` and `K:\Reality TV`; within Plex there are two libraries:
            `Anime` and `Reality TV` located at `C:\Anime` and `K:\Reality TV`
            (the same directory as within Emby). The Library Paths setting
            should look like:

            | Media Server | Library Name | Path          |
            | :----------- | :----------- | :------------ |
            | Emby         | TV           | C:\TV         |
            | Emby         | Reality TV   | K:\Reality TV |
            | Plex         | Anime        | C:\Anime      |
            | Plex         | Reality TV   | K:\Reality TV |

8. After entering all the necessary library paths, click
<span class="example md-button">Save Changes</span>.

## Webhook Integration

!!! note "Tautulli Alternative"

    Tautulli Notification Agents are a much better alternative to Sonarr
    Webhooks _if_ you are using Plex __and__ Tautulli in your setup.

    The process of setting this up Tautulli is covered [here](tautulli.md). It
    is not recommended (or necessary) to enable both integrations.

!!! warning "Sonarr v4 Required"

    The Webhook utilized by TCM was reworked in Sonarr v4; meaning this is
    required for the integration.

If you'd like to create Title Cards for Episodes faster than TCM typically does
via the [adjustable scheduler](../scheduler.md), you can enable a Sonarr Webhook
to trigger card creation for Episodes as they are grabbed by Sonarr. How to
enable this functionality is described below.

1. From the Sonarr WebUI, navigate to :fontawesome-solid-gears: `Settings`, then
`Connect`.

2. Click the plus button to create a new connection.

3. Scroll to and click the last option, `Webhook`.

4. Change the name to something like _TitleCardMaker_, and then select __only__
the `On Import` and `On Upgrade` Notification Triggers.

5. Leave the Tags field blank (unless you'd like to filter by tag).

6. For the URL, enter your TCM WebUI URL (including the port) with
`/api/cards/sonarr` added to the end.

    ??? example "Example URL"

        If I access the TCM web interface at `http://192.168.0.19:4242`, then
        in this URL field I would enter
        `http://192.168.0.19:4242/api/cards/sonarr`.

7. Leave the method as `POST`, and the Username and Password fields blank.

8. Hit `Save`, and in your TCM logs you should get some messages like this:

    ```
    [DEBUG] [...] Starting POST "/api/cards/sonarr"
    [INFO] [...] Cannot find Series for Test Title (0)
    [DEBUG] [...] Finished in xxx.xms
    ```

!!! success "Success"

    With the Webhook created, Sonarr will now send a signal to TitleCardMaker
    whenever an Episode is imported or upgraded. This typically results in
    Title Cards being created for Episodes within _seconds_ of them being added
    to your media server.
