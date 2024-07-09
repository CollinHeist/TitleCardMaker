---
title: Adding Series and Blueprints
description: >
    Manually adding a Series or Blueprint.
tags:
    - Series
    - Blueprints
---

# Series and Blueprint Browser

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
[Episode Data Source](./settings.md#episode-data-source), but it is largely
irrelevant which Connection you browse (as TCM uses them all). Click `Search`.

![Browsing Series](../assets/add_series_light.webp#only-light){.no-lightbox}
![Browsing Series](../assets/add_series_dark.webp#only-dark){.no-lightbox}

!!! note "Unclickable Results"

    Results which have already been imported will not be clickable, and will
    appear greyed out. See the first result above.

After the results have been populated, you are able to select any number of
libraries or [Templates](./templates.md). Of course these can also be changed
later by going to the Series page itself. After making your selections, clicking
any result will add that Series to TitleCardMaker.


## Browse Blueprints

!!! tip "Blueprints"
    
    Blueprints are described in much greater detail [here](../blueprints.md).

Below the Series browser is the Blueprints browser. From here, you can view the
Blueprint submissions for _all_ Series. These can be sorted by (Blueprint)
release date and Series name. There are also two filter options which adjust
_which_ Blueprints are displayed:

- Only show Blueprints for Series which you have already added to TCM
- Display Blueprints which you have already imported

![](../assets/blueprint_all_light.webp#only-light){.no-lightbox}
![](../assets/blueprint_all_dark.webp#only-dark){.no-lightbox}

The Blueprint themselves can be interacted with in various ways:

- If the Blueprint has more than one example Card, these can be cycled through
by clicking the image.
- Click the Blueprint Name to search your TitleCardMaker server for that Series.
- Click the creator's name to show all Blueprints by that creator (or those
creators)
- If there are multiple Blueprints for that Series, a small number icon will
appear - clicking this will filter the Blueprint browser by that Series' name.
- Click the :material-cloud-download: icon to add the Blueprint to TCM
- Click the :fontawesome-regular-eye-slash: icon to remove the Blueprint from
this list. However, this Blueprint will still be visible if browsing Blueprints
[by Series](../blueprints.md#by-series).
- Some Blueprints may be a part of a _Set_. This is described
[here](../blueprints.md#viewing-sets).

### Refreshing Blueprints

For performance reasons, TitleCardMaker caches the Blueprints database and only
re-downloads it every few hours. However, if you want to _force_ a reload of the
database, you can __right click__ the 
<span class="example md-button">Browse Blueprints</span> button.
