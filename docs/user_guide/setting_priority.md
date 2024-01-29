---
title: Setting Priority
description: >
    Relative priority of all Settings.
---

# Setting Priority

TitleCardMaker allows for specification of settings in a tiered system of
increasing specificity. This means that many settings can be specified in
multiple places, and TCM will only choose the highest priority option when
actually taking actions.

There are two "levels" under which settings are evaluated - these are on the
Series- and Episode-level. In general these are pretty self explanatory - for
example: the [Episode Data Source](./settings.md#episode-data-source) setting is
only evaluated per-Series (because an individual Episode cannot have a separate
data source); while a Card setting like Font color is evaluated per-Episode.

The following priority is listed below in _ascending_ order, meaning elements at
the top of the list will __always__ take priority of those below them.

!!! tip "Tip to Remember Priority"

    Rather than referring to or remembering the following list, it's easiest to
    remember that settings are overwritten in _increasing specificity_. Meaning
    the more specific a setting, the higher priority.

1. Episode extras
2. Episode Template extras
3. Series extras
4. Series Template extras
5. Episode settings
6. Episode Named Font settings
7. Episode Template settings[^1]
8. Series settings
9. Series Named Font settings
10. Series Template settings[^1]
11. Global settings
12. Card default settings

[^1]: This includes any Named Font assigned to the Template.