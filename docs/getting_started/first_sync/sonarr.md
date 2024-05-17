---
title: Syncing from Sonarr
description: >
    Creating a Sync to automatically add Series from Sonarr to TitleCardMaker.
tags:
    - Tutorial
    - Sonarr
    - Sync
---

# Syncing from Sonarr

!!! note "Example Series"

    I'll be using _Better Call Saul_ and _Breaking Bad_ as example Series. If
    you do not have either of these Series in Sonarr, you can add them (and
    remove them later - or not, because they're great shows), or just pick two
    entirely different Series.

For the purposes of this tutorial, we will be Syncing a subset of your Series
by using a filter tag within Sonarr.

1. Open the Sonarr Web Interface.

2. Open _Better Call Saul_, and then click the `Edit` wrench.

3. In the Tags section, type `tcm-test` and hit ++enter++ - click `Save`.

4. Repeat Steps 2-3 for _Breaking Bad_.

5. Back within TitleCardMaker, navigate to the Sync page by clicking
:fontawesome-solid-arrows-rotate: `Sync` from the side navigation bar.

6. Under the Sonarr section of the page, click the
<span class="example md-button">+ Add Sync</span> button.

7. In the launched dialog, fill out the following information:

    1. Enter the Sync Name as `Test Sync`
    2. In the "Templates to Apply", select `Tinted Frame` Template from
    [earlier](../creating_templates.md) in the tutorial.

        !!! tip "Template Order Matters"

            When adding multiple Templates, the order in which they are listed
            is critical. TCM will apply the first Template whose Filter
            conditions are all satisfied.

    3. Under the Filters section, open the dropdown and select the tag
    `tcm-test`.

        ??? warning "Tag not appearing?"

            Sonarr can take a while to refresh the API with newly created tags,
            so if the `tcm-test` tag does not appear in the dropdown, you can
            type it and hit ++enter++ to manually enter the tag.

    4. Hit the `Create` button.

    !!! success "Sync Created"

        You have successfully created a Sync that automatically adds all Series
        in Sonarr that are tagged with `tcm-test`, and assigns our two Templates
        to them.

8. At the top of the page is an indication of when all your Syncs will next
run - we'll adjust this [next](../scheduler.md) - but to run a Sync
immediately, click the small :fontawesome-solid-arrows-rotate: Sync icon.

9. TCM will then query Sonarr for all your Series, filter the results by our
indicated filters (in our case the `tcm-test` tag), and then filter out any
exclusions (none). The added Series will be listed in a message. You should
see "Synced 1 Series", with _Breaking Bad_ listed below.

    ??? question "Why is _Better Call Saul_ not listed here?"

        The reason BCS is not listed as having been Synced is because when TCM
        runs a Sync, it checks the resulting list of Series against any
        _existing_ Series. Since BCS was added in the previous step, TCM does
        not add it again.

10. From the message, you can click on the newly added _Breaking Bad_ to
directly go to the Series page. On the main Configuration tab, double check that
the Library field for your Media Server is filled in with the correct library.

    ??? failure "Don't see a Library?"

        If you have enabled any other Media Servers and do not see a Library
        listed for this Series, that means that your Sonarr Library Paths
        are set incorectly, and TCM will not auto-detect a Series Library when
        syncing.

        Review Step 7 of the [Sonarr Setup](../connections/sonarr.md) page to
        correct your Library Paths. When you've corrected these, delete
        _Breaking Bad_ and re-Sync to verify they are correct.

!!! success "Synced from Sonarr"

    You have successfully Synced from Sonarr. This exact structure can be used
    to create and run any number of Syncs.

*[BCS]: Better Call Saul