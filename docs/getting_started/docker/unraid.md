---
title: Unraid Docker Installation
description: >
    Installing TitleCardMaker in a Docker container on Unraid.
---

# UnRAID Installation
## Background

!!! info "Benefits of Docker"

    For more info on the benefits of Docker, see [here](./index.md).

For Synology DSM users, the built-in Docker manager can be used to easily set up
TitleCardMaker with all the necessary Docker variables and paths.

## Instructions

1. Navigate to the UnRAID WebGUI home page for your server.

2. Select the `APPS` tab from the top toolbar.

3. In the search bar, search for `titlecardmaker`.

4. Click the first result, and in the actions (just below the container
name), click `Install`.

5. You will be prompted to choose which branch (or _tag_) to install,
make your selection and continue.

    ??? tip "Choosing the Right Branch"

        For most users, I recommend the default `latest` branch. This branch is
        updated with the most recent public release of TitleCardMaker, and is
        the most stable option.

        For users who are okay with the occasional bug, and would like to test
        out features _as they are developed_, then choose the `develop` tag.

6. UnRAID will take you to the Docker template, where you can edit the
details of the container as you'd like. There are four settings to take
note of, all other settings can be adjusted within TitleCardMaker.

    1. The `Source Directory`. This is where TitleCardMaker will keep
    all source images used in Title Card creation. The default path is
    recommended.
    2. The `Log Directory`. This is where TitleCardMaker will write log
    files, which can aid in debugging or monitoring the health of
    TitleCardMaker behind the scenes. The default path is recommended.
    3. The `Card Directory`. This is where TitleCardMaker will create
    the actual title card files. The default path is recommended.
    4. The `Group ID` (`GID`). This _needs_ to be valid group ID on your
    host UnRAID system that has both Read and Write access to the above
    directories. This is commonly `99`.
    5. The `User ID` (`UID`). This _needs_ to be a valid user ID on your
    host UnRAID system that has both Read and Write access to the above
    directories. This is commonly `100`.

        ??? question "Why Specify a User and Group?"

            Specifying a specific user and group ID allows TitleCardMaker
            to launch and run _as_ that user. This is recommended over
            the alternative of allowing the container to run as the
            `root` user, which could theoretically have permission
            implications. 

        ??? tip "Finding a Specific Group and User ID"

            If you have a specific user on your system you'd like to
            use, in the UnRAID terminal, type the following command:

            ```bash
            id {user}
            ```

            Replacing `{user}` with the _name_ of the user you'd like to
            get the ID's of.

7. After finalizing your settings, select `Apply`.

8. UnRAID will begin downloading the Docker container. After it's
finished, go back to the `DOCKER` tab, click the newly created
TitleCardMaker container, and then select `WebUI` from the dropdown.

!!! success "Success"

    Installation is complete, and TitleCardMaker is ready to be
    configured.
