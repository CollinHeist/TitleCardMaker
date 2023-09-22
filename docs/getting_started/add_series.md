# Adding a Series
## Background

Now that TitleCardMaker has established connections to all of your servers, it
is time to begin the actual Title Card creation. This step is to showcase how
Series can be _manually_ added to TCM. 

!!! info "Automatically Adding Series"

    Manually adding Series is not the typical use-case for TCM, as adding an
    entire server's worth of Series would be extremely tedious. Automatically
    adding Series is covered in [the next step](./first_sync/index.md).

## Instructions

1. Navigate back to the TitleCardMaker homepage - this can be done by clicking
:fontawesome-solid-tv: `Series` from the side navigation bar, or clicking the
TCM logo in the top corner.

2. In the top right (below the search bar), click the `+ New Series` button.
This will take you to a separate page where you can browse both Series and
Blueprints.

3. For this tutorial, we'll be adding and customizing
[Better Call Saul](https://www.themoviedb.org/tv/60059-better-call-saul).
Depending on which connections you've enabled, select one (the default being
whatever your default Episode data source is), and then then type _Better Call
Saul_ in the top search bar and click `Search`.

    !!! note "Search Source"

        If your default search connection is Emby, Jellyfin, or Plex and you
        don't have Better Call Saul in your server, you can choose a different
        connection or search TMDb.

4. TCM will now query your selected connection for all Series that match that
name. _Better Call Saul_ should be the first result. There are now two ways to
add this to TCM:

    1. Click the Series search result - this launches a popup dialog where you
    can assign any libraries or Templates to the Series, as well as search for
    any existing Blueprints.

    2. Click the `Quick-Add` button on the right of the result. This adds the
    Series to TCM using the last-selected library and Template settings. This
    makes it easy to quickly add multiple Series in succession.

5. Click the search result (option 1 above). If you'd like, assign the
appropriate media server library from the dropdown (if available). At the bottom
of the dialog, click the `Search for Blueprints` button. If you like the look of
any these, you can import them (and the Series) here. Otherwise, click `Add`.

    ??? question "What are Blueprints?"

        Blueprints are described in greater detail [here](../blueprints.md), but
        in-short: they are pre-made Title Card configurations that include
        everything needed to made Cards in a given style. This includes Fonts,
        Templates, Series customizations, etc.

6. After TCM has finished processing the Series, go to the _Better Call Saul_
Series page in one of a few ways:

    1. Click the Search box in the top left corner, then search for and select
    _Better Call Saul_.

        !!! tip "Keyboard Shortcut"

            You can enter the Search box by typing ++f++ or ++s++ (for `f`ind
            and `s`earch) anywhere in TCM (when a textbox is not selected).
    
    2. Return to the home page by clicking the `Series` button on the left
    navigation bar, find _Better Call Saul_ and click either the `View` button
    or the Series name.

        !!! tip "Keyboard Shortcut"

            You can return to the home page by typing ++shift++ + ++h++ (for
            `h`ome) anywhere in TCM (when a textbox is not selected).

7. Click the `Card Configuration` tab, then in the "Font" dropdown select the
`Better Call Saul` font we created earlier. This _assigns_ this custom font (and
all of it's associated customizations) to BCS. Scroll down and click `Save.` If
you imported a Blueprint back in Step 5, a custom Font will already have been
assigned.

!!! success "Success"

    You've now manually added a Series to TCM, as well as assigned a custom
    font. After the tutorial is completed you can review the cards created for
    BCS and see how this font is applied.
