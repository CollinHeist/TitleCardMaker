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
3. For this tutorial, we'll be adding and customizing
[Better Call Saul](https://www.themoviedb.org/tv/60059-better-call-saul) - in
the popup form, fill out the name and year as _Better Call Saul_ and `2015`.

    !!! tip "Required Information"

        In order to add a new Series, TCM only _requires_ a Series name and
        year. Assigning a Library or any Templates (covered later) at this point
        is optional.

4. Click `Add`. Behind the scenes, TCM will automatically try and match this
name and year to an existing Series based on the global Episode Data Source set
[previously](./settings.md). If you enabled a connection to TMDb, then TCM will
also try and download a poster.

    ??? warning "Missing Poster?"

        If the _Better Call Saul_ poster does not load (even after a refresh),
        and stays as a blank black image, then TCM might be unable to
        communicate with TMDb.

5. Close the "Add Series" popup.

6. From the homepage, hover over _Better Call Saul_ and click `View` to view the
Series customization page.

7. Click the `Card Configuration` tab, then in the "Font" dropdown select the
`Better Call Saul` font we created earlier. This _assigns_ this custom font (and
all of it's associated customizations) to BCS. Scroll down and click `Save.`

!!! success "Success"

    You've now manually added a Series to TCM, as well as assigned a custom
    font. After the tutorial is completed you can review the cards created for
    BCS and see how this font is applied.