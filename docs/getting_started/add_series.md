---
title: Manually Adding a Series
description: >
    An introduction to manually adding a Series to TitleCardMaker.
tags:
    - Tutorial
    - Series
---

# Adding a Series


!!! note "Example Series"

    I'll be referring to _Better Call Saul_ as example Series. If you do not
    have this Series in your server, you can add it (and remove it later if
    needed), or just pick an entirely different Series.

Now that TitleCardMaker has established connections to all of your servers, it
is time to begin the actual Title Card creation. TCM will only create Cards for
Series that have been added - this step is to showcase how to do this manually.

!!! info "Automatically Adding Series"

    Manually adding Series is not the typical use-case for TCM, as adding an
    entire server's worth of Series would be extremely tedious. Automatically
    adding Series is covered in [the next step](./first_sync/index.md).

1. Navigate back to the TitleCardMaker homepage - this can be done by clicking
:fontawesome-solid-tv: `Series` from the side navigation bar, or hitting
++shift++ + ++h++ (when a text box is not selected).

2. On the left-hand side bar, a navigation menu labeled
:material-magnify-plus-outline: `Add` should appear. Click this to go to the
"Add Series" page where you can add both Series and Blueprints.

3. For this tutorial, we'll be adding and customizing
[Better Call Saul](https://www.themoviedb.org/tv/60059-better-call-saul). Under
`Browse Series`, type _Better Call Saul_ in the search bar and click
<span class="example md-button">Search</span>.

    !!! note "Search Source"

        If your default search connection is Emby, Jellyfin, or Plex and you
        don't have Better Call Saul in your server, you can choose a different
        connection, or just search TMDb.

    ??? warning "Sonarr Posters Not Loading"

        If the posters in your search results are not loading (all black), this
        is a result of Sonarr rejecting TCM's API request to view the poster.
        You can either disable authentication for local addresses within Sonarr
        (if using TCM locally), or just ignore this.

4. TCM will now query your selected connection for all Series which match that
name. _Better Call Saul_ should be the first result. Before you click anything,
you may select any media server libraries you want associated with this Series.

    !!! example "Example Libraries"

        If I had _Better Call Saul_ in a server under two libraries, then I
        could select either or both libraries in the dropdown so that TCM knows
        to load Cards into those libraries.

        If I did not have _Better Call Saul_ in any of my servers, then I can
        leave this blank. This can always be changed later.

5. Click the search result and TCM will begin processing it. While you are on
this page, scroll down to `Browse Blueprints` section at the bottom of the page.

6. Type _Better Call Saul_ in the Blueprint search field and click
<span class="example md-button">Browse Blueprints</span>. TCM will display all
available Blueprints for this Series - at the time of writing, there are 3. For
the purposes of this tutorial we will _not_ be importing these, instead we'll be
customizing the Cards ourselves. But keep in mind this is _one way_ to find
Blueprints.

    ??? question "What are Blueprints?"

        Blueprints are described in greater detail [here](../blueprints.md), but
        in-short: they are pre-made Title Card configurations that include
        everything needed to made Cards in a given style. This includes Fonts,
        Templates, Series customizations, etc.

7. Once TCM has finished processing the Series, go to the _Better Call Saul_
Series page in one of a few ways:

    1. Click the Search box in the top left corner, then search for and select
    _Better Call Saul_.

        !!! tip "Keyboard Shortcut"

            You can enter the Search box by typing ++f++ or ++s++ (for `f`ind
            and `s`earch) anywhere in TCM (when a textbox is not selected).
    
    2. Return to the home page by clicking the :fontawesome-solid-tv: `Series`
    button on the left navigation bar, find _Better Call Saul_ and click either
    the <span class="example md-button">View</span> button or the Series name.

8. Click the `Card Configuration` tab. In the `Font` dropdown, select the
`Better Call Saul` font we created earlier. This assigns this custom font (and
all of it's associated settings) to _Better Call Saul_. Scroll down and click
<span class="example md-button">Save</span>.

!!! success "Success"

    You've now manually added a Series to TCM, as well as assigned a custom
    font. After the tutorial is completed you can review the cards created for
    BCS and see how this font is applied.
