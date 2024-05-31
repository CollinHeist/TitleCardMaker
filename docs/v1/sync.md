---
title: Sync (v1)
description: >
    How to set up syncing within TCM to automatically add Series.
---

# Syncing

## Background

This is an optional subsection of the `emby`, `jellyfin`, `plex`, or `sonarr`
sections of your [global preferences file](...) (`preferences.yml`). The
TitleCardMaker can automatically create/update [series YAML files](...) so that
cards can be created for series within Emby, Jellyfin, Plex, or Sonarr
_automatically_, without the need to add all your series manually. This behavior
is disabled by default.

!!! note "Note"

    It can be useful to just run the sync functionality of TCM while you first
    set it up. To do this without starting the main TCM loop, use `--sync` in
    your `main.py` command - this is described
    [here](...).

## Recommended Setup

Syncing can be specified for Emby, Jellyfin, Plex, and/or Sonarr, with the only
differences being speed (Emby, Jellyfin, and Plex being much slower than
Sonarr), and that Sonarr has more flexibility for syncing/excluding series type.
The basic functionality is otherwise identical, and all of them can even be set
up at once.

Below are recommended setups that work for 99% of users if you change the paths
and library names to match your setup.

=== "Docker"

    === "Emby"

        ```yaml title="preferences.yml" hl_lines="11-18"
        options:
          source: /config/source/
          series: # (4)!
            - /config/sync_anime.yml
            - /config/sync_tv.yml

        emby:
          url: # (1)!
          api_key: # (2)!
          username: # (3)!
          sync:
            - card_directory: /config/cards
            - file: /config/sync_anime.yml
                libraries:
                - Anime
            - file: /config/sync_tv.yml
                libraries:
                - TV
        ```

        1. Replace with your URL
        2. Replace with your API key
        3. Replace with your username
        4. Notice how the files listed here match the file names listed in the
        `sync` section.

    === "Jellyfin"

        ```yaml title="preferences.yml" hl_lines="11-18"
        options:
          source: /config/source/
          series: # (4)!
            - /config/sync_anime.yml
            - /config/sync_tv.yml

        jellyfin:
          url: # (1)!
          api_key: # (2)!
          username: # (3)!
          sync:
            - card_directory: /config/cards
            - file: /config/sync_anime.yml
                libraries:
                - Anime
            - file: /config/sync_tv.yml
                libraries:
                - TV
        ```

        1. Replace with your URL
        2. Replace with your API key
        3. Replace with your username
        4. Notice how the files listed here match the file names listed in the
        `sync` section.

    === "Plex"

        ```yaml title="preferences.yml" hl_lines="10-17"
        options:
          source: /config/source/
          series: # (3)!
            - /config/sync_anime.yml
            - /config/sync_tv.yml

        plex:
          url: # (1)!
          token: # (2)!
          sync:
            - card_directory: /config/cards
            - file: /config/sync_anime.yml
                libraries:
                - Anime
            - file: /config/sync_tv.yml
                libraries:
                - TV
        ```

        1. Replace with your URL
        2. Replace with your X-Plex-Token
        3. Notice how the files listed here match the file names listed in the
        `sync` section.

    === "Sonarr"

        ```yaml title="preferences.yml" hl_lines="10-20"
        options:
          source: ./config/source/
          series: # (4)!
            - ./config/sync_anime.yml
            - ./config/sync_tv.yml

        sonarr:
          url: # (1)!
          api_key: # (2)!
          sync:
            - card_directory: /config/cards/
                downloaded_only: true
                monitored_only: true
                plex_libraries: # (3)!
                  /media/tv: TV
                  /media/anime: Anime
            - file: /config/sync_anime.yml
                series_type: anime
            - file: /config/sync_tv.yml
                series_type: standard
        ```

        1. Replace with your URL
        2. Replace with your API key
        3. Replace with your root Sonarr library paths
        4. Notice how the files listed here match the file names listed in the
        `sync` section.

=== "Non-Docker"

    !!! note "Window Paths"

        All paths shown below use the Unix-type pathing (e.g. forward slashes
        `/`) - this should work on Windows machines, but I strongly recommend
        Windows users use the Windows-type pathing (e.g. backslashes `\`).

    === "Emby"

        ```yaml title="preferences.yml" hl_lines="5-12"
        options:
          source: ./config/source/
          series: # (4)!
            - ./config/sync_anime.yml
            - ./config/sync_tv.yml

        emby:
          url: # (1)!
          api_key: # (2)!
          username: # (3)!
          sync:
            - card_directory: ./config/cards
            - file: ./config/sync_anime.yml
                libraries:
                - Anime
            - file: ./config/sync_tv.yml
                libraries:
                - TV
        ```

        1. Replace with your URL
        2. Replace with your API key
        3. Replace with your username
        4. Notice how the files listed here match the file names listed in the
        `sync` section.

    === "Jellyfin"

        ```yaml title="preferences.yml" hl_lines="11-18"
        options:
          source: ./config/source/
          series: # (4)!
            - ./config/sync_anime.yml
            - ./config/sync_tv.yml

        jellyfin:
          url: # (1)!
          api_key: # (2)!
          username: # (3)!
          sync:
            - card_directory: ./config/cards
            - file: ./config/sync_anime.yml
                libraries:
                - Anime
            - file: ./config/sync_tv.yml
                libraries:
                - TV
        ```

        1. Replace with your URL
        2. Replace with your API key
        3. Replace with your username
        4. Notice how the files listed here match the file names listed in the
        `sync` section.

    === "Plex"

        ```yaml title="preferences.yml" hl_lines="10-17"
        options:
          source: ./config/source/
          series: # (3)!
            - ./config/sync_anime.yml
            - ./config/sync_tv.yml

        plex:
          url: # (1)!
          token: # (2)!
          sync:
            - card_directory: ./config/cards
            - file: ./config/sync_anime.yml
              libraries:
                - Anime
            - file: ./config/sync_tv.yml
              libraries:
                - TV
        ```

        1. Replace with your URL
        2. Replace with your X-Plex-Token
        3. Notice how the files listed here match the file names listed in the
        `sync` section.

    === "Sonarr"

        ```yaml title="preferences.yml" hl_lines="10-20"
        options:
          source: ./config/source/
          series: # (4)!
            - ./config/sync_anime.yml
            - ./config/sync_tv.yml

        sonarr:
          url: # (1)!
          api_key: # (2)!
          sync:
            - card_directory: ./config/cards/
                downloaded_only: true
                monitored_only: true
                plex_libraries: # (3)!
                  /media/tv: TV
                  /media/anime: Anime
            - file: ./config/sync_anime.yml
              series_type: anime
            - file: ./config/sync_tv.yml
              series_type: standard
        ```

        1. Replace with your URL
        2. Replace with your API key
        3. Replace with your root Sonarr library paths
        4. Notice how the files listed here match the file names listed in the
        `sync` section.

## Syncing Multiple Files

Multiple series YAML files _can_ be synced at once. To enable this, the sync
must be specified as a _list_. If done, the item specified first will apply to
all subsequent syncs. This is implemented to avoid having to repeatedly specify
anything.

!!! example "Example"

    ```yaml
    options:
      source: ./config/source/
      series:
        - ./config/sync_file_1.yaml
        - ./config/sync_file_2.yaml

    sync:
      # (1)!
      - mode: append
        volumes:
          /docker/tv/: /tcm/tv/

      - file: ./config/sync_file_1.yaml
        add_template: template_1

      - file: ./config/sync_file_2.yaml
        exclusions:
      - series: Breaking Bad (2008)
        mode: sync
    ```

    1. Since there is no `file` specified, this will not result in any syncing.
    Since this is the first item in the list, `mode` and `volumes` will be
    carried over to the following syncs.

## Attributes

!!! note "Note"

    The Emby, Jellyfin, Plex, and Sonarr columns indicate whether that option
    _can_ be specified for that interface. No options are required.

| Name                                              | YAML              | Allowed Values                  | Default  | Emby, Jellyfin, Plex                       | Sonarr                                     |
| :-----------------------------------------------: | :---------------: | :-----------------------------: | :------: | :----------------------------------------: | :----------------------------------------: |
| [YAML File](#yaml-file)                           | `file`            | Any valid file                  | -        | :fontawesome-regular-circle-check:{.green} | :fontawesome-regular-circle-check:{.green} |
| [Sync Mode](#sync-mode)                           | `mode`            | `append` or `match`             | `append` | :fontawesome-regular-circle-check:{.green} | :fontawesome-regular-circle-check:{.green} |
| [Compact Mode](#compact-mode)                     | `compact_mode`    | `true` or `false`               | `true`   | :fontawesome-regular-circle-check:{.green} | :fontawesome-regular-circle-check:{.green} |
| [Card Directory](#card-directory)                 | `card_directory`  | Any valid path                  | -        | :fontawesome-regular-circle-check:{.green} | :fontawesome-regular-circle-check:{.green} |
| [Template](#template)                             | `add_template`    | Any template name               | -        | :fontawesome-regular-circle-check:{.green} | :fontawesome-regular-circle-check:{.green} |
| [Filter Downloaded Only](#filter-downloaded-only) | `downloaded_only` | `true` or `false`               | `false`  | :fontawesome-regular-circle-xmark:{.red}   | :fontawesome-regular-circle-check:{.green} | 
| [Filter Monitored Only](#filter-monitored-only)   | `monitored_only`  | `true` or `false`               | `false`  | :fontawesome-regular-circle-xmark:{.red}   | :fontawesome-regular-circle-check:{.green} | 
| [Required Tags](#required-tags)                   | `required_tags`   | A list of any tags              | -        | :fontawesome-regular-circle-check:{.green} | :fontawesome-regular-circle-check:{.green} |
| [Filter Libraries](#filter-libraries)             | `libraries`       | A list of any library names     | -        | :fontawesome-regular-circle-check:{.green} | :fontawesome-regular-circle-xmark:{.red}   |
| [Series Type](#series-type)                       | `series_type`     | `anime`, `daily`, or `standard` | -        | :fontawesome-regular-circle-xmark:{.red}   | :fontawesome-regular-circle-check:{.green} | 
| [Docker Volumes](#docker-volumes)                 | `volumes`         | _See below_                     | -        | :fontawesome-regular-circle-check:{.green} | :fontawesome-regular-circle-check:{.green} |
| [Plex Libraries](#plex-libraries)                 | `plex_libraries`  | _See below_                     | -        | :fontawesome-regular-circle-xmark:{.red}   | :fontawesome-regular-circle-check:{.green} | 
| [Exclusions](#exclusions)                         | `exclusions`      | A list of any excluded entries  | -        | :fontawesome-regular-circle-check:{.green} | :fontawesome-regular-circle-check:{.green} |

Each of these options is explained in greater detail below.

### YAML File (`file`) { data-toc-label="YAML File" }

The filepath that the Maker should create/modify with series YAML.

!!! warning "File is not automatically read"

    Specifying a file here __does not__ mean that TCM will create title cards
    for it - the file must also be listed as a YAML file in the `options`
    `series` setting.

### Mode (`mode`) { data-toc-label="Mode" }

The mode in which the Maker should write/update the specified
[YAML file](#yaml-file). `append` mode will look at the file and skip and not
modify any series/libraries that are already defined; while `match` mode will
also remove series that are not present in the synced interface/filter (see
below for details).

??? example "Example"

    If syncing to Plex and `match` mode is indicated, if a series is _deleted_
    from Plex, the entry in the synced file will also be removed. The same will
    happen if syncing to Sonarr, and a series is removed from Sonarr, untagged,
    or otherwise changed to no longer be in the sync.

### Compact Mode (`compact_mode`) { data-toc-label="Compact Mode" }

Whether the Maker should write the series YAML in "compact" mode or not. This is
entirely an aesthetic option, but can make scrolling through very long files (if
you have a lot of series being synced) much easier.

??? example "Example"

    If `#!yaml compact_mode: false` is specified, the YAML file will be
    formatted like this:

    ```yaml
    libraries:
      TV:
        path: /media/TV
    series:
      11.22.63 (2016):
        library: TV
      30 Rock (2006):
        library: TV
      American Vandal (2017):
        year: 2017
      Breaking Bad (2008):
        library: TV
    ```

    If `#!yaml compact_mode: true` is specified, these same series would be
    written as:

    ```yaml
    libraries:
      TV:
        path: /media/TV
    series:
      11.22.63 (2016): {library: TV}
      30 Rock (2006): {library: TV}
      American Vandal (2017): {library: TV}
      Breaking Bad (2008): {library: TV}
      # ...
    ```

### Card Directory (`card_directory`) { data-toc-label="Card Directory" }

Directory to put all title cards inside. This overrides any paths returned by
the source, and is _much_ easier if your folder structure is somewhat
complicated.

TCM can still load the cards into your server as long as you have set up your
library detection/assignment set up correctly. Storing the cards alongside the
media is not required.

### Template Name (`add_template`) { data-toc-label="Template Name" }

Optional [template](...) _name_ to add to all synced series. This does not
define or pass any arguments to the template, just specifies its name for the
series. See the example for more details.

??? example "Example"

    The following example specifies `my_template` for each synced series:

    ```yaml hl_lines="6"
    sonarr: 
      url: ...
      api_key: ...
      sync:
        file: ./yml/plex_sync.yml
        add_template: my_template
    ```

    Which, would result in `./yml/plex_sync.yml` (hypothetically) looking like:

    ```yaml
    templates: # Created by you, the user, NOT the sync
      my_template:
        card_type: roman
        archive: false
    series:
      11.22.63 (2016): {library: TV, template: my_template}
      30 Rock (2006): {library: TV, template: my_template}
      # ...
    ```

    Where the definition of `my_template` was added manually by the user.


### Filter Downloaded Only (`downloaded_only`) { data-toc-label="Filter Downloaded Only" }

!!! note "Sonarr Syncs Only"

    This is only applicable to `sonarr` syncs.

Whether to only sync series that have _any_ downloaded episodes within Sonarr.
If enabled (`#!yaml downloaded_only: true`), series with no episodes will be
rejected.

### Filter Monitored Only (`monitored_only`) { data-toc-label="Filter Monitored Only" }

!!! note "Sonarr Syncs Only"

    This is only applicable to `sonarr` syncs.

Whether to only sync series that are Monitored within Sonarr. If enabled
(`#!yaml monitored_only: true`), unmonitored series will be rejected.

### Required Tags (`required_tags`) { data-toc-label="Required Tags" }

List of tags to filter the synced series by. If specified, only series that have
_all_ of the provided tags will be synced. This must be specified as a _list_,
like so:

```yaml
required_tags:
- tag1
- tag2
```

Within Emby, Jellyfin, or Sonarr, these are "tags", and within Plex they are
called "Sharing labels".

??? example "Example"

    This will only sync series to the specified file that are tagged with both
    `dolby-vision` and `ongoing` will be written:

    ```yaml
    sonarr:
      url: ...
      api_key: ...
      sync:
        file: ./yaml/sonarr_sync.yml
        required_tags:
        - dolby-vision
        - ongoing
    ```

### Filter Libraries (`libraries`) { data-toc-label="Filter Libraries" }

!!! note "Emby, Jellyfin, and Plex Syncs Only"

    This is only applicable to `emby`, `jellyfin`, or `plex` syncs.

Libraries within Emby/Jellyfin/Plex to filter the synced series by. If
specified, only series that are within any of the listed libraries will be
synced. Otherwise, all series from all TV libraries will be synced.

This must be specified like a list, like so:

```yaml
libraries:
- TV
- TV 4K
```

### Series Type (`series_type`) { data-toc-label="Series Type" }

!!! note "Sonarr Syncs Only"

    This is only applicable to `sonarr` syncs.

The series type to filter the sync by. If specified, only series that match this
type will be synced. Otherwise, all series types will be synced. These are the
types assigned to a series within Sonarr.

The only accepted values are `anime`, `daily`, and `standard`.

### Docker Volumes

!!! warning "Not Recommended"

    This setting is fairly complicated and rarely needed. As such it is not
    recommended for most users.

If your instances of Emby/Jellyfin/Plex/Sonarr are running in a Docker
container, the reported media paths might not match TitleCardMaker. To
accommodate this, you can define the volumes you've mounted to the containers
and the Maker will substitute these paths to their Maker-equivalents. These
should be specified as `#!yaml server_path: tcm_path`, see the example for
details.

!!! note "Windows Paths"

    Windows users should specify their filepaths with forward-slashes, e.g.
    `C:\\Users\Documents\` should be written as `C:/Users/Documents`.

<details><summary>Example</summary>

If I have mounted `/documents/Media/` on my machine to `/media/` within the Plex docker container, and have then mounted `/documents/Media/` to `/libraries/media/` within the TitleCardMaker docker container, then the following would be a suitable volume specification:

```yaml
sonarr:
  url: ...
  api_key: ...
  sync:
    file: ./yaml/sonarr_sync.yml
    volumes:
      /documents/Media/: /libraries/Media/
```

</details>

### Plex Libraries

!!! note "Sonarr Syncs Only"

    This is only applicable to `sonarr` syncs.

If you've grouped your libraries by sub-folder, this section can define what paths within TCM should be assigned to which libraries. This needs to be specified as `{path}: {library name}`. This setting can be confusing if both Sonarr and TitleCardMaker are in Docker containers, see Example 2 for details.

These paths should be specified _before_ any replacements done by specifying any [docker volumes](#docker-volumes).

<details><summary>Example 1</summary>

If Sonarr puts my `TV` library at `/media/TV/`, and `Anime` library at `/media/Anime/`, then I want to define those two libraries here, like so:

```yaml
sonarr:
  url: ...
  api_key: ...
  sync:
    file: ./yaml/sonarr_sync.yml
    plex_libraries:
      /media/TV/: TV
      /media/Anime/: Anime
```

This means when Sonarr reports to TCM that a given series, such as Breaking Bad, is located at `/media/TV/Breaking Bad (2008)/` then TCM will be able to assign this series to the `TV` library automatically. 

</details>

<details><summary>Example 2</summary>

If Sonarr is in a Docker container and puts Media for the `TV` library at `/sonarr/media/TV/` and the `Anime` library at `/sonarr/media/Anime/`, and I've mounted these paths at `/maker/media/TV` and `/maker/media/Anime` in my TitleCardMaker container, then my `volumes` and `plex_libraries` specification should look like this:

```yaml
sonarr:
  url: ...
  api_key: ...
  sync:
    file: ./yaml/sonarr_sync.yml
    volumes:
      /sonarr/media/: /maker/media/
    plex_libraries:
      /sonarr/media/TV/: TV
      /sonarr/media/Anime/: Anime
```

This means that Sonarr reports a path like `/sonarr/media/TV/Breaking Bad (2008)/` to TCM. TCM then converts the `/sonarr/media/` portion of that path to with `/maker/media/`, becoming `/maker/media/TV/Breaking Bad (2008)/`. Finally, TCM looks at the specified libraries and matches `/sonarr/media/TV/` to the `TV` library, meaning this series will be assigned to the `TV` library. It then writes the _converted_ path into the sync file.

</details>

## Exclusions
A list of exclusions to not sync to the specified file. This can be useful if there are series you either don't want cards for, or have custom cards specified in another file. All series titles are excluded case _insensitively_.

There are three _types_ of exclusions, all are listed below:

| Exclusion Name | Description | Example |
| :---: | :---: | :--- |
| `series` | Full name of a series | `series: Breaking Bad (2008)` |
| `tag` | Tag | `tag: ignore_tag` |
| `yaml` | [Series YAML file](https://github.com/CollinHeist/TitleCardMaker/wiki/Series-YAML-Files) to exclude _all_ entries of<sup>1</sup> | `yaml: ./path/to/yaml_file.yml` |

> <sup>1</sup>This can be useful if you have many series to exclude, or you have a YAML file of customized cards that you don't want the sync to override. All entries in the given file's `series` will be ignored.

This _must_ be given as a list, like so:

```yaml
exclusions:
- series: ...
- tag: ...
- yaml: ...
```

<details><summary>Example of an excluded YAML file</summary>

If there are a lot of series you want to exclude - the most efficient way to do this is to create an excluded YAML file, and add it to your sync. An example of how this file might looks is:

```yaml
series:
  Beastars (2019): {}
  Dark (2017): {}
  "The Lord of the Rings: The Rings of Power (2022)": {}
  # etc.
```

Each 'entry' in the file must be under the `series` key (like a normal series YAML file), but there is no need to specify any actual "content" (e.g. custom fonts, card types, etc.) as TCM will just look at the _name_ of the series.

</details>
