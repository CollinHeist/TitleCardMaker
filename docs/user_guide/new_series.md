---
title: Adding Series and Blueprints
description: >
    Manually adding a Series or Blueprint.
tags:
    - Series
    - Blueprints
---

# Series and Blueprint Browser

!!! warning "Under Construction"

    This documentation is actively being developed.

## Background
From the left-hand navigation menu, new Series and Blueprints can be manually
added and imported to TitleCardMaker. When on the home page, the
:material-magnify-plus-outline: `Add New` sub-menu will appear. This can also
be accessed from the search bar (top-left corner, or hitting the ++s++ key) and
clicking the bottom `Search for ...` result.

This page is separated into two sections, the Series browser - where new Series
can be search for and added; and the Blueprints browser - where all Blueprint
submissions can be viewed, filtered, and imported.

## Adding Multiple Series

If you are adding multiple Series (especially with the same Title Card
configuration, or first a first-time setup) it is recommended to set up a
[Sync](./syncs.md), as this automates the process.

## Browse Series

After typing the name of the Series you're looking to add, select the applicable
Connection to search. The default is to search your global
[Episode data source](./settings.md#episode-data-source), but it is largely
irrelevant which Connection you browse (as TCM uses them all). Click `Search`.

![Browsing Series](../assets/add_series_light.png#only-light){.no-lightbox}
![Browsing Series](../assets/add_series_dark.png#only-dark){.no-lightbox}

!!! note "Unclickable Results"

    Results which have already been imported will not be clickable, and will
    appear greyed out. See the first result above.

The top results will appear below. Clicking a result will launch a separate
dialog in which any libraries or [Templates](./templates.md) can be applied. Of
course these can also be changed later by going to the Series page itself.

In addition to the above Series options, you may also browse any existing
[Blueprints](../blueprints.md) that are available for this Series. Clicking the
`Import Series and Blueprint` button will start the Series import process - so
be sure to have entered any libraries or Templates beforehand.

If not utilizing a Blueprint, then click the `Add` :material-plus: button to add
the Series to TitleCardMaker.

## Quick-Adding Series

On the right-hand side of the result is a `Quick-Add` button. This can be
pressed to bypass the customization dialog and add the Series to TCM using
__the last-selected library and Template options__. This can be useful if you
are adding multiple related Series, but do not want to create a
[Sync](./syncs.md).

## Browse Blueprints

!!! tip "Blueprints"
    
    Blueprints are described in much greater detail [here](../blueprints.md).

Below the Series browser is the Blueprints browser. From here, you can view the
Blueprint submissions for _all_ Series. These can be sorted by (Blueprint)
release date and Series name.  There are also two filter options which adjust
_which_ Blueprints are displayed:

- Only show Blueprints for Series which you have already added to TCM
- Display Blueprints which you have already imported

![](../assets/blueprint_all_light.webp#only-light){.no-lightbox}
![](../assets/blueprint_all_dark.webp#only-dark){.no-lightbox}

There are two actions for each Blueprint:

- __Import__ - add the selected Blueprint (along with the associated Series
_if_ it is not already in TCM).
- __Hide__ - Remove the selected Blueprint from this list. However it will still
be present if you browse for Blueprints [by Series](../blueprints.md#by-series).