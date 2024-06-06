---
title: Creating Title Cards
description: >
    Wrapping up the tutorial with Title Card creation.
tags:
    - Tutorial
    - Title Cards
---

# Creating Title Cards

!!! warning "Under Construction"

    This documentation is actively being developed.

There has been a lot of preamble, but the core of TitleCardMaker is making
Title Cards. We'll be creating Title Cards in order to showcase the effects of
our Template, as well as show how these Cards can be further customized.

!!! example "Example Series"

    This part of the tutorial will refer to _Breaking Bad_ as the example Series. 
    Those who decided to Sync a Series __other than__ _Breaking Bad_ can still
    follow these steps, just apply them to whatever Series you chose.

## Episode Data

1. Go to the _Breaking Bad_ Series configuration page - you can quickly access
it by searching for the title in the top left search bar (next to the TCM logo).

2. At the top of the page is a set of buttons where many global actions can be
performed. However, in this case, open the `Episode Data` tab in the middle of
the page and click the <span class="example md-button">Refresh</span> button.
TCM will now query your global Episode Data Source for any new Episodes
(although this is also done when you first add a Series to TCM).

    !!! note "Scheduled Task"

        Refreshing Episode data happens automatically as a
        [scheduled task](../user_guide/scheduler.md), __unless__ the Series is
        marked as Unmonitored.

## Source Images

4. Open the "Files" tab. This tab shows image information for all Source Images
for each Episode of the Series. Since we just added _Breaking Bad_, all images
should show as missing.

5. Under _Source Images_, for Season 1 Episode 1, click the browse
:material-grid-large: icon. This will launch a browser for all Source Images on
TMDb. Clicking any image will request TCM download it and store it inside the
Source Image directory. Download any image.

    ??? tip "Image Resolution"
    
        In the corner of each image is a small ribbon that indicates the
        resolution of the image.
        
        When manually browsing the images on TMDb, your global minimum
        resolution is ignored.

    ![](../assets/tmdb_browse_images.jpg)

6. Close the image browser. The file for that Episode should now be filled in
with Source Image information.

    !!! note "Scheduled Task"

        Downloading Source Images happens automatically as a
        [scheduled task](../user_guide/scheduler.md), __unless__ the Series is
        marked as Unmonitored.

## Title Cards

7. At the top of the page, click
<span class="example md-button">Create Title Cards</span>.

8. After waiting a small while for TCM to have created a few Cards, go to the
_Title Cards_ section on the _Files_ tab and expand the _View Images_ accordion.

9. You should see that Title Cards have been created using the Tinted Frame card
type.

10. Back in the _Episode Data_ tab, click the :material-eye-outline: icon
under the _Extras & Translations_ column for Season 2 Episode 1. In that window,
change the _Bottom Element_ input to `omit`, hit
<span class="example md-button">Save</span> and close out the window.

11. Close Click <span class="example md-button">Create Title Cards</span> again.
This Card should be remade with no logo in the bottom position, overriding what
was placed in the Template.

    ??? question "Why did the Template not apply?"

        Any Episode-level customizations _override_ Series-level customizations.

        Because we entered this extra for the Episode, the extra from the
        Series' Template is completely ignored.

## Cleanup

The substantive part of the tutorial is over, and I recommend removing cleaning
up the artifacts from the tutorial. These are:

- Delete the Template
- Delete (or edit) the Sync
- Set the scheduler task interval to something sensible
- If you want to use different Cards, then the Series and Fonts can also be
deleted.

!!! success "Tutorial Completed"

    With that finished, you have successfully grabbed Episode data, downloaded
    Source Images (manually _and_ automatically), created Title Cards, seen how
    Template Filters apply, as well as observed the effects of overriding card
    creation on an Episode-level.

    These are all the major components of TCM, and mark the end of the tutorial.
    If you have any other questions, you can browse this documentation or reach
    out for help on the [Discord](https://discord.gg/bJ3bHtw8wH).

!!! question "What's Next?"

    For most users, the next step is to create a Sync that doesn't just Sync
    the example Series, but instead _all_ (or large portions) of your Series.
    Review [Creating the First Sync](./first_sync/index.md) for a reminder on
    how to create Syncs.

    See the [User Guide](../user_guide/index.md) for detailed guides on each
    part of TCM.
