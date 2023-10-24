# Configuring Connections

TitleCardMaker can communicate directly with Emby, Jellyfin, Plex,
Sonarr, Tautulli, and TMDb to get episode data, download images, add
translations, and load Title Cards.

Although not required to run TCM, enabling whichever connections that
are applicable to your setup will improve TCM's operation.

!!! warning "Using Multiple Media Servers"

    Although using multiple media servers together - e.g. any two of
    Emby, Jellyfin, and Plex - is _possible_, using [watch-specific
    styles]() will not integrate well if the two Servers have different
    watch statuses.
