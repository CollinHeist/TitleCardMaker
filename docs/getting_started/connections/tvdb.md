---
title: Connecting to TVDb
description: >
    How to connect TitleCardMaker to The TV Database (TVDb).
tags:
    - Tutorial
    - TVDb
---

# ![TVDb Logo](./assets/tvdb-light.png#only-light){.no-lightbox .twemoji} ![TVDb Logo](./assets/tvdb-dark.png#only-dark){.no-lightbox .twemoji} The TV Database

!!! info "Optional Step"

    This step is optional for all users.

The TV Database (hereafter referred to as TVDb for brevity) is a free,
publicly accessible database which can serve as an
[Episode Data Source](../../user_guide/settings.md#episode-data-source) and 
[Image Source](../../user_guide/settings.md#image-source-priority).

1. Under the TVDb section, click the
<span class="example md-button">Add Connection</span> button.

2. Click the external link :octicons-link-external-16: icon next to _API Key_
and open the TVDb [API](https://thetvdb.com/api-information) page.

3. Follow their instructions to generate an API key for yourself (this will
require a TVDb account). Copy the generated API key.

    ??? danger "Security Warning"

        Keep this API key private, as it can be used to submit API requests on
        your behalf (although there's no real danger to your TVDb account - I
        mean who would steal a free API key?).

4. Paste your API key into the API Key input box.

5. Check `Include Movies` if you do not want TCM to reject Episodes which are
also movies (most common for Anime).

6. Enter your desired minimum image resolution. This is personal preference
based on your own quality threshold of images. If you truly don't care about
image quality, you can enter `0x0`.

    ??? question "What if there are no images above this threshold?"

        If none of the available images are above both the minimum width _and_
        height you specify, then TCM will move to the next Connection in your
        global [Image Source
        Priority](../../user_guide/settings.md#image-source-priority).

    !!! tip "Threshold Application"

        This threshold _only_ applies to automatically-gathered Source Images.
        Logos, posters, and Source Images selected manually via the UI have no
        minimum resolution.

7. Click <span class="example md-button">Create</span>.

8. Once the page has reloaded, you may change the `Episode Ordering` to
however you want TCM to grab data from TVDb in. Most users should leave it as
`Default`.

    !!! warning "Missing Episode Ordering"

        If a non-`Default` value is selected and a Series does not have the
        selected ordering, then TCM will be unable to grab any Episode data for
        that Series.

        If you want to use separate orderings for separate Series, consider
        creating multiple TVDb Connections in TCM (these can be use the same
        API key), changing the ordering for each, and then assigning the
        appropriate Connection to your Series as-needed.
