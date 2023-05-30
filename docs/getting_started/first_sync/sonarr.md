# Syncing from Sonarr

!!! note "Example Series"

    For this tutorial, we'll be using `Better Call Saul` and `Breaking Bad` as
    example Series. If you do not have either of these Series in Sonarr, you can
    add them (and remove them later - or not, because they're great shows), or
    just pick two entirely different Series.

1. For the purposes of this tutorial, we will be Syncing a subset of your
Series by using a filter tag within Sonarr. Open the Sonarr Web Interface.

2. Open `Better Call Saul`, and then click the `Edit` wrench.

3. In the Tags section, type `tcm-test` and hit ++enter++ - click `Save`.

4. Repeat Steps 2-3 for `Breaking Bad`.

5. Back within TitleCardMaker, navigate to the Sync page by clicking `Sync` from
the side navigation bar.

6. Under the Sonarr section of the page, click the `+ Add Sync` button.

7. In the launched dialog, fill out the following information:

    1. Enter the Sync Name as `Test Sync`
    2. In the "Templates to Apply", select __in order__, the `Tier 1 - Standard`
    and `Tier 0 - Tinted Frame` Templates from
    [the last step](../creating_template.md).

        !!! tip "Template Order Matters"

            For Templates, the order in which they are listed is critical. TCM
            will apply the first Template whose Filter conditions are all
            satisfied.

    3. Under the Filters section, open the dropdown and select the tag
    `tcm-test`.

        ??? warning "Tag not appearing?"

            Sonarr can take a while to refresh the API with newly created Tags,
            so if the `tcm-test` tag does not appear in the dropdown, you can
            type it and hit ++enter++ to manually enter the tag.

    4. Hit the `Create` button.

    !!! success "Sync Created"

        You have successfully created a Sync that automatically adds all Series
        in Sonarr that are tagged with `tcm-test`, and assigns our two Templates
        to them.

8. At the top of the page is an indication of when all your Syncs will next
run - we'll cover adjusting this [later]() - but to run a Sync immediately,
click the small blue Sync icon (the circular arrows next to the delete icon).

9. TCM will then query Sonarr for all your Series, filter the results by our
indicated filters (in our case the `tcm-test` tag), and then filter out any
exclusions (none). The added Series will be listed in a message. You should
see "Synced 1 Series", with "Breaking Bad" listed below.

    ??? question "Why is Better Call Saul not listed here?"

        The reason BCS is not listed as having been Synced is because when TCM
        runs a Sync, it checks the resulting list of Series against any
        _existing_ Series. Since BCS was added in the previous step, TCM does
        not add it again.

!!! success "Synced from Sonarr"

    You have successfully Synced from Sonarr. This exact structure can be used
    to create and run any number of Syncs.

*[BCS]: Better Call Saul
*[Media Server]: Plex, Emby, or Jellyfin
*[Media Servers]: Plex, Emby, or Jellyfin
*[TCM]: TitleCardMaker
*[TMDb]: TheMovieDatabase