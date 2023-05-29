# Adding a Series
## Background

Now that TitleCardMaker has established connections to all of your servers, it
is time to begin the actual Title Card creation. This step is to showcase how
Series can be _manually_ added to TCM. 

!!! info "Automatically Adding Series"

    Manually adding Series is not the typical use-case for TCM, as adding an
    entire server's worth of Series would be extremely tedious. Automatically
    adding Series is covered in the next step, Creating the First Sync.

## Instructions

1. Navigate back to the TitleCardMaker homepage - this can be done by clicking
`Series` from the side navigation bar, or clicking the TCM logo in the top
corner.
2. In the top right (below the search bar), click the `+ New Series` button.
3. For this tutorial, we'll be adding and customizing
[Better Call Saul](https://www.themoviedb.org/tv/60059-better-call-saul) - in
the popup form, fill out the name and year as `Better Call Saul` and `2015`.

    !!! tip "Required Information"

        In order to add a new Series, TCM only _requires_ a Series name and
        year. Assigning a Library or any Templates (covered later) at this point
        is optional.

4. Click `Add`. Behind the scenes, TCM will automatically try and match this
name and year to an existing Series based on the global Episode Data Source set
[previously](./settings.md). If you enabled a connection to TMDb, then TCM will
also try and download a poster.
5. Close the "Add Series" popup.

    !!! success "Success"

        If a poster for `Better Call Saul` is now visible on your homepage,
        you've successfully added a series to TitleCardMaker.

        You can view the Series customization page by clicking the name or the
        View button (visible when hovering over the poster). We'll explore this
        page [later on]().

    !!! warning "Missing Poster"

        If the `Better Call Saul` poster does not load (even after a refresh),
        and stays as a blank black image, then TCM might be unable to
        communicate with TMDb.

*[Media Server]: Plex, Emby, or Jellyfin
*[Media Servers]: Plex, Emby, or Jellyfin
*[TCM]: TitleCardMaker
*[TMDb]: TheMovieDatabase