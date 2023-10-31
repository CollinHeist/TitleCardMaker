---
title: Connecting to TMDb
description: >
    How to connect TitleCardMaker to The Movie Database.
tags:
    - Tutorial
    - TMDb
---

# :simple-themoviedatabase:{.tmdb} The Movie Database

!!! info "Optional Step"

    This step is _technically_ optional, but is __strongly recommended__ for all
    users.

The Movie Database (hereafter referred to as TMDb for brevity) is a free,
publicly accessible database which  can serve as an
[Episode Data Source](../../user_guide/settings.md#episode-data-source), and is
the recommended
[Image Source](../../user_guide/settings.md#image-source-priority) due to the 
much higher quality (and selection) of images compared to the Media Servers. It
is also the only Connection which can provided Episode translations, Series
logos, backdrops, and posters.

1. Click the external link :octicons-link-external-16: icon and open the TMDb
[Getting Started](https://developer.themoviedb.org/docs/getting-started) page.

2. Follow their instructions to generate an API key for yourself. You can put
whatever you'd like in the application details (such as TCM, nunya, etc.). Copy
the generated API key.

    ??? danger "Security Warning"

        Keep this API key private, as it can be used to submit API requests on
        your behalf (although there's no real danger to your TMDb account - I
        mean who would steal a free API key?).

3. Back in TCM, on the Connections page, scroll down towards the bottom and
click the `Add Connection` button beneath _TheMovieDatabase_.

4. Paste your API key from Step 2 into the API Key input box.

5. Enter your desired minimum image resolution. This is personal preference
based on your own quality threshold of images - I personally use `800x400`. If
you truly don't care about image quality, you can enter `0x0`.

    ??? question "What if there are no images above this threshold?"

        If none of the available images are above both the minimum width _and_
        height you specify, then TCM will move to the next Connection in your
        global [Image Source
        Priority](../../user_guide/settings.md#image-source-priority).

    !!! tip "Threshold Application"

        This threshold _only_ applies to automatically-gathered Source Images.
        Logos and posters, in addition to Source Images you select within the
        UI, have no minimum resolution.

6. Check `Ignore Localized Images` so that TCM rejects Source Images which have
assigned languages.

7. Click `Create`.

7. After the page has reloaded, and if you speak any non-English languages,
select these in the order you which TCM to grab logos in.

    !!! example "Example and Recommendation"

        Selecting `English` and `Japanese` as the only two options, this will
        prompt TCM to search for logos in English first, and then Japanese if no
        English logos are available.

        This is recommended for users who have Anime libraries.
