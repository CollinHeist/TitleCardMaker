# Import TitleCardMaker YAML Settings
## Background

!!! note "Applicability"

    This page is only applicable to users who have old YAML preferences files
    from previous TitleCardMaker installations. New users should skip this.

For users migrating to the Web UI from TCM v1 (the command-line interface), some
of the following configuration steps _can_ be skipped by importing your
Preferences YAML file.

## Instructions

1. In the TitleCardMaker Web Interface, open the `Importer` from the left-hand
side navigation bar.

2. Scroll down to the YAML section of this page. You can now copy and paste your
entire Preferences YAML file in the text box.

3. There are three checkboxes that toggle which settings TCM should parse while
importing YAML. A summary of what each box enables is below:

    === "Global Options"

        ```yaml
        options:
            source: # ...
            card_dimensions: # ...
            card_extension: # ...
            card_type: # ...
            episode_data_source: # ...
            filename_format: # ...
            image_source_priority: # ...
            season_folder_format: # ...
            sync_specials: # ...

        plex: # (1)
            watched_style: # ...
            unwatched_style: # ...
        ```

        1. Parses the `emby`, `plex`, or `jellyfin` section for this.

    === "Connections"

        ```yaml
        emby:
            url: # ...
            api_key: # ...
            username: # ...
            verify_ssl: # ...
            filesize_limit: # ...

        jellyfin:
            url: # ...
            api_key: # ...
            username: # ...
            verify_ssl: # ...
            filesize_limit: # ...

        plex:
            url: # ...
            token: # ...
            verify_ssl: # ...
            integrate_with_pmm_overlays: # ...
            filesize_limit: # ...

        sonarr:
            url: # ...
            api_key: # ...
            verify_ssl: # ...

        tmdb:
            api_key: # ...
            minimum_resolution: # ...
            skip_localized_images: # ...
            logo_language_priority: # ...
        ```

    === "Syncs"

        ```yaml
        emby:
            sync: # ...

        jellyfin:
            sync: # ...

        sonarr:
            sync: # ...

        tmdb:
            sync: # ...
        ```

    ??? question "What settings are not imported? Why?"
    
        There are [a lot]() of changes between TCM v1 and v2 - because of this,
        some settings are no longer applicable, and as such are not imported.
        These are:

        The list of Series YAML files (`options`, `series`)
        
        :   TitleCardMaker no longer reads YAML files for lists of Series to
            create Title Cards for. However, these files _can_ be [imported]().

        Execution mode (`options`, `execution_mode`)

        :   TitleCardMaker now executes all primary tasks on separate,
            [schedulable](), intervals. The concept of the two different
            execution modes is no longer applicable.

        Font validation (`options`, `validate_fonts`)

        :   This feature was hardly ever _disabled_, as there is very little
            reason to do so. Font validation is always enabled.

        Language codes (`options`, `language_codes`)

        :   Language codes are now interpreted directly from a Series' or
            Episode's episode text format, and do not need to be globally
            enabled.

        Various Sync options

        :   Since TCM no longer Syncs to files, a lot of old Sync settings are
            no longer applicable. These are `file`, `mode`, `compact_mode`, and
            `yaml` `exclusions`.

        Archives

        :   Currently, Archives are completely removed from TCM v2 due to their
            complexity and relatively niche use. 

        ImageMagick container name

        :   The ability to specify a standalone ImageMagick container to use was
            not used, and added needless complication. So parsing these options
            is no longer necessary.

4. If you plan on importing Sync data, _and_ you have any `add_template`
specifications, you first need to create those Templates so that TCM can assign
them to the imported Syncs. See [here](../getting_started/creating_template.md)
for an introduction to creating Templates. Make sure the Template name
__exactly__ matches the name in your Sync.

5. After selecting your desired import options, click the `Submit` button to
start the import process.

*[Media Server]: Plex, Emby, or Jellyfin
*[Media Servers]: Plex, Emby, or Jellyfin
*[TCM]: TitleCardMaker
*[TMDb]: TheMovieDatabase