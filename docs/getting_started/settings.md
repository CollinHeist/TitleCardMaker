# Settings
For most users the default Settings can be left as-is. If you'd like to adjust
these, additional detail can be found [here](../user_guide/settings.md).

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
        | Card Dimensions | 3200x1800 |
        | Card Extension | .jpg |
        | Filename Format | {series_full_name} - S{season_number:02}E{episode_number:02} |
        | Specials Folder Format | Specials |
        | Season Folder Format | Season {season_number} |
        | ImageMagick Docker Container | Unchecked and Disabled |

    === "Non-Docker"

        | Setting | Recommended Value |
        | ---: | :--- |
        | Card Directory | ./cards/ |
        | Source Directory | ./source/ |
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

If you are not using Sonarr, then you will need to change your Episode Data
Source setting to either TMDb or your Media Server.