---
title: Configuring Connections
description: >
    Add connections to external services like Emby, Jellyfin, Plex, Sonarr,
    Tautulli, TMDb, and TVDb.
---

# Configuring Connections

TitleCardMaker can communicate directly with Emby, Jellyfin, Plex, Sonarr,
Tautulli, TMDb, and TVDb to automate all aspects of Card creation. Although not
'required' to run TCM, enabling whichever Connections that are applicable to
your setup will vastly improve TCM's operation.

All Connection information should be entered on the Connections page (the
`/connections` URL), which can be found by clicking `Settings`, and then
`Connections` from the sidebar within the UI. The following pages contain
instructions for setting up each type of Connection.

!!! warning "Using Multiple Media Servers"

    Using multiple Media Servers together is _possible_, using [watch-specific
    styles](../../user_guide/settings.md#watched-and-unwatched-episode-styles)
    will require enabling the global [multi-library
    filename](../../user_guide/settings.md#multi-library-filename-support)
    setting in order to properly integrate. Carefully read the in-UI help text
    and the linked documentation before enabling this.
