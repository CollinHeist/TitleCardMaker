---
title: Global Settings
description: >
    Recommended global settings for new users.
tags:
    - Tutorial
    - Global Settings
---

# Settings
For most users the default Settings can be left as-is with the exception of the
_Episode Data Source_ and _Image Source Priority_ settings, which must be set.
If you'd like to adjust these, additional detail can be found
[here](../user_guide/settings.md).

I also recommend clicking through the various options of the Default Card Type
dropdown and picking your favorite style. The most popular choices are the
Tinted Frame and Standard.

For the purposes of this tutorial, the following settings are recommended:

!!! tip "Recommended Settings"

    === ":material-docker: Docker"

        | Setting                     | Recommended Value                                            |
        | --------------------------: | :----------------------------------------------------------- |
        | Episode Data Source         | Sonarr                                                       | 
        | Image Source Priority       | `TMDb` `Plex` `Emby` `Jellyfin`[^1]                          |
        | Enable Specials             | Unchecked                                                    |
        | Delete Missing Episodes     | Checked                                                      |
        | Delete Un-Synced Series     | Unchecked                                                    |
        | Delete Series Source Images | Unchecked                                                    |
        | Default Card Type           | _Personal Preference_                                        |
        | Excluded Card Types         | _Personal Preference_                                        |
        | Watched Episode Style       | Unique                                                       |
        | Unwatched Episode Style     | _Personal Preference_                                        |
        | Card Dimensions             | 3200x1800[^2]                                                |
        | Card Quality                | 95                                                           |
        | ImageMagick Executable      | See note[^3]                                                 |
        | Card Directory              | /config/cards/                                               |
        | Source Directory            | /config/source/                                              |
        | Filename Format             | {series_full_name} - S{season_number:02}E{episode_number:02} |
        | Card Extension              | .webp                                                        |
        | Specials Folder Format      | Specials                                                     |
        | Season Folder Format        | Season {season_number}                                       |
        | Multi-Library File Naming   | _Unchecked_                                                  |

    === ":material-language-python: Non-Docker"

        | Setting                     | Recommended Value                                            |
        | --------------------------: | :----------------------------------------------------------- |
        | Episode Data Source         | Sonarr                                                       | 
        | Image Source Priority       | `TMDb` `Plex` `Emby` `Jellyfin`[^1]                          |
        | Enable Specials             | Unchecked                                                    |
        | Delete Missing Episodes     | Checked                                                      |
        | Delete Un-Synced Series     | Unchecked                                                    |
        | Delete Series Source Images | Unchecked                                                    |
        | Default Card Type           | _Personal Preference_                                        |
        | Excluded Card Types         | _Personal Preference_                                        |
        | Watched Episode Style       | Unique                                                       |
        | Unwatched Episode Style     | _Personal Preference_                                        |
        | Card Dimensions             | 3200x1800[^2]                                                |
        | Card Quality                | 95                                                           |
        | ImageMagick Executable      | See note[^3]                                                 |
        | Card Directory              | ./config/cards/                                              |
        | Source Directory            | ./config/source/                                             |
        | Filename Format             | {series_full_name} - S{season_number:02}E{episode_number:02} |
        | Card Extension              | .webp                                                        |
        | Specials Folder Format      | Specials                                                     |
        | Season Folder Format        | Season {season_number}                                       |
        | Multi-Library File Naming   | _Unchecked_                                                  |

If you are not using Sonarr, then you will need to change your Episode Data
Source setting to either TMDb or your Media Server.

[^1]: Only include the Connections which you are personally using.

[^2]: Feel free to reduce this to some ratio of 16:9 (e.g. 1600:900) if you want
to save storage space (at the minor cost of image fidelity). Increasing this is
not recommended.
