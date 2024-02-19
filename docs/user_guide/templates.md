---
title: Templates
description: >
    Create, customize, and view Templates for bulk-editing settings.
tags:
    - Templates
---

# Templates

!!! warning "Under Construction"

    This documentation is actively being developed.

A Template is a set of custom settings and Card configurations that can be
assigned to multiple Series or Episodes at once. Mutliple Templates can be
assigned to a Series or Episode, and, with Filters, can be used to conditionally
apply setting changes. Templates can be viewed and edited at the Templates page
within TCM (the `/card-templates` URL).

An easy way to view Templates is that they allow you to group Card
customizations together so they can be easily edited en-masse without changing
each Series individually. The most common use-case is to develop a Template (or
a set of Templates) that applies to some subset of your Series - e.g. all anime,
or all documentaries - and apply those Templates automatically when
[Syncing](./syncs.md).

!!! example "Standard Example"

    By far the most common example of using a Template is for utilizing
    different card configurations for anime and non-anime cards. Creating an
    anime Template which overrides the card type, adds translations, and
    potentially adds absolute episode numbering allows for easily maintaining
    two very separate card looks. 

Some widely used Templates can be found [here](...).

## Template Priority

One key feature of Templates is the ability to assign more than one to a Series
or Episode and implement a priority system using [Filters](#filters).

Whenever a Template is assigned, TCM evaluates whether that Template should be
applied to whatever operation it is performing. It does this by looking at the
assigned [Filters](#filters); and the first Template whose Filter conditions are
all met will be utilized.

Within the UI, Templates are __always__ displayed in order. Meaning the first
Template listed in the dropdown of a Sync, Series, or Episode is the highest
priority Template.

## Creating a New Template

At the top of the Templates page, a new Template can be created by clicking the
<span class="example md-button">Create New Template</span> button. This will
create a "blank" Template.

Clicking the accordion will expand the Template, where all customization can be
entered.

## Previews

On the right-hand side of all Templates are 'live' previews of the current
Template. This preview reflects the currently entered settings - not necessarily
what is saved - and can be refreshed by clicking the
<span class="example md-button">:material-refresh: Refresh Preview</span> button.

## Customization

All Templates have the following options which can be adjusted:

- ...

Each of these is described in greater detail below. All values can be left
blank - if blank, TCM will use the next highest priority setting from the
Series, Episode, or global setting. Setting priorities are listed
[here](./setting_priority.md).

### Name

A Template's name is purely for easier selection within the TCM UI. If you are
using [Tiered](#template-priority) Templates, it is recommended to include the
relative priority of the Template in the name - e.g. _Tier 1 - Unwatched Anime_,
or _Tier 0 - All Anime_.

!!! note "Importing Blueprint Templates"

    The name of a Template is also used to match Templates when importing
    [Blueprints](../blueprints.md).
    
    For example - if you are importing a Blueprint featuring a Template named
    _Anime_ and have already created a Template named _Anime_, then TCM will not
    duplicate the Template and instead just assign the existing Template to the
    Series.

    This is relatively uncommon, as Templates are not typically included in
    Blueprints.

### Filters

Filters are a critical component of utilizing different
[priority](#template-priority) Templates for more fine-tuned customization. A
Template can have any number of Filters, and all Filters must be true (or
unevaluatable) for a Template to be applied.

Each condition of a Filter is made up of 3 parts. An _Argument_, which is the
variable pulled from the specific Series or Episode being evaluated; an
_Operation_ which is what operation is being applied to the _Argument_; and a
_Reference Value_ which is what the result of the evaluation is compared
against. To remove a condition, clear its Operation (the middle column).

!!! example "Example"

    To add a Filter condition which only applies to unwatched pilots (season 1
    episode 1 of a Series), you would create the following conditions:

    | Argument                 | Operation  | Reference Value |
    | ------------------------ | ---------- | --------------- |
    | `Season Number`          | `equals`   | `1`             |
    | `Episode Number`         | `equals`   | `1`             |
    | `Episode Watched Status` | `is false` |                 |

    Note that there is no reference value for the `Episode Watched Status`
    condition, as the `is false` operation does not need to reference another
    value.

If you enter some invalid condition - like a bad reference value, or a
nonsensical operation - then the condition is skipped (which is the same as
being true).

!!! tip "Optimal Filter Ordering"

    If you'd like to make marginal perfomance improvements, it is best practice
    to put conditions which are more likely to fail - i.e. the more restrictive
    conditions - first, as this short-circuits the Filter evaluation logic.

    For example, putting a condition for `Episode Number` `equals` _before_
    `Season Number` `equals` would be ideal since more failures will occur on
    the Episode number condition than the season number condition.

Below is a summary of all Filter arguments, their valid operations, a
description of what this Filter accomplishes, and whether it requires a
reference value.

!!! note "All Supported Filter Conditions[^1]"

    === "Series Name"

        | Operation | Description | Reference Value |
        | --------: | :---------- | :-------------: |
        | equals | Only apply to Series of the given name | :fontawesome-regular-circle-check:{.green} |
        | does not equal | Do not apply to Series of the given name | :fontawesome-regular-circle-check:{.green} |
        | starts with | Only apply to Series whose name starts with the given text | :fontawesome-regular-circle-check:{.green} |
        | does not start with | Do not apply to Series whose name starts with the given text | :fontawesome-regular-circle-check:{.green} |
        | ends with | Only apply to Series whose name ends with the given text | :fontawesome-regular-circle-check:{.green} |
        | does not end with | Do not apply to Series whose name ends with the given text | :fontawesome-regular-circle-check:{.green} |
        | contains | Only apply to Series whose name contains the given text | :fontawesome-regular-circle-check:{.green} |
        | does not contain | Do not apply to Series whose name contains the given text | :fontawesome-regular-circle-check:{.green} |
        | matches | Only apply to Series whose name matches the given regex | :fontawesome-regular-circle-check:{.green} |
        | does not match | Do not apply to Series whose name matches the given regex | :fontawesome-regular-circle-check:{.green} |

    === "Series Year"

        The `is before` and `is after` conditions  cannot be used with a Series
        Year argument; see the Episode Airdate argument, or use the math
        operations (less than, greater than, etc.).
    
        | Operation | Description | Reference Value |
        | --------: | :---------- | :-------------: |
        | equals | Only apply to Series whose year is exactly the given number | :fontawesome-regular-circle-check:{.green} |
        | does not equal | Do not apply to Series whose year is exactly the given number | :fontawesome-regular-circle-check:{.green} |
        | matches | Only apply to Series whose year matches the given regex | :fontawesome-regular-circle-check:{.green} |
        | does not match | Do not apply to Series whose year matches the given regex | :fontawesome-regular-circle-check:{.green} |
        | is less than | Only apply to Series whose year is less than the given number | :fontawesome-regular-circle-check:{.green} |
        | is less than or equal | Only apply to Series whose year is less than or equal to the given number | :fontawesome-regular-circle-check:{.green} |
        | is greater than | Only apply to Series whose year is greater than the given number | :fontawesome-regular-circle-check:{.green} |
        | is greater than or equal | Only apply to Series whose year is greater than or equal to the given number | :fontawesome-regular-circle-check:{.green} |

    === "Number of Seasons"

        The Number of Seasons argument _only_ counts Episodes which are in TCM.

        | Operation | Description | Reference Value |
        | --------: | :---------- | :-------------: |
        | equals | Only apply to Series with exactly the given number of seasons | :fontawesome-regular-circle-check:{.green} |
        | does not equal | Do not apply to Series with exactly the given number of seasons | :fontawesome-regular-circle-check:{.green} |
        | is less than | Only apply to Series whose number of seasons is less than the given number | :fontawesome-regular-circle-check:{.green} |
        | is less than or equal | Only apply to Series whose number of seasons is less than or equal to the given number | :fontawesome-regular-circle-check:{.green} |
        | is greater than | Only apply to Series whose number of seasons is greater than the given number | :fontawesome-regular-circle-check:{.green} |
        | is greater than or equal | Only apply to Series whose number of seasons is greater than or equal to the given number | :fontawesome-regular-circle-check:{.green} |

    === "Series Library Names"

        Library names are evaluated as a list of all assigned libraries, meaning
        the full library name must be specified to filter on this argument. For
        example, if I had a Series assigned to the `Anime HD` and `Anime 4K`
        libraries, the reference value `Anime` would __not__ match either of
        these. The entire name, such as `Anime HD` would be required.

        | Operation | Description | Reference Value |
        | --------: | :---------- | :-------------: |
        | contains | Only apply to Series with a library of the given name | :fontawesome-regular-circle-check:{.green} |
        | does not contain | Do not apply to Series with a library of the givens name | :fontawesome-regular-circle-check:{.green} |

    === "Series Logo"

        This Filter condition only looks at the _default_ Series logo - e.g.
        `logo.png` within the source directory.

        | Operation | Description | Reference Value |
        | --------: | :---------- | :-------------: |
        | file exists | Only apply to Series whose logo exists | :fontawesome-regular-circle-xmark:{.red} |

    === "Reference File"

        This Filter condition can be used with [Variables](./variables.md) to
        dynamically apply a Template based on the existence of some file, such
        as a poster, per-season logo, etc.

        | Operation | Description | Reference Value |
        | --------: | :---------- | :-------------: |
        | file exists | Only apply to Series where the indicated File exists | :fontawesome-regular-circle-check:{.green} |

    === "Episode Watched Status"

        Watched statuses are evaluated per-library (even if
        [Multi-Library mode](./settings.md#multi-library-filename-support) is
        disabled).

        | Operation | Description | Reference Value |
        | --------: | :---------- | :-------------: |
        | is true | Only apply to Episodes that have been watched | :fontawesome-regular-circle-xmark:{.red} |
        | is false | Do not apply to Episode that have been watched | :fontawesome-regular-circle-xmark:{.red} |
        | is null | Only apply to Episode whose watched status is unknown[^2] | :fontawesome-regular-circle-xmark:{.red} |
        | is not null | Only apply to Episode whose watched status is known[^2] | :fontawesome-regular-circle-xmark:{.red} |

    === "Season Number"

        | Operation | Description | Reference Value |
        | --------: | :---------- | :-------------: |
        | is true | Only apply to Episodes that are not part of season 0 | :fontawesome-regular-circle-xmark:{.red} |
        | equals | Only apply to Episodes with exactly the given season number | :fontawesome-regular-circle-check:{.green} |
        | does not equal | Do not apply to Episodes with exactly the given season number | :fontawesome-regular-circle-check:{.green} |
        | is less than | Only apply to Episodes whose season number is less than the given number | :fontawesome-regular-circle-check:{.green} |
        | is less than or equal | Only apply to Episodes whose season number is less than or equal to the given number | :fontawesome-regular-circle-check:{.green} |
        | is greater than | Only apply to Episodes whose season number is greater than the given number | :fontawesome-regular-circle-check:{.green} |
        | is greater than or equal | Only apply to Episodes whose season number is greater than or equal to the given number | :fontawesome-regular-circle-check:{.green} |

    === "Episode Number"

        | Operation | Description | Reference Value |
        | --------: | :---------- | :-------------: |
        | equals | Only apply to Episodes with exactly the given episode number | :fontawesome-regular-circle-check:{.green} |
        | does not equal | Do not apply to Episodes with exactly the given episode number | :fontawesome-regular-circle-check:{.green} |
        | is less than | Only apply to Episodes whose episode number is less than the given number | :fontawesome-regular-circle-check:{.green} |
        | is less than or equal | Only apply to Episodes whose episode number is less than or equal to the given number | :fontawesome-regular-circle-check:{.green} |
        | is greater than | Only apply to Episodes whose episode number is greater than the given number | :fontawesome-regular-circle-check:{.green} |
        | is greater than or equal | Only apply to Episodes whose episode number is greater than or equal to the given number | :fontawesome-regular-circle-check:{.green} |

    === "Absolute Number"

        !!! tip "Special Variable"

            The variable `{absolute_episode_number}` can be used in episode text
            format strings (and other locations) which will use the absolute
            episode number _if available_, and the normal episode number,
            otherwise.

        | Operation | Description | Reference Value |
        | --------: | :---------- | :-------------: |
        | is null | Only apply to Episodes with no absolute episode number | :fontawesome-regular-circle-xmark:{.red} |
        | is not null | Only apply to episodes with an absolute episode number | :fontawesome-regular-circle-xmark:{.red} |
        | equals | Only apply to Episodes with exactly the given absolute episode number | :fontawesome-regular-circle-check:{.green} |
        | does not equal | Do not apply to Episodes with exactly the given absolute episode number | :fontawesome-regular-circle-check:{.green} |
        | is less than | Only apply to Episodes whose absolute episode number is less than the given number | :fontawesome-regular-circle-check:{.green} |
        | is less than or equal | Only apply to Episodes whose absolute episode number is less than or equal to the given number | :fontawesome-regular-circle-check:{.green} |
        | is greater than | Only apply to Episodes whose absolute episode number is greater than the given number | :fontawesome-regular-circle-check:{.green} |
        | is greater than or equal | Only apply to Episodes whose absolute episode number is greater than or equal to the given number | :fontawesome-regular-circle-check:{.green} |

    === "Episode Title"

        | Operation | Description | Reference Value |
        | --------: | :---------- | :-------------: |
        | equals | Only apply to Episodes whose title is exactly some text | :fontawesome-regular-circle-check:{.green} |
        | does not equal | Do not apply to Episodes whose title is exactly some text | :fontawesome-regular-circle-check:{.green} |
        | starts with | Only apply to Episodes whose title starts with some text | :fontawesome-regular-circle-check:{.green} |
        | does not start with | Do not apply to Episodes whose title starts with some text | :fontawesome-regular-circle-check:{.green} |
        | ends with | Only apply to Episodes whose title ends with some text | :fontawesome-regular-circle-check:{.green} |
        | does not end with | Do not apply to Episodes whose title ends with some text | :fontawesome-regular-circle-check:{.green} |
        | contains | Only apply to Episodes whose title contains some text | :fontawesome-regular-circle-check:{.green} |
        | does not contain | Do not apply to Episodes whose title contains some text | :fontawesome-regular-circle-check:{.green} |
        | matches | Only apply to Episodes whose title matches some regex | :fontawesome-regular-circle-check:{.green} |
        | does not match | Do not apply to Episodes whose title matches some regex | :fontawesome-regular-circle-check:{.green} |

    === "Episode Title Length"

        | Operation | Description | Reference Value |
        | --------: | :---------- | :-------------: |
        | equals | Only apply to Episodes whose title length is exactly the given number | :fontawesome-regular-circle-check:{.green} |
        | does not equal | Do not apply to Episodes whose title length is exactly the given number | :fontawesome-regular-circle-check:{.green} |
        | is less than | Only apply to Episodes whose title length is less than the given number | :fontawesome-regular-circle-check:{.green} |
        | is less than or equal | Only apply to Episodes whose title length is less than or equal to the given number | :fontawesome-regular-circle-check:{.green} |
        | is greater than | Only apply to Episodes whose episode title length is greater than the given number | :fontawesome-regular-circle-check:{.green} |
        | is greater than or equal | Only apply to Episodes whose episode title length is greater than or equal to the given number | :fontawesome-regular-circle-check:{.green} |

    === "Episode Airdate"

        All airdate reference values must be entered as `YYYY-MM-DD` - e.g.
        `2023-12-30`.

        | Operation | Description | Reference Value |
        | --------: | :---------- | :-------------: |
        | is null | Only apply to Episodes with no airdate | :fontawesome-regular-circle-xmark:{.red} |
        | is not null | Do not apply to Episodes with airdates | :fontawesome-regular-circle-xmark:{.red} |
        | is before | Only apply to Episodes which aired before the given date | :fontawesome-regular-circle-check:{.green} |
        | is after | Only apply to Episodes which aired after the given date | :fontawesome-regular-circle-check:{.green} |

    === "Episode Extras"

        | Operation | Description | Reference Value |
        | --------: | :---------- | :-------------: |
        | is null | Only apply to Episodes with no extras | :fontawesome-regular-circle-xmark:{.red} |
        | is not null | Do not apply to Episodes with any extras | :fontawesome-regular-circle-xmark:{.red} |
        | contains | Only apply to Episodes with extras of the given label | :fontawesome-regular-circle-check:{.green} |
        | does not contain | Do not apply to Episodes with extras of the given label | :fontawesome-regular-circle-check:{.green} |

### Card Type

The card type to apply as part of this Template.

### Font

A [Named Font](./fonts.md) to apply as part of this Template.

### Watched and Unwatched Episode Style

How to [stylize](./settings.md#watched-and-unwatched-episode-styles) watched
and unwatched Episodes as part of this Template.

### Hide Season Titles

Whether to hide season titles as part of this Template.

### Season Titles




[^1]: Argument and operation pairs which are meaningless (but technically
valid) - e.g. `Series Name` `is greater than` `...` - are not listed. Many of
these are either always true or always false, but hold no real meaning.

[^2]: An Episode's watched status is unknown if the Episode cannot be found
in an associated Media Server within the specified library.
