---
title: Docker Compose
description: >
    Compose file to run TitleCardMaker in a Docker container.
---

# Docker Compose

Below is a reference Docker compose snippet which can be modified to launch
TitleCardMaker via `docker -compose up`. Lines which should be reviewed and
modified are highlighted.

```yaml linenums="1" hl_lines="4 8 10-12 19-23"
version: '2' # Or 3
services:
  titlecardmaker:
    image: 'collinheist/titlecardmaker:latest' # (1)!
    container_name: TitleCardMaker
    network_mode: bridge
    volumes:
      - '"/docker/titlecardmaker/":/config/:rw' # (2)!
    environment:
      - PGID=99 # (3)!
      - PUID=100 # (4)!
      - TZ=America/Los_Angeles # (5)!
    ports:
      - '4242:4242'
    restart: unless-stopped
    stdin_open: true
    tty: true
    # (6)!
    # depends_on:
    #   - sonarr
    #   - plex
    #   - emby
    #   - jellyfin
```

1. Choose `:latest` or `:develop`. For most users, I recommend the default
`latest` branch. See [here](./docker.md#selecting-a-tag) for details.

2. Change `"/docker/titlecardmaker"` to _your_ install directory and leave the
`/config/:rw` part as-is.

3. Change this to your group ID. Likely the same GID as your Media Server or
Sonarr container(s).

4. Change this yo your user ID. Likely the same GID as your Media Server or
Sonarr container(s).

5. Change this to your timezone. See
[here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) in the
_TZ Identifier_ column for a reference list.

6. Uncomment these lines as needed __if__ you want the TitlecardMaker container
to be dependant upon these services (for a cleaner boot).
