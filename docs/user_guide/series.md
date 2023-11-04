---
title: Series
description: >
    All Series-specific customizations and actions.
tags:
    - Series
---

# :material-television: Series

!!! warning "Under Construction"

    This documentation is actively being developed.

When a Series is clicked on via the home page or the search bar, you will access
the Series page (at `/series/{series_id}`) where all Series-level options, Title
Card customizations, files, and actions can be viewed.

![Series Page](../assets/series_light.webp#only-light){.no-lightbox}
![Series Page](../assets/series_dark.webp#only-dark){.no-lightbox}

This page is separated into two sections - the _actions_ (on the left), and the
_options_ (on the right).

## Poster

When a Series is added to TitleCardMaker, it looks for a poster in your media
servers (Plex, Emby, Jellyfin) - _if a library has been assigned_ - and then
TMDb.

This poster is purely visual and is not used for Title Card creation.

??? tip "Changing the Poster"

    If you would like to change the poster, hover over the poster and click the
    `Edit Poster` button. This will launch a modal where you can either enter a
    URL which TCM will download the poster from, query TMDb for a poster, or
    upload a file from your current machine. 

    After selecting any of these options, clicking `Update` will then swap out
    the currently visible poster for the Series.

## Navigation

To the right of the Series name are two arrow icons
(:material-arrow-left-circle: and :material-arrow-right-circle:). Clicking
either of these will navigate to the previous and next Series _alphabetically_
from the current Series.

If you click either arrow and the current page does not change _and_ the arrow
becomes greyed out, then there is no next or previous Series to navigate to.

## Monitoring

Each Series can be _monitored_ and _unmonitored_. All Series start as monitored
unless explicitly unmonitored, which can be done by clicking the green / red
button below the Series poster. Unmonitored Series do __not__ do the following
actions _automatically_. All actions can still be done manually.

- Refresh Episode data - i.e. check for new Episodes, look for modified
Episode titles, etc.
- Add Episode translations
- Download missing Source Images

The Tasks in [the scheduler](./scheduler.md) that are responsible for the
above actions will skip all unmonitored Series.

## Series Processing

The `Process Series` button can be pressed to perform multiple Card operations
at once, in the correct order. Pressing this button does the following:

1. Refreshes all Episode data; then
2. Looks for any missing Episode translations; then
3. Download any missing Source Images; and finally
4. Begins Title Card creation

!!! tip "Recommendation"

    Pressing this button is preferable to individually clicking each
    corresponding button as TCM will wait for each step to finish _before_
    moving on. Whereas if you pressed each button back-to-back, then TCM likely
    will have not finished a step by the time it starts Title Card creation.

## Refresh Episode Data

!!! note "Scheduled Action"

    This action occurs automatically as part of the [Refresh Episode
    Data](./scheduler) Task __unless the Series is [unmonitored](#monitoring)__.

The `Refresh Episode Data` button can be pressed to start reloading the Episode
data for the current Series. This does a few things:

- Queries the effective [Episode data source](...) for any _new_ Episodes and
adds them to the Series; and
- Updates the titles of all _existing_ Episodes to match what is currently
present in the Episode data source __if__ [title matching](...) is enabled.

## Download Source Images

!!! note "Scheduled Action"

    This action occurs automatically as part of the [Download Source
    Images](./scheduler.md) Task __unless the Series is
    [unmonitored](#monitoring)__.

The `Download Source Images` button can be pressed to start a download of all
Source Images for Episodes which do not already have images. It will __not__
replace any existing images, nor will it download any backdrops or logos.

TCM will search for images in the order specified in your global [image source
priority](./settings.md#image-source-priority). If the Series does not have
any libraries assigned for a given media server Connection - i.e. a Plex
Connection being in your source priority, but this Series having no Plex
library - then it will be skipped.

## Create Title Cards

!!! note "Scheduled Action"

    This action occurs automatically as part of the
    [Create Title Cards](./scheduler.md) Task.

The `Create Title Cards` button can be pressed to prompt TCM to begin updating
existing, _and_ create new Title Cards. In order to apply any watch-status
conditional styling, TCM also gets the Episode watched statuses before creating
the Cards.

!!! tip "Background Execution"

    Because Title Card creation can take a long time, Card creation is executed
    in a background thread. This also means that if you start Card creation,
    make a change which would prompt new Cards, and then restart Card creation;
    TCM will create, delete, then re-create the Cards.

## Title Card Loading

!!! note "Scheduled Action"

    This action occurs automatically as part of the
    [Load Title Cards](./scheduler.md) Task. Title Cards are never automatically
    force-reloaded.

Below the `Create Title Cards` button will be multiple sets of grouped buttons
which can be used to load all created Title Cards into the relevant library.

Selecting `Load Cards` will load only _unloaded_ Title Cards into the associated
Connection and library. This only affects Title Cards which were changed (and
not re-loaded), or never loaded in the first place.

Selecting `Force Reload Cards` will reload _all_ Title cards into the associated
Connection and library. This is much slower than the `Load Cards` button, but
can be used as needed - most commonly when the metadata of a Media Server is
reset and previously loaded Title Cards are removed.

## Remove Episode Labels

TitleCardMaker looks for specific labels on Episodes within Plex to determine
whether it is able to download Source Images from that Episode. This is done to
avoid grabbing a "Source Image" which is actually a previously loaded Title
Card, or some image with a PMM overlay applied.

Alongside each Plex library will be a `Remove Episode Labels` button. This
button can be pressed to remove the labels which TCM uses to track whether an
Episode can provide a Source Image. This is applies to all Episodes of this
Series within Plex.
