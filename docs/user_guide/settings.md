---
title: Global Settings
description: >
    In-depth descriptions of all global settings.
tags:
    - Global Settings
---

# Settings

!!! warning "Under Construction"

    This documentation is actively being developed.

From the left-hand navigation menu, Global Settings can be accessed and set.
Settings listed here are the _global_ defaults for TitleCardMaker, but many can
be overwritten within an Episode, Series, or Template.

## Recommended Settings
TitleCardMaker's default settings are typically the recommended settings
for a vast majority of users. Specifics about each setting are detailed
below.

??? tip "Recommended Settings"

    === "Docker"

        | Setting | Recommended Value |
        | ---: | :--- |
        | Card Directory | /config/cards/ |
        | Source Directory | /config/source/ |
        | Episode Data Source | Sonarr | 
        | Image Source Priority | `TMDb` `Plex` `Emby` `Jellyfin` |
        | Sync Specials | Unchecked |
        | Default Card Type | _Personal Preference_ |
        | Excluded Card Types | _Personal Preference_ |
        | Watched Episode Style | Unique |
        | Unwatched Episode Style | _Personal Preference_ |
        | Card Dimensions | 3200x1800 |
        | Card Extension | .jpg |
        | Filename Format | {series_full_name} - S{season_number:02}E{episode_number:02} |
        | Specials Folder Format | Specials |
        | Season Folder Format | Season {season_number} |
        | ImageMagick Docker Container | Unchecked and Disabled |

    === "Non-Docker"

        | Setting | Recommended Value |
        | ---: |  :--- |
        | Card Directory | ./config/cards/ |
        | Source Directory | ./config/source/ |
        | Episode Data Source | Sonarr | 
        | Image Source Priority | `TMDb` `Plex` `Emby` `Jellyfin` |
        | Sync Specials | Unchecked |
        | Default Card Type | _Personal Preference_ |
        | Excluded Card Types | _Personal Preference_ |
        | Watched Episode Style | Unique |
        | Unwatched Episode Style | _Personal Preference_ |
        | Card Dimensions | 3200x1800 |
        | Card Extension | .jpg |
        | Filename Format | {series_full_name} - S{season_number:02}E{episode_number:02} |
        | Specials Folder Format | Specials |
        | Season Folder Format | Season {season_number} |
        | ImageMagick Docker Container | Unchecked and Disabled |

## Quick Reference
Below is a brief description of each setting, as well as whether that setting
can be overwritten per-Series. Each setting is described in greater detail
below.

| Setting | Overwritable | Description |
| ---: | :---: | :--- |
| Card Directory | :material-check:{.green} | Root directory where all Title Cards will be created and stored. |
| Source Directory | :octicons-x-16:{.red} | Root directory where all source images will be stored. |
| Episode Data Source | :material-check:{.green} | Where to source Series Episode data from. |
| Image Source Priority | :octicons-x-16:{.red} | Where to gather source images from. |
| Sync Specials | :material-check:{.green} | Whether to ignore Episodes from Season 0 by default. |
| Default Card Type | :material-check:{.green} | Default card type to use for all Title Cards. |
| Excluded Card Types | :octicons-x-16:{.red} | Card types to exclude from card type dropdowns (for easier use). |
| Watched Episode Style | :material-check:{.green} | How to style Title Cards for Episodes that are watched. |
| Unwatched Episode Style | :material-check:{.green} | How to style Title Cards for Episodes that are unwatched. |
| Card Width and Height | :octicons-x-16:{.red} | Image dimensions for created Title Cards. |
| Card Extension | :octicons-x-16:{.red} | Image extension for created Title Cards. |
| Filename Format | :material-check:{.green} | Format for the filenames of created Title Cards. |
| Specials Folder Format | :octicons-x-16:{.red}| Format of the folder name for Title Cards from Season 0. |
| Season Folder Format | :octicons-x-16:{.red} | Format of the folder name for all other Title Cards. |

## Root Folders
The root folders listed here serve as the primary asset directories for both
Title Card and Source images. If using Docker, it is importan that both of these
directories are accessible _outside_ of the Container.

### Card Directory

<!-- md:overwritable Series  -->

The root folder for all Title Cards created by TitleCardMaker. Within this
directory, each Series added to TitleCardMaker will have a subfolder created for
it, under which cards will be created.

??? example

    === "Docker"

        For Docker setups, the recommended settings for this is
        `/config/cards`. In this instance, if the Series `Breaking Bad` were
        added to TitleCardMaker, I'd expect to find all associated Title Cards
        under the `/config/cards/Breaking Bad (2008)/` directory.

    === "Non-Docker"

        When installed locally, this setting can be whatever is most-convenient.
        It is very common to specify a `cards` directory within your local
        installation directory, e.g. `./config/cards/`. However, this is not
        required. In this instance, if the Series `Breaking Bad` were added to
        TitleCardMaker, I'd expect to find all associated Title Cards under the
        `./config/cards/Breaking Bad (2008)/` directory.

This directory __does not__ need to align with your Media folders (where your
media files are kept), as TCM loads the Title Cards directly into your Media
Server, bypassing any "local media" matching.

### Source Directory
The root folder for all source images downloaded and used by TitleCardMaker.
Within this directory, each Series added to TitleCardMaker will have a subfolder
created for it, under which source images (and logos) will be added.

??? question "What's a Source Image?"

    A source image is the (typically) textless input images which text or
    effects are added on top of (by TCM) to create a Title Card.

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
        within your local installation directory, e.g. `./config/source/`.
        However, this is not required. In this instance, if the Series
        `Breaking Bad` were added to TitleCardMaker, I'd expect to find
        all associated source images (and logos) under the `./config/source/
        Breaking Bad (2008)/` directory.

---

## Episode Data
### Episode Data Source

<!-- md:overwritable Series, Template -->

So that Episode data (e.g. numbers, titles, airdates, etc.) does not have to be
manually entered, TitleCardMaker needs to source Episode data from some external
source. Any enabled Connection _can_ be used as an Episode Data source -
however, there are some differences between each.

??? info "Differences in Episode Data Sources"

    | Episode Data Source | Provides Absolute Episode Numbers | Only Provides Data for Downloaded Episodes | Relative Speed |
    | :---: | :---: | :---: | :---: |
    | Emby | :material-close:{.red} | :material-check:{.green} | Average |
    | Jellyfin | :material-close:{.red} | :material-check:{.green} | Average |
    | Plex | :material-close:{.red} | :material-check:{.green} | Average |
    | Sonarr | :material-check:{.green} | :material-check:{.green} [^1] | Fast |
    | TMDb | :material-close:{.red} | :octicons-x-16:{.red} | Fast |

    The speed of a Media Server as an Episode data source will vary wildy with
    both the number of Episodes for a given Series, as well as the overall size
    of your database.

### Image Source Priority

Similar to the [Episode data source](#episode-data-source) option, this
setting controls where TitleCardMaker should gather images (this includes source
images, logos, and posters) from. Unlike the Episode data source, multiple
sources can be specified here, and the selected order does matter.

TitleCardMaker, while searching for images, will try the listed sources
_in order_ until a source image is found.

??? tip "Recommended Setting"

    For __a vast majority__ of users, specifying TMDb and then your Media
    Servers (so `TMDb` `Plex`, etc.) is recommended. This is  because TMDb has a
    much wider variety of image availability, and is typically much higher
    quality than the auto-scraped images from your Media Server.

### Sync Specials

<!-- md:overwritable Series, Template -->

Whether to ignore Episodes from Season 0 by default.

Many Series have "bonus" content like behind the scenes, featurettes, shorts,
commercials, etc. listed under Season 0 as _Specials_. If you would like TCM to
ignore these when grabbing Episode data from you specified Episode data source,
then uncheck this setting.

??? note "Manually Adding Specials"

    Even if this setting is disabled (so Specials are ignored), Episodes can
    still be added manually.

### Translation Languages

Depending on the Card and your indicated episode text format or season titles,
TCM can add spelled versions of a number to a Title Card - e.g.
`Season One - Episode Four`. If you would like this text translated into a non-
English language, the language(s) you would like to make available should be
selected here.

After selecting any number of languages here, the language code can be appended
to the end of a cardinal or ordinal variable to use the translated version of
that text. See the following example for details.

??? example "Example"

    If I would like my Title Card's text to be in French (fr) or Esperanto (eo)
    then I would select both of those languages in the dropdown. Now, within a
    Template or Series I can specify the _Episode Text Format_ (or season title)
    as `Épisode {episode_number_cardinal_fr}` or
    `{episode_number_ordinal_eo} Epizodo` and my Card's episode text would read
    as `Épisode un` (Episode One) or `unua Epizodo` (First Episode).

!!! tip "Cardinal vs. Ordinal Mnemonic"

    An easy way to remember whether you want the cardinal or ordinal text is
    that ++c++ardinal starts with a ++c++ like ++c++ount - so one, two, three,
    etc.; while ++o++ordinal starts with ++o++ like ++o++rder - so first,
    second, third, etc.

This is purely to make these languages _available_ for use - you will still need
to actually change your Card settings to reflect them. This setting __does not__
change Episode titles; that requires [translations](...).

---

## Title Cards
### Default Card Type

<!-- md:overwritable Episode, Series, Template -->

The global default card type for all Title Cards. Any instances where the card
type is left _unspecified_ will use this card type.

??? warning "Missing Card Types?"

    [Excluded card types](#excluded-card-types) are _not_ shown in this dropdown.

### Excluded Card Types

Any number of card types to exclude from any card type dropdowns. This is purely
a cosmetic selector, and is intended to make finding your desired card easier if
you find there are specific types you intend to never use.

### Watched and Unwatched Episode Styles

<!-- md:overwritable Episode, Series, Template -->

The default style for all Episodes that are **watched** or **unwatched** in
their indicated Media Server.

For a visual example of each available style, click the :octicons-question-16:
icon next to either dropdown.

!!! note "Relevant User"

    The watched statuses for Emby and Jellyfin can be adjusted in the Connection
    configuration, but the watched statuses of a Plex Media Server will
    __always__ come from the server admin.

### Card Dimensions

The output dimensions of all created Title Cards. This can be reduced to
decrease the filesize (and therefore quality) of your Title Card assets, or
increased for the opposite effect.

??? warning "16:9 Aspect Ratio"

    TCM will not stop you from setting a non-standard (non-16:9) aspect ratio,
    but your created Title Cards __will__ be cropped when loaded into your
    Media Server.

---

## File Naming
### Card Extension

Image extension for all created Title Cards. Below is a table summarizing the
differences in each type (with regards to TCM):

??? tip "Image Extension Differences"
 
    | Format | Compression Category | Supports Transparency | Relative Filesize |
    | :---: | :---: | :---: | :---: |
    | `jpg` / `jpeg` | Lossy | :material-close:{.red} | 100% |
    | `png` | Lossless | :material-check:{.green} | 230% |
    | `tiff` | Lossless | :material-check:{.green} | 300% |
    | `gif` | Lossless | :material-check:{.green} | 90% |
    | `webp` | Lossless / Lossy | :material-check:{.green} | 70% |

    !!! note "Note about Transparency"

        Only a select few card types can take advantage of transparency. These
        are typically types that allow use of a background _color_ instead of an
        image - e.g. the [Roman Numeral](...) and [Logo](...) cards.

My personal recommendation is to use the `webp` image extension because of the
file size savings and support for transparency. The reason this is not the
default is because of the ubiquity of JPEG images.

### Filename Format

<!-- md:overwritable Series -->

The format / naming convention of how to name the Title Card files. This is a
_format_, and will be applied to each individual Title Card. This format can
contain variable data (wrapped in `{}` curly braces) that is evaluated for each
Title Card.

A full list of the available variables are listed below.

??? note "Available Variables"

    All the following examples will be for _Mr. Robot_ Season 4 Episode 1
    (absolute episode 33), titled "401 Unauthorized"

    ## Series Variables

    | Variable | Example |
    | ---: | :--- |
    | `{series_name}` | Mr. Robot |
    | `{series_full_name}` | Mr. Robot (2015) |
    | `{year}` | 2015 |
    | `{series_emby_id}` | _Depends_ |
    | `{series_imdb_id}` | tt4158110 |
    | `{series_jellyfin_id}` | _Depends_ |
    | `{series_sonarr_id}` | _Depends_ |
    | `{series_tmdb_id}` | 62560 |
    | `{series_tvdb_id}` | 289590 |
    | `{series_tvrage_id}` | N/A |

    ## Episode Variables

    | Variable | Example |
    | ---: | :--- |
    | `{season_number}` | 4 |
    | `{season_number:02}` | 04 |
    | `{episode_number}` | 1 |
    | `{episode_number:02}` | 01 |
    | `{absolute_number}` | 33 |
    | `{title}` | 401 Unauthorized |
    | `{title.lower()}` | 401 unauthorized |
    | `{title.upper()}` | 401 UNAUTHORIZED |
    | `{episode_emby_id}` | _Depends_ |
    | `{episode_imdb_id}` | tt7748418 |
    | `{episode_jellyfin_id}` | _Depends_ |
    | `{episode_tmdb_id}` | 1905049 |
    | `{episode_tvdb_id}` | 7337251 |
    | `{episode_tvrage_id}` | N/A |


    !!! tip "Formatting"

        All number data can be zero-padded with `n` many zeroes. Just specify
        the variable as `{variable:0n}`.

        All text data can be made fully upper or lowercase. Just specify the
        variable as `{variable.upper()}` or `{variable.lower()}`.

??? example "Example Formats"

    ```
    {series_full_name} - S{season_number:02}E{episode_number:02}
    ```

    Will produce files named like `Breaking Bad (2008) - S01E01`.

    ```
    {series_name} [{series_imdb_id}] - S{season_number}E{episode_number} - {title}
    ```

    Will produce files named like `Breaking Bad [tt0903747] - S1E1 - Pilot`.

??? example "TRaSH Naming Convention"

    If you follow the
    [TRaSH](https://trash-guides.info/Sonarr/Sonarr-recommended-naming-scheme/)
    recommended naming scheme, you can use the following setting:

    ```
    {series_full_name} - S{season_number:02}E{episode_number:02} - {title}
    ```

    It is important to note that this can produce _extremely_ long file names
    - sometimes _too_ long for your OS - if the Episode titles are exceedingly
    long, in particular for some Anime.

### Specials Folder Format

...

### Season Folder Format

...

---

## Web Interface

### Home Page Size

How many Series to display on the home screen. Larger values will result in
longer load times. Must be between 1 and 250.

### Episode Data Table Page Size

How many Episodes per page to display in Episode data tables. These are the
tables accessed on a [Series page](./series.md) in the _Episode Data_ tab.

### Simplified Episode Data Tables

Whether to hide Advanced (uncommonly edited) columns from Episode data tables.
This is purely a visual toggle inted to make navigation easier, and any existing
customizations, whether they were entered beforehand or are imported from a
[Blueprint](../blueprints.md) are still applied.

### Stylize Unmonitored Series Posters

Whether to apply different styling to the posters of unmonitored Series on the
home screen. This is to make differentiating between the two easier when
navigating the home screen.

Stylized posters have a blurred grayscale effect applied.

### Source Image Data Display

On the _Files_ tab of the [Series](./series.md) page, source image data can be
presented as "card" elements or inside a table. The same information and actions
are available in either view.

### Color Impaired Mode

Accessibility feature to utilize an alternate coloring which makes certain
color combinations more distinguishable for those with color impairments.

!!! note "Accessibility Feedback"

    If you have feedback or suggestions on improving the accessibility of the
    project, please reach out on the [Discord](https://discord.gg/bJ3bHtw8wH) or
    [GitHub](https://github.com/TitleCardMaker/TitleCardMaker-WebUI/).

[^1]: This can be toggled on/off.