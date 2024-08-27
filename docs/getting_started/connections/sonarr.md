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

1. Under the Sonarr section, click the
<span class="example md-button">Add Connection</span> button.

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

7. The next step is to add the top-level directories for each of your television
libraries to that TitleCardMaker can automatically detect a Series' Library when
[Syncing](../first_sync/sonarr.md) from Sonarr. The paths listed here __must__
be as they appear __within Sonarr__ - not your media server. See the following
examples for reference.

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

For details on setting up this integration, see
[here](../../user_guide/integrations.md#sonarr).
