---
title: Syncing from Emby
description: >
    Creating a Sync to automatically add Series from Emby to TitleCardMaker.
tags:
    - Tutorial
    - Emby
    - Sync
---

# Syncing from Emby

!!! note "Example Series"

    I'll be referring to _Better Call Saul_ and _Breaking Bad_ as example
    Series. If you do not have either of these Series in your Emby server, you
    can add them (and remove them later - or not, because they're great shows
    :wink:), or just pick two entirely different Series.

For the purposes of this tutorial, we will be Syncing a subset of your Series
by using a filter tag within Emby.

1. Open Emby.

2. Open _Better Call Saul_, and then click the "more data"
:material-dots-horizontal: button, then click `Edit Metadata` for the Series.

3. At the very bottom click the `+` button next to Tags, type `tcm-test` and hit
++enter++ - click `Save`.

4. Repeat Steps 2-3 for _Breaking Bad_.

5. Back within TitleCardMaker, navigate to the Sync page by clicking
:fontawesome-solid-arrows-rotate: `Sync` from the side navigation bar.

6. Under the Emby section of the page, click the `+ Add Sync` button.

7. In the launched dialog, fill out the following information:

    1. Enter the Sync Name as `Test Sync`
    2. In the "Templates to Apply", select __in order__, the `Tier 1 - Standard`
    and `Tier 0 - Tinted Frame` Templates from
    [earlier](../creating_templates.md) in the tutorial.

        !!! tip "Template Order Matters"

            For Templates, the order in which they are listed is critical. TCM
            will apply the first Template whose Filter conditions are all
            satisfied.

    3. Under the Filters section, enter the tag `tcm-test` and hit ++enter++.
    4. Hit the `Create` button.

    !!! success "Sync Created"

        You have successfully created a Sync that automatically adds all Series
        in Emby that are tagged with `tcm-test`, and assigns our two Templates
        to them.

8. At the top of the page is an indication of when all your Syncs will next
run - we'll adjust this [next](../scheduler.md) - but to run a Sync
immediately, click the small :fontawesome-solid-arrows-rotate: Sync icon.

9. TCM will then query Emby for all your Series, filter the results by our
indicated filters (in our case the `tcm-test` tag), and then filter out any
exclusions (none). The added Series will be listed in a message. You should
see "Synced 1 Series", with _Breaking Bad_ listed below.

    ??? question "Why is _Better Call Saul_ not listed here?"

        The reason BCS is not listed as having been Synced is because when TCM
        runs a Sync, it checks the resulting list of Series against any
        _existing_ Series. Since BCS was added in the previous step, TCM does
        not add it again.

!!! success "Synced from Emby"

    You have successfully Synced from Emby. This exact structure can be used
    to create and run any number of Syncs.

*[BCS]: Better Call Saul