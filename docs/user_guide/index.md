---
title: User Guide
description: >
    Detailed guides on using each component of TitleCardMaker.
---

# User Guide

!!! warning "Under Construction"

    This documentation is actively being developed.

!!! warning "Not for New Users"

    The User Guide __is not__ intended to be an introduction to TitleCardMaker
    for new users - it is a detailed reference for those already familiar with
    the basics. New users should follow the
    [Getting Started](../getting_started/index.md) tutorial.

## Pages

The TitleCardMaker interface is separated into various pages which can be
navigated to via the sidebar or buttons on the header. Each page is detailed
below:

- [Series](./series.md)
- [Adding Series](./new_series.md)
- [Missing Summary](./missing.md)
- [Templates](./templates.md)
- [Fonts](./fonts.md)
- [Sync](./syncs.md)
- [Settings](./settings.md)
- [Connections](./connections.md)
- [Scheduler](./scheduler.md)
- [Importer](./importer.md)
- [System Summary](./system.md)
- [Logs](./logs.md)
- [Graphs](./graphs.md)
- [Changelog](./changelog.md)

## Selecting a Branch / Tag

TitleCardMaker follows the typical design pattern of lots of software packages,
separating changes which are "in development" and "finalized". As a result, you
have the option of selecting between either of these branches (or _tags_) for
your version of TCM.

!!! warning "Develop Branches / Tags"

    If using the `develop` version of TCM, expect to encounter bugs which may
    require frequently updating. If this sounds cumbersome, stick to the `main`
    branch.

!!! warning "Backwards Compatibility"

    If there are changes to the TCM database schema, these are often
    __irreversible__ - meaning swapping from `develop` to `main` is not
    possible.

### Docker

| Tag Name        | Description                                               | Recommended For..                        |
| :-------------: | :-------------------------------------------------------: | :--------------------------------------- |
| `latest`        | The most up-to-date (stable) release                      | Most users[^1]                           |
| `main`          | _Same as `latest`_                                        | It's recommended to use `latest`         |
| `develop`       | The most feature-rich (unstable) release                  | Those wanting to try the latest features |
| `main-armv7`    | Same as `latest`, but for those on an ARMv7 architecture  | _See `latest`_                           |
| `develop-armv7` | Same as `develop`, but for those on an ARMv7 architecture | _See `develop`_                          |

### Non-Docker

| Branch Name | Description                              | Recommended For..                        |
| :---------: | :--------------------------------------: | :--------------------------------------- |
| `main`      | The most up-to-date (stable) release     | Most users[^1]                           |
| `develop`   | The most feature-rich (unstable) release | Those wanting to try the latest features |

## Environment Variables

??? tip "Specifying an Environment Variable"

    === ":material-docker: :fontawesome-solid-file-code: Docker Compose"

        Add all environment variables under the `environment` section of your
        compose file, like so:

        ```yaml title="docker-compose.yml" hl_lines="5-6"
        name: titlecardmaker
        services:
          tcm:
            # etc.
            environment:
              - TZ=America/Los_Angeles
              - TCM_LOG_STDOUT=WARNING
            # etc.
        ```

    === ":material-docker: Docker"

        Specify the environment variable with the `-e` commands in your Docker
        run command, like so:

        ```bash
        -e TZ=America/Los_Angeles -e TCM_LOG_STDOUT=WARNING
        ```

    === ":material-language-python: Non-Docker"

        The easiest method is to create a file named `.env` in the main TCM
        installation directory (where you type your `python` command) - like so:

        ```ini title=".env"
        TZ=America/Los_Angeles
        TCM_LOG_STDOUT=WARNING
        ```

While a vast majority of TCM's behavior can be adjusted within the UI, there are
a few options which can only be adjusted with environment variables. These are
described below:

`TCM_BACKUP_RETENTION`

:   How long to keep old backups before deleting them. This is an integer number
    of days. The default is `21`.

`TCM_IM_DOCKER`

:   Name of a standalone Docker container to execute ImageMagick commands
    within. This is only required if TCM is __not__ executing within Docker, but
    ImageMagick is. This is unspecified by default.

`TCM_LOG`

:   _This has been deprecated in place of `TCM_LOG_STDOUT`._

`TCM_LOG_STDOUT`

:   The minimum log level for the standard (console) output. Log messages at a
    level _lower_ than this will not be transmitted. This can be either `TRACE`,
    `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. The default is `INFO`.

`TCM_LOG_FILE`

:   The minimum log level for the logging file output. Log messages at a level
    _lower_ than this will not be written to any log files. This can be either
    `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. The default is
    `TRACE` and it is __not recommended__ to change this, as it can make it much
    more difficult to diagnose or debug issues.

`TCM_LOG_RETENTION`

:   How long to keep log files before they are deleted. This can be any human-
    readable duration - e.g. `2 days`, `3 weeks`, etc. The default is `7 days`.

`TCM_NEW_SERIES_VIEW`

:   _As of `v2.0-alpha.10.0`, this setting is no longer requires as the "old"
    Series view has been removed._

`TZ`

:   The timezone which is used for all local time reporting (most notably
    logging). To determine your timezone, a full list is available
    [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). You
    will want to take note of the text in the _TZ Identifer_ column. The default
    is `UTC`.

`TCM_DISABLE_AUTH`

:   Whether to reset and disable authentication access to the TCM UI. This is
    only read when TCM first boots, and if set to `TRUE` then your previously
    established username and password will be deleted. For more details, see
    [here](./connections.md#forgotten-login). This is unspecified by default.

### Plex Variables

TCM uses the [plexapi](https://github.com/pkkid/python-plexapi) module to
communicate with Plex, and as such can be configured by configuring their
assigned environment variables - these are all detailed
[here](https://python-plexapi.readthedocs.io/en/stable/configuration.html).

The most popular one is the API timeout - `PLEXAPI_PLEXAPI_TIMEOUT`.

[^1]:
    Unless you've encountered a bug which you personally _require_ and is only
    available on `develop`.
