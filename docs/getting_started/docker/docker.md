---
title: Docker Installation
description: >
    Installing TitleCardMaker in a Docker container.
---

# Docker Installation

!!! info "Pre-Release Instructions"

    These instructions are __not applicable__ while TCM is in pre-release.
    Please refer to [here](../index.md).

??? info "Benefits of Docker"

    For more info on the benefits of Docker, see [here](./index.md).

For all non-Unraid and Synology DSM users, the TitleCardMaker Docker container
can be built and installed via the command line.

## Installing Docker
Verify the Docker engine is installed by running the following command:

<!-- termynal -->

```bash
$ docker run --rm hello-world
---> 100%
Hello from Docker!
This message shows that your installation appears to be working correctly.
# etc. 
```

If you __do not__ see some variation of the above message, double-check your
Docker daemon is running, or attempt to fix your Docker install. See the
[Docker installation instructions](https://docs.docker.com/engine/install/).

## Selecting a Directory

Identify where you want to store all the TCM data - this will be the SQL
database, poster and font files, source images, and Title Cards. This directory
will be mounted to `/config` inside the container. Navigate to this directory
from the command line.

=== ":material-linux: Linux"

    ```bash
    cd "~/Your/Install/Directory"
    ```

=== ":material-apple: MacOS"

    ```bash
    cd "~/Your/Install/Directory"
    ```

=== ":material-powershell: Windows (Powershell)"

    ```bash
    cd 'C:\Your\Install\Directory'
    ```

=== ":material-microsoft-windows: Windows (Non-Powershell)"

    ```bash
    cd 'C:\Your\Install\Directory'
    ```

Replace the example path with your directory.

## Folder Permissions

Ensure this directory has the correct permission so that TCM can read and
write to it.

For Unix users, you should identify which Group and User you want the container
to run under - this is typically the same GID and UID used for your media server
or Sonarr Docker containers.

=== ":material-linux: Linux"

    With the Group and User ID that you would like TCM to execute with, run
    the following command:

    ```bash
    sudo chown -R {group}:{user} "~/Your/Install/Directory"
    ```

    Replace `{group}:{user}` with the _actual_ group and user names (or
    IDs) - e.g. `99:100`.

=== ":material-apple: MacOS"

    With the Group and User ID that you would like TCM to execute with, run
    the following command:

    ```bash
    sudo chown -R {group}:{user} "~/Your/Install/Directory"
    ```

    Replace `{group}:{user}` with the _actual_ group and user names (or
    IDs) - e.g. `99:100`.

=== ":material-powershell: Windows (Powershell)"

    Changing the permissions is (generally) not necessary on Windows.

=== ":material-microsoft-windows: Windows (Non-Powershell)"

    Changing the permissions is (generally) not necessary on Windows.

## Selecting a Tag

There are two available _tags_ (or branches) for the TCM container - `latest`
and `develop`.

For most users, I recommend the default `latest` branch. This branch is
updated with the most recent public release of TitleCardMaker, and is
the most stable option.

For users who are okay with the occasional bug, and would like to test
out features _as they are developed_, then choose the `develop` tag.

## Creating the Container

Take note of your local timezone from
[here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
- specifically the _TZ Identifier_ column, e.g. `America/Los_Angeles`.

Finally - pull, create, and launch the Docker container by running the following
command.

!!! warning "Installation Directory"

    The following command creates the Container from the __current directory__;
    so double check you have `cd`'d into the directory from above.

=== ":material-linux: Linux"

    Change the value after the `=` for `PGID`, `PUID`, to your Group and
    User ID from Step 3; `TZ` to your local timezone, and the _tag_ after
    `titlecardmaker` to your tag (`latest` or `develop`).

    ```bash
    docker run -itd \
        --net="bridge" \
        -v "$(pwd)":"/config/" \
        -e PGID=99 \
        -e PUID=100 \
        -e TZ="America/Los_Angeles" \
        -p 4242:4242 \
        --name "TitleCardMaker" \
        titlecardmaker:latest
    ```

=== ":material-apple: MacOS"

    Change the value after the `=` for `PGID`, `PUID`, to your Group and
    User ID from Step 3; `TZ` to your local timezone, and the _tag_ after
    `titlecardmaker` to your tag (`latest` or `develop`).

    ```bash
    docker run -itd \
        --net="bridge" \
        -v "$(pwd)":"/config/" \
        -e PGID=99 \
        -e PUID=100 \
        -e TZ="America/Los_Angeles" \
        -p 4242:4242 \
        --name "TitleCardMaker" \
        titlecardmaker:latest
    ```

=== ":material-powershell: Windows (Powershell)"

    Change the value after the `=` to your local timezone, and the _tag_ after
    `titlecardmaker` to your tag (`latest` or `develop`)

    ```bash
    docker run -itd `
        --net="bridge" `
        -v "$(pwd)":"/config/" `
        -e TZ="America/Los_Angeles" `
        -p 4242:4242 `
        --name "TitleCardMaker" `
        titlecardmaker:latest
    ```

=== ":material-microsoft-windows: Windows (Non-Powershell)"

    Change the value after the `=` to your local timezone, and the _tag_ after
    `titlecardmaker` to your tag (`latest` or `develop`)

    ```bash
    docker run -itd ^
        --net="bridge" ^
        -v "%cd%":"/config/" ^
        -e TZ="America/Los_Angeles" ^
        -p 4242:4242 ^
        --name "TitleCardMaker" ^
        titlecardmaker:latest
    ```

!!! success "Success"

    TitleCardMaker is now accessible at the `http://0.0.0.0:4242` or
    `http://localhost:4242/` URL.

??? failure "Interface not accessible?"

    If your logs (Docker or TCM at `/config/logs/maker.log`) shows

    ```log
    INFO:     Application startup complete.
    ```
    
    And neither the `http://0.0.0.0:4242` or `http://localhost:4242` URL loads
    the TCM UI, then replace the `0.0.0.0` part of the previous command with
    your _local_ IP address - e.g. `192.168.0.10`. If you still have issues,
    reach out on the Discord.
