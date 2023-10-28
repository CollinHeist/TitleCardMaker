---
title: Global Settings
description: >
    Recommended global settings for new users.
tags:
    - Tutorial
    - Global Settings
---

# Settings
For most users the default Settings can be left as-is. If you'd like to adjust
these, additional detail can be found [here](../user_guide/settings.md).

I do recommend clicking through the various options of the Default Card Type
dropdown and picking your favorite style. The most common choices are the
Standard and Tinted Frame cards.

For the purposes of this tutorial, the following settings are recommended:

!!! tip "Recommended Settings"

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
        | Card Dimensions | 3200x1800[^1] |
        | Card Extension | .jpg |
        | Filename Format | {series_full_name} - S{season_number:02}E{episode_number:02} |
        | Specials Folder Format | Specials |
        | Season Folder Format | Season {season_number} |

    === "Non-Docker"

        | Setting | Recommended Value |
        | ---: | :--- |
        | Card Directory | ./config/cards/ |
        | Source Directory | ./config/source/ |
        | Episode Data Source | Sonarr | 
        | Image Source Priority | `TMDb` `Plex` `Emby` `Jellyfin` |
        | Sync Specials | Unchecked |
        | Default Card Type | _Personal Preference_ |
        | Excluded Card Types | _Personal Preference_ |
        | Watched Episode Style | Unique |
        | Unwatched Episode Style | _Personal Preference_ |
        | Card Dimensions | 3200x1800[^1] |
        | Card Extension | .jpg |
        | Filename Format | {series_full_name} - S{season_number:02}E{episode_number:02} |
        | Specials Folder Format | Specials |
        | Season Folder Format | Season {season_number} |

If you are not using Sonarr, then you will need to change your Episode Data
Source setting to either TMDb or your Media Server.

[^1]: Feel free to reduce this to some ratio of 16:9 (e.g. 1600:900) if you want
to save storage space (at the minor cost of image fidelity). Increasing this is
not recommended.
