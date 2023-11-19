---
title: Connections
description: >
    Add connections to external services like Plex, Sonarr, Tautulli, or TMDb.
tags:
    - Authentication
    - Emby
    - Jellyfin
    - Plex
    - Sonarr
    - Tautulli
    - TMDb
---

# Connections

!!! warning "Under Construction"

    This documentation is actively being developed.

The Connections page is where all _external_ connections are defined. Currently
this is the following:

- [Authentication](#authentication)
- [Emby](#emby)
- [Jellyfin](#jellyfin)
- [Plex](#plex)
- [Sonarr](#sonarr)
- [Tautulli](#tautulli_1)
- [TheMovieDatabase](#themoviedatabase)

Each Connection is described in greater detail below.

## Authentication

If you expose your instance of TCM _outside_ our LAN (through a reverse proxy
or some other means), it is recommended to enable Authentication so that a
username and password are required to access TCM.

Once authorized, the OAuth2 access token for your login is stored in your
browser's local storage, so accessing the interface from another browser will
require re-authentication. Tokens expire after two weeks.

!!! tip "API Request"

    All[^1] API requests _also_ require authorization (if enabled). If accessing
    the API [from the UI](../development/api.md), then the locally stored
    OAuth2 session tokens _should_ be applied, but if not you can click
    `Authorize` in the top right of the API page and enter your credentials.

### First Time Setup

When first enabling Authentication by clicking the `Require Authentication`
checkbox, a temporary username and password will be created. These are
printed in the logs, but default to `admin` and `password`.

### Changing Credentials

After authentication is enabled, returning to the Connections page will show
your current username and an empty password field. Simply type in your desired
username and password, then hit `Save Changes` and TCM will modify your
credentials - prompting a new login.

### Disabling Authentication

Authentication can be disabled at any point by unchecking the `Require
Authentication` checkbox.

### Forgotten Login

If you've forgotten your login credentials, follow the following steps to
disable authentication.

1. Define the `TCM_DISABLE_AUTH` environment variable as `TRUE`.

    === ":material-linux: Linux"

        ```bash
        export TCM_DISABLE_AUTH=TRUE
        ```

    === ":material-apple: MacOS"

        ```bash
        TCM_DISABLE_AUTH=TRUE
        ```

    === ":material-powershell: Windows (Powershell)"

        ```bash
        $env:TCM_DISABLE_AUTH = "TRUE"
        ```

    === ":material-microsoft-windows: Windows (Non-Powershell)"

        ```bash
        set TCM_DISABLE_AUTH="TRUE"
        ```

2. If you're using Docker, pass this environment variable into the container
with `-e` (or in your Docker Compose file); if you're not using Docker then
nothing else is necessary. Relaunch TCM.

3. Navigate to the Connections page (`/connections`), re-enable
Authentication - TCM will then create a new User with the default
username and password as `admin` and `password`.

4. Login, then change your credentials as desired.

5. Close TCM and either define `TCM_DISABLE_AUTH` as something other than
`TRUE`, or remove the specification altogether. Re-build/launch TCM.

6. Get a password manager!

[^1]: All API endpoint require authorization _except_ the Tautulli and Sonarr
integrations, as these services are not capable of authenticating themselves.

## Adding a Connection

For each Connection type, clicking the
<span class="example md-button">Add Connection</span> button will create a blank
form which you can enter all details into. After you have finished entering the
info, click <span class="example md-button">Create</span> and TCM will refresh
the page.

Additional settings can be entered _after_ creation. Open the newly created
Connection, enter those details, and click
<span class="example md-button">Save Changes</span>

---

## :material-emby:{.emby} Emby

As a Media Server, Emby can serve as an
[Episode Data Source](./settings.md#episode-data-source),
[Image Source](./settings.md#image-source-priority), and as a location where
Title Cards are uploaded to.

TCM can communicate with any number of Emby Media Servers, although if you plan
to use
[watch-status styling](./settings.md#watched-and-unwatched-episode-styles), make
sure you read and enable the global
[multi library filename support](./settings.md#multi-library-filename-support)
setting first.

### Connection Name

The name of the Connection as it appears within the UI. This is purely
aesthetic.

### URL

The _root_ URL to your Emby server, including the port.

### API Key

API key to authenticate communication. The process of creating one within
Emby is covered
[Getting Started](../getting_started/connections/emby.md).

### Username

Username of the user to query Episode watched statuses from.

### SSL

Whether to connect with HTTPS instead of HTTP.

### Filesize Limit

The maximum file size of Title Cards to upload to Emby. Title Cards larger than
this will be compressed[^1].

Changing this setting __does not__ retroactively affect created or uploaded
Title Cards.

This can be entered as `{digit} {unit}` - e.g. `4 Megabytes` - where the
acceptable units are `Bytes`, `Kilobytes`, and `Megabytes`.

---

## :simple-jellyfin:{ .jellyfin } Jellyfin

As a Media Server, Jellyfin can serve as an
[Episode Data Source](./settings.md#episode-data-source),
[Image Source](./settings.md#image-source-priority), and as a location where
Title Cards are uploaded to.

TCM can communicate with any number of Jellyfin Media Servers, although if you
plan to use
[watch-status styling](./settings.md#watched-and-unwatched-episode-styles), make
sure you read and enable the global
[multi library filename
support](./settings.md#multi-library-filename-support) setting first.

### Connection Name

The name of the Connection as it appears within the UI. This is purely
aesthetic.

### URL

The _root_ URL to your Jellyfin server, including the port.

### API Key

API key to authenticate communication. The process of creating one within
Jellyfin is covered in
[Getting Started](../getting_started/connections/jellyfin.md).

### Username

Username of the user to query Episode watched statuses from.

### SSL

Whether to connect with HTTPS instead of HTTP.

### Filesize Limit

The maximum file size of Title Cards to upload to Jellyfin. Title Cards larger
than this will be compressed[^1].

Changing this setting __does not__ retroactively affect created or uploaded
Title Cards.

This can be entered as `{digit} {unit}` - e.g. `4 Megabytes` - where the
acceptable units are `Bytes`, `Kilobytes`, and `Megabytes`.

---

## :material-plex:{ .plex } Plex

As a Media Server, Plex can serve as an
[Episode Data Source](./settings.md#episode-data-source),
[Image Source](./settings.md#image-source-priority), and as a location where
Title Cards are uploaded to.

TCM can communicate with any number of Plex Media Servers, although if you plan
to use
[watch-status styling](./settings.md#watched-and-unwatched-episode-styles), make
sure you read and enable the global
[multi library filename
support](./settings.md#multi-library-filename-support) setting first.

### Connection Name

The name of the Connection as it appears within the UI. This is purely
aesthetic.

### URL

The _root_ URL to your Plex server, including the port.

### Token

Token to authenticate communication. The process of obtaining your Plex Token
is covered in
[Getting Started](../getting_started/connections/plex.md).

### SSL

Whether to connect with HTTPS instead of HTTP.

### PMM Integration

Whether to remove the `Overlay` label after uploading Title Cards. This also
prevents TCM from grabbing Source Images with overlays applied.

Only check this box if you use (or have used)
[Plex Meta Manager](https://github.com/meisnate12/Plex-Meta-Manager) Episode
overlays.

### Filesize Limit

The maximum file size of Title Cards to upload to Jellyfin. Title Cards larger
than this will be compressed[^1].

Changing this setting __does not__ retroactively affect created or uploaded
Title Cards.

This can be entered as `{digit} {unit}` - e.g. `4 Megabytes` - where the
acceptable units are `Bytes`, `Kilobytes`, and `Megabytes`.

### Tautulli

The Tautulli agent is covered [here](#tautulli_1).

---

## ![Sonarr Logo](../assets/sonarr.png){.no-lightbox} Sonarr

Although Sonarr can only serve as an
[Episode Data Source](./settings.md#episode-data-source), it is typically much
faster than the other alternatives (Emby, Jellyfin, Plex) and is generally the
recommended option for most users.

In addition to this, Sonarr can act as a [Tautulli](#tautulli_1) alternative which
works for non-Plex Media Servers and triggers immediate Title Card creation
when new Episodes are added - settings this up is detailed
[here](../getting_started/connections/sonarr.md#webhook-integration).

### Connection Name

The name of the Connection as it appears within the UI. This is purely
aesthetic.

### URL

The _root_ URL to your Sonarr server, including the port.

### API Key

API key to authenticate communication. The process of getting one from Sonarr is
covered in [Getting Started](../getting_started/connections/sonarr.md).

### SSL

Whether to connect with HTTPS instead of HTTP.

### Downloaded Episode Toggle

Whether to only get Episode data for Episodes which are downloaded. This is only
applicable if Sonarr is the
[Episode Data Source](./settings.md#episode-data-source).

If _unchecked_, and Sonarr is the specified Episode Data Source, then TCM will
grab Episode data for __all__ Episodes within Sonarr, typically resulting in
Title Cards for Episodes which you do not personally have.

### Library Paths

If [Syncing](./sync.md) from Sonarr, then this setting is critical to ensure
that TCM is able to correctly auto-assign libraries to Series. If you are not
Syncing from Sonarr, then you can leave this blank.

Each set of inputs corresponds to a single Library which TCM can assign to. This
means you should generally have one entry for each library across all your
servers. This setting __requires__ that your libraries are in separate
directories (at least within the same Media Server).

!!! tip "Paths"

    All paths should be the path __within Sonarr__ - so users with their Sonarr
    server inside a Docker container need to specify the paths that appear
    within the container, not your Media Server.
    
See the examples for details.

??? example "Example Library Paths"

    === "Example 1"

        Within Plex, I have two libraries called `Anime` and `TV` located at
        `/data/media/Anime` and `/data/media/TV` respectively. My Library Paths
        setting should look like:

        | Media Server | Library Name | Path               |
        | :----------- | :----------- | :----------------- |
        | Plex         | Anime        | /data/media/Anime/ |
        | Plex         | TV           | /data/media/TV/    |

    === "Example 2"

        Within Jellyfin, I have three libraries called `Anime`, `Anime 4K`,
        `TV Shows`, and `TV Shows 4K` - they are located at `/data/media/anime`,
        `/data/media/anime 4k/`, `/data/media/tv/`, and `/data/media/tv 4k`
        respectively. The Library Paths setting should look like:

        | Media Server | Library Name | Path                  |
        | :----------- | :----------- | :-------------------- |
        | Jellyfin     | Anime        | /data/media/anime/    |
        | Jellyfin     | Anime 4K     | /data/media/anime 4k/ |
        | Jellyfin     | TV           | /data/media/TV/       |
        | Jellyfin     | TV 4K        | /data/media/TV 4k/    |

    === "Example 3"

        Within Emby I have two libraries: `TV`, and `Reality TV` located at
        `C:\TV` and `K:\Reality TV`; within Plex there are two libraries:
        `Anime` and `Reality TV` located at `C:\Anime` and `K:\Reality TV` (the
        same directory as within Emby). The Library Paths setting should look
        like:

        | Media Server | Library Name | Path          |
        | :----------- | :----------- | :------------ |
        | Emby         | TV           | C:\TV         |
        | Emby         | Reality TV   | K:\Reality TV |
        | Plex         | Anime        | C:\Anime      |
        | Plex         | Reality TV   | K:\Reality TV |

When Syncing, TCM will _add_ the library assignments defined in the Connection
to the Series.

---

## ![Tautulli Logo](../assets/tautulli.png){.no-lightbox} Tautulli

Typically, TitleCardMaker creates and loads Title Cards on an [adjustable
schedule](./scheduler.md). However, TCM is able to set up a Notification Agent
on Tautulli so that it can notify TCM __immediately__ after new Episodes are
available, or an existing Episode has been watched.

This integration can only be created _after_ creating a Plex connection, and it
is server-specific, as Tautulli only works on one Plex server at a time.

The instructions for enabling this integration are detailed in the
[Getting Started](../getting_started/connections/tautulli.md) page.

---

## :simple-themoviedatabase:{.tmdb} TheMovieDatabase

TMDb is a free database service which can serve as an
[Episode Data Source](./settings.md#episode-data-source), and is the recommended
[Image Source](./settings.md#image-source-priority) due to the much higher
quality (and wider selection) of images compared to the Media Servers. It is
also the only Connection which can provided Episode translations, Series logos,
backdrops, and posters.

??? question "Why enable multiple TMDb Connections?"

    Because TMDb is a _service_, and not a local server, in a vast majority of
    use cases, users __should not__ enable multiple TMDb Connections (as each
    Connection will have the same data available).
    
    However, _some_ users might find value in the flexibility to selectively
    adjust some options (such as image resolution or language priority), so the
    ability is present (and it was also just easier to program that way
    :man_shrugging:).

### Connection Name

The name of the Connection as it appears within the UI. This is purely
aesthetic.

### API Key

API key to submit request to TMDb. These are free, and details on obtaining one
are covered in [Getting Started](../getting_started/connections/tmdb.md).

### Minimum Image Resolution

The minimum resolution of _Source Images_ to gather from TMDb. This must be
entered as `{width}x{height}` - e.g. `800x400` - and can be as low as `0x0` (to
not apply any minimum resolution).

### Ignore Localized Images

<!-- md:overwritable Series, Template -->

When users upload images to TMDb they can assign a language to that image - this
is not common, but some Episodes feature in-Episode title cards which might
typically want to be avoided by TCM. Enabling this will direct TCM to ignore all
images with assigned language codes.

### Logo Language Priority

The relative priority of languages to search for logos under. Ordered highest
to lowest priority.

For non-English users whose library might contain non-English content, it is
recommended to set this to (your language) _then_ English; as this will prompt
TCM to search for logos in your native language and then English if none are
available.

[^1]: If you are using an uncompressed
[file extension](./settings.md#card-extension), like `.png` or `.tiff`, 
alongside a low filesize limit, then the compression algorithm TCM uses might
fail to compress and upload some Title Cards.
