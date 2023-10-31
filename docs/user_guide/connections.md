---
title: External Connections
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

- Authentication
- Emby
- Jellyfin
- Plex
- Sonarr
- Tautulli
- TheMovieDatabase (TMDb)

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

## :material-emby:{.emby} Emby Media Servers

...

## :simple-jellyfin:{ .jellyfin } Jellyfin Media Servers

...

## :material-plex:{ .plex } Plex Media Servers

...

## Sonarr

...

## Tautulli

## :simple-themoviedatabase:{.tmdb} TheMovieDatabase