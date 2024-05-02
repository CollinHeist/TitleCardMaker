---
title: Custom Card Types
description: >
    An overview of all the kinds of supported card types.
---

# Custom Card Types

!!! warning "Under Construction"

    This documentation is actively being developed.

## Background

In addition to customizing individual parts of a Title Card like the text,
styling, and font, TitleCardMaker is designed to support multiple different
types of Title Cards. These different types vary in more fundamental ways such
as layout, text placement, and additional features.

There are three different categories of card types:

Built-in

:   Card types developed by yours truly and shipped as part of TitleCardMaker.
    These types are typically the most thoroughly tested and support all the
    features of TitleCardMaker.

User-made

:   Cards developed by users of TCM who have taken the effort to make these
    available for others. These cards are not officially maintained, and so are
    not guaranteed to support all features. These are downloaded while TCM is
    running from the
    [card types repository](https://github.com/CollinHeist/TitleCardMaker-CardTypes).

Local

:   Cards as Python files that exist on your local machine and are only
    available to yourself. These are read and loaded dynamically when TCM
    launches (and periodically after that). These can be used to test cards as
    they are being developed, but do require a little but of Python knowledge.

## Built-in Cards

TitleCardMaker currently has the following built-in card types:

| Card Type                         | Preview                                            |
| :-------------------------------: | :------------------------------------------------: |
| [Anime](./anime.md)               | <img src="./assets/anime.webp" width="400">        |
| [Music](./music.md)               | <img src="./assets/music.webp" width="400">        |
| [Notification](./notification.md) | <img src="./assets/notification.webp" width="400"> |
| [Striped](./striped.md)           | <img src="./assets/striped.webp" width="400">      |

## User-made Cards

...

## Local Cards

The details of developing local card types is described [here](./local.md).
