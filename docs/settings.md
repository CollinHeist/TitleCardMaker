# Settings
## Background
From the left-hand navigation menu, Global Settings can be accessed and
set. Settings listed here are the _global_ defaults for TitleCardMaker,
but many can be overwritten for a specific Series.

---

## Recommended Settings
TitleCardMaker's default settings are typically the recommended settings
for a vast majority of users. Specifics about each setting are detailed
below.

??? tip "Recommended Settings"

    === "Docker"

        | Setting | Recommended Value |
        | ---: | :--- |
        | Card Directory | `/config/cards/` |
        | Source Directory | `/config/source/` |
        | Episode Data Source | Sonarr | 
        | Image Source Priority | `TMDb` `Plex` `Emby` `Jellyfin` |
        | Sync Specials | Unchecked |
        | Default Card Type | _Personal Preference_ |
        | Excluded Card Types | _Personal Preference_ |
        | Watched Episode Style | Unique |
        | Unwatched Episode Style | _Personal Preference_ |
        | Card Dimensions | 3200x1800 |
        | Card Extension | `.jpg` |
        | Filename Format | `{series_full_name} - S{season_number:02}E{episode_number:02}` |
        | Specials Folder Format | Specials |
        | Season Folder Format | `Season {season_number}` |
        | ImageMagick Docker Container | Unchecked and Disabled |

    === "Non-Docker"

        ...

## Root Folders
The root folders listed here serve as the primary asset directories for
both Title Card and Source images. If using Docker, it is important
that both of these directories are accessible _outside_ of the Container.

### Card Directory
The root folder for all Title Cards created by TitleCardMaker. Within
this directory, each Series added to TitleCardMaker will have a
subfolder created for it, under which cards will be created.

??? example

    === "Docker"

        For Docker setups, the recommended settings for this is
        `/config/cards`. In this instance, if the Series `Breaking Bad`
        were added to TitleCardMaker, I'd expect to find all associated
        Title Cards under the `/config/cards/Breaking Bad (2008)/`
        directory.

    === "Non-Docker"

        When installed locally, this setting can be whatever is most-
        convenient. It is very common to specify a `cards` directory
        within your local installation directory, e.g. `./cards/`.
        However, this is not required. In this instance, if the Series
        `Breaking Bad` were added to TitleCardMaker, I'd expect to find
        all associated Title Cards under the `./cards/Breaking Bad
        (2008)/` directory.

This directory __does not__ need to align with your Media folders (where
your media files are kept), as TCM loads the Title Cards directly into
your Media Server, bypassing any "local media" matching.

### Source Directory
The root folder for all source images downloaded and used by 
TitleCardMaker. Within this directory, each Series added to
TitleCardMaker will have a subfolder created for it, under which source
images (and logos) will be added.

??? question "What's a Source Image?"

    A source image is the (typically) textless input images which text
    or effects are added on top of (by TCM) to create a Title Card.

??? example

    === "Docker"

        For Docker setups, the recommended settings for this is
        `/config/source`. In this instance, if the Series `Breaking Bad`
        were added to TitleCardMaker, I'd expect to find all associated
        source images (and logos) under the `/config/source/Breaking Bad
        (2008)/` directory.

    === "Non-Docker"

        When installed locally, this setting can be whatever is most-
        convenient. It is very common to specify a `source` directory
        within your local installation directory, e.g. `./source/`.
        However, this is not required. In this instance, if the Series
        `Breaking Bad` were added to TitleCardMaker, I'd expect to find
        all associated source images (and logos) under the `./source/
        Breaking Bad (2008)/` directory.

---

## Episode Data
### Episode Data Source
So that Episode data (e.g. numbers, titles, airdates, etc.) does not 
have to be manually entered, TitleCardMaker needs to source Episode data
from some external source. Any enabled Connection _can_ be used as an
Episode Data source - however, there are some differences between each.

??? info "Differences in Episode Data Sources"

    | Episode Data Source | Provides Absolute Episode Numbers | Only Provides Data for Downloaded Episodes | Relative Speed |
    | :---: | :---: | :---: | :---: |
    | Emby | :material-close: | :material-check: | Slow |
    | Jellyfin | :material-close: | :material-check: | Slow |
    | Plex | :material-close: | :material-check: | Slow |
    | Sonarr | :material-check: | :material-check:{color: green} | Fast |
    | TMDb | :material-close: | :material-check: | Fast |

This setting _can_ be overwritten per-Series, and with Templates.

### Image Source Priority
Similar to the [Episode data source](#episode-data-source) option, this
setting controls where TitleCardMaker should gather Images from. Unlike
the Episode data source, multiple sources can be specified here, and the
selected order does matter.

TitleCardMaker, while searching for images, will try the listed sources
_in order_ until a source image is found.

??? tip "Recommended Setting"

    For __a vast majority__ of users, specifying TMDb and then your
    Media Servers (so `TMDb` `Plex` `...`) is recommended. This is
    because TMDb has a much wider variety of image availability, and is
    typically much higher quality than the auto-scraped images from your
    Media Server.