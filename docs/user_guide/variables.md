---
title: Available Variables
description: >
    All available internal Title Card variables.
tags:
    - Series
---

# Available Variables

Throughout TCM, when something is referred to as a "format string", this means
that any of the internally defined variables can be used, allowing for more
fine-tuned customization. Accessing these variables is done by specifying the
variable name in curly brackets (`{}`), such as `{episode_number}`.

This page documents all the available variables.

## Variable Reference

For reference, each variable example is shown for the same hypothetical
[Episode](...).

=== "Inherent Metadata"

    | Variable Name             | Description             | Example                |
    | ------------------------- | ----------------------- | ---------------------- |
    | `series_name`             | Name of the Series      | `Breaking Bad`         |
    | `series_full_name`        | Full name of the Series | `Breaking Bad (2008)`  |
    | `year`                    | Release year of the Series | `2008`              |
    | `season_number`           | Season number           | `2`                    |
    | `episode_number`          | Episode number          | `6`                    |
    | `absolute_number`         | Absolute episode number | `13`                   |
    | `absolute_episode_number` | The absolute number (if available), otherwise the episode number | `13` |
    | `airdate`                 | Episode airdate         | `2009-04-12`           |
    | `watched`                 | Whether the Episode is watched or not | `true`   |

=== "Text Variables"

    | Variable Name       | Description                          | Example     |
    | ------------------- | ------------------------------------ | ----------- |
    | `title`             | Original title of the Episode        | `Peekaboo`  |
    | `title_text`        | Formatted title text of the Card[^1] | `PEEKABOO`  |
    | `hide_season_text`  | Whether to hide season text          | `false`     |
    | `hide_episode_text` | Whether to hide episode text         | `false`     |
    | `season_text`       | The season text of the Card          | `Season 2`  |
    | `episode_text`      | The episode text of the Card         | `Episode 6` |

=== "Calculated Metadata"

    | Variable Name          | Description                                   | Example |
    | ---------------------- | --------------------------------------------- | ------- |
    | `season_episode_count` | Number of Episodes in the season              | `13`    |
    | `season_episode_max`   | Maximum episode number in the season          | `13`    |
    | `season_absolute_max`  | Maximum absolute episode number in the season | `20`    |
    | `series_episode_count` | Total number of Episodes in the Series        | `62`    |
    | `series_episode_max`   | Maximum episode number in the Series          | `16`    |
    | `series_absolute_max`  | Maximum absolute episode number in the Series | `62`    |

    !!! question "How do these differ?"

        At first glance, the maximum and count variables (like
        `season_episode_count` and `season_episode_max`) might appear the same
        (and in most cases they are), but for Series where Episodes are missing
        these two would differ.

        For example, if I had Episodes 3-10 of Breaking Bad in TCM,
        `season_episode_count` would be `8`, while `season_episode_max` would be
        10.

        The same logic is true for their absolute-number equivalents.

=== "Fonts"

    | Variable Name            | Description                | Example  |
    | ------------------------ | -------------------------- | -------- |
    | `font_color`             | Font color                 | `yellow` |
    | `font_file`              | File path to the font file | `/config/assets/fonts/0/Breaking Bad.ttf`   |
    | `font_size`              | Font size                  | `1.2`    |
    | `font_kerning`           | Font kerning               | `2.3`    |
    | `font_stroke_width`      | Font stroke width          | `1.0`    |
    | `font_interline_spacing` | Font interline spacing     | `0`      |
    | `font_interword_spacing` | Font interword spacing     | `20`     |
    | `font_vertical_shift`    | Font vertical shift        | `20`     |

=== "Files"

    | Variable Name | Description                   | Example |
    | ------------- | ----------------------------- | --------|
    | source_file   | File path to the Source Image | `/config/source/Breaking Bad (2008)/s2e6.jpg` |
    | card_file     | File path to the Title Card   | `/config/cards/Breaking Bad (2008)/Season 2/Breaking Bad (2008) - S02E06.jpg` |

=== "Database IDs"

    | Variable Name        | Description               | Example             |
    | -------------------- |-------------------------- | ------------------- |
    | `series_emby_id`     | Emby ID of the Series     | `0:TV Shows:abcdef` |
    | `series_imdb_id`     | IMDb ID of the Series     | `tt0903747`         |
    | `series_jellyfin_id` | Jellyfin ID of the Series | `1:TV:def0123`      |
    | `series_sonarr_id`   | Sonarr ID of the Series   | `3:25`              |
    | `series_tmdb_id`     | TMDb ID of the Series     | `1396`              |
    | `series_tvdb_id`     | TVDb ID of the Series     | `81189`             |
    | `series_tvrage_id`   | TV Rage ID of the Series  | `18164`             |
    | `episode_emby_id`    | Emby ID of the Episode    | `0:TV Shows:993981` |
    | `episode_imdb_id`    | IMDb ID of the Episode    | `tt1232253`         |
    | `episode_jellyfin_id`| Emby ID of the Episode    | `1:TV:9d9da`        |
    | `episode_tmdb_id`    | TMDb ID of the Episode    | `62097`             |
    | `episode_tvdb_id`    | TVDb ID of the Episode    | `438917`            |
    | `episode_tvrage_id`  | TV Rage ID of the Episode | `710919`            |

    !!! note "Emby, Jellyfin, and Sonarr IDs"

        The IDs of Emby, Jellyfin, and Sonarr are all unique to your server(s)
        and libraries.

=== "Internal Data"

    | Variable Name | Description                            | Example     |
    | ------------- | -------------------------------------- | ----------- |
    | `extras`      | Any assigned extras                    | _See below_ |
    | `NEWLINE`     | A character to move text to a new line | `\n`      |

    Any assigned extras are added as their variable name. For example, if I
    specify the "Episode Text Color" extra for the Series, then the variable
    `episode_text_color` would provided. This can be used to add arbitrary extra
    data to a Card.

## Function Reference

In addition to defining many variables which can be used, TCM also implements
many functions which allow for more customization. Each is described below.

| Function Name | Description | Example |
| --- | --- | --- |
| `to_roman_numeral()` | Convert the given number to a roman numeral | `{to_roman_numeral(episode_number)}` |

[^1]: This is _after_ any Font replacements, font case functions, and line
splitting.