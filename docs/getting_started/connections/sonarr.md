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
typically much faster than the other alternatives (Emby, Jellyfin, Plex) and
is _generally_ the recommended option for most users.

## Connecting

1. Toggle the `Enable Sonarr` checkbox.
2. Enter the _root_ URL of your Sonarr server (including the port).

    ??? example "Example URL"

        Although your local IP address will obviously be different, this IP
        should be _like_ `http://192.168.0.29:8989/`.

3. Open the Sonarr WebUI, then open your settings from the left navigation bar.
4. Towards the bottom of the Settings submenu, open `General`.
5. Under the Security subsection, and find and copy the API key - it should be a
32-character long string of numbers and the letters between A and F.

    ??? danger "Security Warning"

        Keep this API key private, as it can be used to remotely access and
        modify Sonarr.

6. Back within TitleCardMaker, paste the API key from Step 5 into the API key
input box.
7. The next step is to add the top-level directories for each of your Television
libraries to that TitleCardMaker can automatically detect a Series' Library when
[Syncing](../first_sync/sonarr.md) from Sonarr. See the following examples for
guidance on how to enter your library paths.

    !!! tip "Quick Setup"

        For most users, simply listing the paths in Sonarr under `Settings` >
        `Media Management` > `Root Folders` and their associated Library names
        will work.

    ??? example "Example Library Paths"

        === "Example 1"

            I have two libraries, called `Anime` and `TV` in my Media Servers
            that are in __separate__ directories. Within Sonarr, the `Anime`
            library is located under `/data/media/anime`, and the `TV` library
            is located under `/data/media/tv`.

            Within TitleCardMaker, this setting should be entered as:

            | Library Name | Path |
            | ---: | :--- |
            | Anime | /data/media/anime |
            | TV | /data/media/tv |

        === "Example 2"

            I have two libraries, called `Anime` and `TV` in my Media Servers
            that are in __separate__ directories. Within Sonarr, the `Anime`
            library is located under `/data/media/anime`, but the `TV` library
            is located under two _separate_ directories, `/data/media/tv_4k` and
            `/data/media/tv_hd`. 

            Within TitleCardMaker, this setting should be entered as:

            | Library Name | Path |
            | ---: | :--- |
            | Anime | /data/media/anime |
            | TV | /data/media/tv_4k |
            | TV | /data/media/tv_hd |

            Notice how each root directory of the TV library needs an entry.

        === "Example 3"

            I have three libraries, called `Anime`, `TV`, and `TV (4K)` in my
            Media Servers that are in __separate__ directories. Within Sonarr,
            the `Anime` library is located under `J:\Anime`, the `TV` library
            under `K:\TV`, and the `TV (4K)` library is under `K:\TV 4K`. 

            Within TitleCardMaker, this setting should be entered as:

            | Library Name | Path |
            | ---: | :--- |
            | Anime | J:\Anime |
            | TV | K:\TV |
            | TV (4K) | K:\TV 4K |

8. After entering all the necessary library paths, click the `Save Changes`
button.

## Webhook Integration

!!! note "Tautulli Alternative"

    Tautulli Notification Agents are a much better alternative to Sonarr
    Webhooks _if_ you are using Plex __and__ Tautulli in your setup.

    The process of setting this up Tautulli is covered [here](tautulli.md). It
    is not recommended (or necessary) to enable both integrations.

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
