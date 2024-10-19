---
title: Global Settings
description: >
    In-depth descriptions of all global settings.
tags:
    - Global Settings
---

# Settings

From the left-hand navigation menu, Global Settings can be accessed and set.

![](../assets/settings_light.webp#only-light){.no-lightbox}
![](../assets/settings_dark.webp#only-dark){.no-lightbox}

Settings listed here are the _global_ defaults for TitleCardMaker, but many can
be overwritten within an Episode, Series, or Template. If a specific setting can
be overwritten, then some variation of this badge will be displayed next to the
Setting (here, not within the UI).

<!-- md:overwritable Episode, Series, Template -->

With the above meaning it can be overwritten per-Episode, per-Series, and
per-Template.

## Recommended Settings
TitleCardMaker's default settings are typically the recommended settings
for a vast majority of users. Specifics about each setting are detailed
below.

??? tip "Recommended Settings"

    === "Docker"

        | Setting                     | Recommended Value                                            |
        | --------------------------: | :----------------------------------------------------------- |
        | Card Directory              | /config/cards/                                               |
        | Source Directory            | /config/source/                                              |
        | Delete Series Source Images | :fontawesome-regular-circle-xmark:{.red}                     |
        | Episode Data Source         | Sonarr                                                       |
        | Image Source Priority       | `TMDb` `Plex` `Emby` `Jellyfin`[^2]                          |
        | Enable Specials             | :fontawesome-regular-circle-xmark:{.red}                     |
        | Delete Missing Episodes     | :fontawesome-regular-circle-check:{.green}                   |
        | Default Card Type           | _Personal Preference_                                        |
        | Excluded Card Types         | _Personal Preference_                                        |
        | Watched Episode Style       | Unique                                                       |
        | Unwatched Episode Style     | _Personal Preference_                                        |
        | Default Templates           | _Blank_                                                      |
        | Card Dimensions             | 3200x1800[^3]                                                |
        | Card Quality                | 95                                                           |
        | Card Extension              | .jpg                                                         |
        | Filename Format             | {series_full_name} - S{season_number:02}E{episode_number:02} |
        | Specials Folder Format      | Specials                                                     |
        | Season Folder Format        | Season {season_number}                                       |
        | Multi-Library File Naming   | :fontawesome-regular-circle-xmark:{.red}                     |

    === "Non-Docker"

        | Setting                     | Recommended Value                                            |
        | --------------------------: | :----------------------------------------------------------- |
        | Card Directory              | ./config/cards/                                              |
        | Source Directory            | ./config/source/                                             |
        | Delete Series Source Images | :fontawesome-regular-circle-xmark:{.red}                     |
        | Episode Data Source         | Sonarr                                                       |
        | Image Source Priority       | `TMDb` `Plex` `Emby` `Jellyfin`[^2]                          |
        | Enable Specials             | :fontawesome-regular-circle-xmark:{.red}                     |
        | Delete Missing Episodes     | :fontawesome-regular-circle-check:{.green}                   |
        | Default Card Type           | _Personal Preference_                                        |
        | Excluded Card Types         | _Personal Preference_                                        |
        | Watched Episode Style       | Unique                                                       |
        | Unwatched Episode Style     | _Personal Preference_                                        |
        | Default Templates           | _Blank_                                                      |
        | Card Dimensions             | 3200x1800[^3]                                                |
        | Card Quality                | 95                                                           |
        | Card Extension              | .jpg                                                         |
        | Filename Format             | {series_full_name} - S{season_number:02}E{episode_number:02} |
        | Specials Folder Format      | Specials                                                     |
        | Season Folder Format        | Season {season_number}                                       |
        | Multi-Library File Naming   | :fontawesome-regular-circle-xmark:{.red}                     |

## Episode Data
### Episode Data Source

<!-- md:overwritable Series, Template -->

So that Episode data (e.g. numbers, titles, airdates, etc.) does not have to be
manually entered, TitleCardMaker needs to source Episode data from some external
source. Any enabled Connection _can_ be used as an Episode Data source -
however, there are some differences between each.

??? info "Differences in Episode Data Sources"

    | Episode Data Source | Provides Absolute Episode Numbers | Only Provides Data for Downloaded Episodes | Relative Speed |
    | :------: | :----------------------: | :---------------------------: | :-----: |
    | Emby     | :material-close:{.red}   | :material-check:{.green}      | Average |
    | Jellyfin | :material-close:{.red}   | :material-check:{.green}      | Average |
    | Plex     | :material-close:{.red}   | :material-check:{.green}      | Average |
    | Sonarr   | :material-check:{.green} | :material-check:{.green} [^1] | Fast    |
    | TMDb     | :material-close:{.red}   | :octicons-x-16:{.red}         | Fast    |
    | TVDb     | :material-check:{.green} | :octicons-x-16:{.red}         | Fast    |

    The speed of your Media Server and Sonarr as an Episode data source will
    vary wildy with both the number of Episodes for a given Series, as well as
    the overall size of your database.

### Image Source Priority

Similar to the [Episode Data Source](#episode-data-source) option, this
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

### Delete Missing Episodes

Whether to delete Episodes (from TCM) which are not present in the assigned
Episode Data Source. When an Episode is deleted, the associated Title Card file
is also deleted.

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
their indicated Media Server. For Episodes whose watched statuses cannot be
determined (likely the Episode is not available in your Media Server), the
unwatched styling is used.

For a visual example of each available style, click the :octicons-question-16:
icon next to either dropdown.

!!! note "Relevant User"

    The watched statuses for Emby and Jellyfin can be adjusted in the Connection
    configuration, but the watched statuses of a Plex Media Server will
    __always__ come from the server admin.

--------------------------------------------------------------------------------

## ImageMagick

### Card Dimensions

The output dimensions of all created Title Cards. This can be reduced to
decrease the filesize (and therefore quality) of your Title Card assets, or
increased for the opposite effect.

??? warning "16:9 Aspect Ratio"

    TCM will not stop you from setting a non-standard (non-16:9) aspect ratio,
    but your created Title Cards __will__ be cropped when loaded into your Media
    Server.

### Card Quality

!!! note "Applicability"

    This setting is only applicable when using a
    [Card Extension](#card-extension) of `jpg`, `jpeg`, or `png`.

The compression level to apply when creating Title Cards. The minimum quality,
1, will result in extremely low quality (highly compressed) Cards; and the
highest quality, 100, will result in the best quality (but least-compressed)
Cards. The recommended value is between 92 and 95.

??? tip "Advanced Details"

    This setting is not exactly linear in the effective quality _or_ reduced
    file sizes. This means changing the quality from 90 to 45 will not
    necessarily result in a 50% reduction in filesize or image quality.

    For more details, read the applicable
    [ImageMagick documentation](https://www.imagemagick.org/script/command-line-options.php#quality).

### ImageMagick Executable

The filepath to the ImageMagick executable (usually `magick.exe`) which will be
used to run all ImageMagick commands. This is required for some Windows users
if the `convert` command is not properly added to your system PATH - this
usually manifests as all Title Cards failing to be created.

--------------------------------------------------------------------------------

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

The root folder for all Source Images downloaded and used by TitleCardMaker.
Within this directory, each Series added to TitleCardMaker will have a subfolder
created for it, under which Source Images (and logos) will be added.

??? question "What's a Source Image?"

    A Source Images is the (typically) textless input images which text or
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

### Source Image Deletion

Whether to delete Source Images when a Series is deleted from TitleCardMaker.

If enabled, any Series that are deleted (manually or automatically) will have
their entire source directory cleared - including Source Images, posters, logos,
and backdrop art.

---

## File Naming

### Filename Format

<!-- md:overwritable Series -->

The format / naming convention of how to name the Title Card files. This is a
_format_, and will be applied to each individual Title Card. This format can
contain variable data (wrapped in `{}` curly braces) that is evaluated for each
Title Card.

A complete list of the available variables is listed [here](./variables.md).

??? example "Example Formats"

    ```
    {series_full_name} - S{season_number:02}E{episode_number:02}
    ```

    Will produce files named like `Breaking Bad (2008) - S01E01`.

    ```
    {series_name} [{series_imdb_id}] - S{season_number}E{episode_number} - {title}
    ```

    Will produce files named like `Breaking Bad [tt0903747] - S1E1 - Pilot`.

??? tip "TRaSH Naming Convention"

    If you follow the
    [TRaSH](https://trash-guides.info/Sonarr/Sonarr-recommended-naming-scheme/)
    recommended naming scheme, you can use the following setting:

    ```
    {series_full_name} - S{season_number:02}E{episode_number:02} - {title}
    ```

    It is important to note that this can produce _extremely_ long file names
    - sometimes too long for the operating system - if the Episode titles are
    exceedingly long. TCM will automatically truncate all file names at 254
    characters.

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

### Specials Folder Format

The format / naming convention for the subfolder of all Title Cards associated
with Specials (season 0). This format can contain variable data, see a complete
list of the available variables is listed [here](./variables.md).

??? tip "Hidden Season Subfolder"

    If you would like to completely remove the subfolder - i.e. write these
    Title Cards directory at the Title Card directory for the  Series - then
    specify the format as:

    ```
    {''}
    ```

### Season Folder Format

The format / naming convention for the subfolder of all Title Cards associated
with all non-Specials (anything other than season 0). This format can contain
variable data, see a complete list of the available variables is listed
[here](./variables.md).

??? tip "Hidden Season Subfolder"

    If you would like to completely remove the subfolder - i.e. write these
    Title Cards directory at the Title Card directory for the  Series - then
    specify the format as:

    ```
    {''}
    ```

### Multi-Library File Naming

!!! warning "Warning"

    Erroneously enabling this setting can result in TitleCardMaker deleting and
    remaking duplicates of all your Title Cards. Please read the following
    descripion and the in-UI help text __very thoroughly__.

Whether to add a unique Library-specific "identifier" to the filenames of all
Title Cards. This is separate from your [Filename Format](#filename-format)
setting.

This setting should only be enabled by users who have more than one Media Server
_and_ would like to utilize watched status specific styling.

Once enabled, TitleCardMaker will keep separate Title Card files created for
each Library assigned to a Series. 

??? example "Example"

    The following example showcases a use of this setting in a Series with three
    libraries alongside Templates which utilize
    [watched-status Filters](./templates.md#filters) to create completely
    different Title Cards for each library.

    ![](../assets/library_unique_cards_light.webp#only-light){.no-lightbox}
    ![](../assets/library_unique_cards_dark.webp#only-dark){.no-lightbox}

    The first two columns are for libraries in which the Episode is watched,
    and in the third column that Episode has not been watched.

---

## Web Interface

### Home Page Size

How many Series to display on the home screen. Larger values will result in
longer load times. Must be between 1 and 250.

### Episode Data Table Page Size

How many Episodes per page to display in Episode data tables. These are the
tables accessed on a [Series page](./series.md) in the _Episode Data_ tab. Must
be at least 1.

### Source Image Preview Page Dimensions

How many Source Image previews to display per page. These are displayed on a
[Series page](./series.md) in the _Files_ tab. This is entered as the number of
rows and columns - e.g. `3x4` is 3 rows of 4 columns each. Must be between 1
and 100 items per page.

### Title Card Preview Page Dimensions

How many Title Card previews to display per page. These are displayed on a
[Series page](./series.md) in the _Files_ tab. This is entered as the number of
rows and columns - e.g. `2x3` is 2 rows of 3 columns each. Must be between 1
and 100 items per page.

### Home Page Table Display

The home page can be displayed in two ways: as a table, or as a series of
posters. The tabular view is recommended because it contains more information,
allows you to perform bulk actions on multiple Series at once, easily edit
specific Series data, and is generally faster. An example of the two is shown
below.

=== "Tabular View"

    ![](../assets/home_table_light.webp#only-light){.no-lightbox}
    ![](../assets/home_table_dark.webp#only-dark){.no-lightbox}

=== "Poster View"

    ![](../assets/home_poster_light.webp#only-light){.no-lightbox}
    ![](../assets/home_poster_dark.webp#only-dark){.no-lightbox}

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

### Color Impaired Mode

Accessibility feature to utilize an alternate coloring which makes certain
color combinations more distinguishable for those with color impairments.

!!! note "Accessibility Feedback"

    If you have feedback or suggestions on improving the accessibility of the
    project, please reach out on the [Discord](https://discord.gg/bJ3bHtw8wH) or
    [GitHub](https://github.com/TitleCardMaker/TitleCardMaker-WebUI/).

### Reduced Animations

Whether to disable various animations within the UI. This can be for improved
site performance or accessibility.

This does not disable all animations, just the more "egregious" ones like the
home-page Series loading.

[^1]: This can be toggled on/off.

[^2]: Only include the Connections which you are personally using.

[^3]: Feel free to reduce this to some ratio of 16:9 (e.g. 1600:900) if you want
to save storage space (at the minor cost of image fidelity). Increasing this is
not recommended.
