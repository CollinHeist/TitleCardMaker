# Sonarr

!!! info "Optional Step"

    This step is completely optional, and only those with Sonarr servers
    should continue.

1. Toggle the `Enable Sonarr` checkbox.
2. Enter the _root_ URL of your Sonarr server (including the port).

    ??? example "Example URL"

        Although your local IP address will obviously be different, this
        IP should be _like_ `http://192.168.0.29:8989/`.

3. Open the Sonarr WebUI, then open your settings from the left
navigation bar.
4. Towards the bottom of the Settings submenu, open `General`.
5. Under the Security subsection, and find and copy the API key - it
should be a 32-character long string of numbers and the letters between
A and F.
6. Back within TitleCardMaker, paste the API key from Step 5 into the
API key input box.
7. The next step is to add the top-level directories for each of your
Television libraries to that TitleCardMaker can automatically detect a
Series' Library when [Syncing](../first_sync/sonarr.md) from Sonarr. See
the following examples for guidance on how to enter your library paths.

    !!! tip "Quick Setup"

        For most users, simply listing the paths in Sonarr under
        `Settings` > `Media Management` > `Root Folders` and their
        associated Library names will work.

    ??? example "Example Library Paths"

        === "Example 1"

            I have two libraries, called `Anime` and `TV` in my
            Media Servers that are in __separate__ directories. Within
            Sonarr, the `Anime` library is located under
            `/data/media/anime`, and the `TV` library is located under
            `/data/media/tv`.

            Within TitleCardMaker, this setting should be entered as:

            | Library Name | Path |
            | ---: | :--- |
            | Anime | /data/media/anime |
            | TV | /data/media/tv |

        === "Example 2"

            I have two libraries, called `Anime` and `TV` in my
            Media Servers that are in __separate__ directories. Within
            Sonarr, the `Anime` library is located under
            `/data/media/anime`, but the `TV` library is located under
            two _separate_ directories, `/data/media/tv_4k` and
            `/data/media/tv_hd`. 

            Within TitleCardMaker, this setting should be entered as:

            | Library Name | Path |
            | ---: | :--- |
            | Anime | /data/media/anime |
            | TV | /data/media/tv_4k |
            | TV | /data/media/tv_hd |

            Notice how each root directory of the TV library needs an
            entry.

        === "Example 3"

            I have three libraries, called `Anime`, `TV`, and `TV (4K)`
            in my Media Servers that are in __separate__ directories.
            Within Sonarr, the `Anime` library is located under
            `J:\Anime`, the `TV` library under `K:\TV`, and the
            `TV (4K)` library is under `K:\TV 4K`. 

            Within TitleCardMaker, this setting should be entered as:

            | Library Name | Path |
            | ---: | :--- |
            | Anime | J:\Anime |
            | TV | K:\TV |
            | TV (4K) | K:\TV 4K |

8. After entering all the necessary library paths, click the `Save
Changes` button.

*[Media Server]: Plex, Emby, or Jellyfin
*[Media Servers]: Plex, Emby, or Jellyfin
*[TCM]: TitleCardMaker
*[TMDb]: TheMovieDatabase