---
title: Getting Started
description: >
    Acquaint yourself with the basics of TitleCardMaker - from installation to
    Title Card creation.
---

# Getting Started

## Accessing the Code

Sponsors of the project will be invited to a [private GitHub
repository](https://github.com/CollinHeist/TitleCardMaker-WebUI/). These steps
will walk you through getting the code from that repository.

After being invited, you will recieve an email at your GitHub's associated email
address, open it and accept the invitation while signed into your GitHub
account.

## Installation

There are three primary ways to install TitleCardMaker - Docker, Docker Compose,
and non-Docker. Docker Compose is generally recommended because it comes with
all the requirements (Python, ImageMagick, etc.), and does not require copying
any long commands.

=== ":material-docker: :fontawesome-solid-file-code: Docker Compose"

    1. Open a terminal[^1] of your choice, and go to your desired install
    location.

        ??? example "Example"

            === ":material-linux: Linux"

                ```bash
                cd "~/Your/Install/Directory/TitleCardMaker"
                ```

            === ":material-apple: MacOS"

                ```bash
                cd "~/Your/Install/Directory/TitleCardMaker"
                ```

            === ":material-powershell: Windows (Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\TitleCardMaker'
                ```

            === ":material-microsoft-windows: Windows (Non-Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\TitleCardMaker'
                ```

    2. In this directory, create a subfolder called `config` by executing the
    following command:

        === ":material-linux: Linux"

            ```bash
            mkdir config
            ```

        === ":material-apple: MacOS"

            ```bash
            mkdir config
            ```

        === ":material-powershell: Windows (Powershell)"

            ```bash
            mkdir config
            ```

        === ":material-microsoft-windows: Windows (Non-Powershell)"

            ```bash
            mkdir config
            ```

    3. We now need to make sure this directory has the correct permissions
    assigned to it.

        === ":material-linux: Linux"

            With the Group and User ID that you would like TCM to execute with,
            run the following command:

            ```bash
            sudo chown -R {group}:{user} ./config # (1)!
            ```

            1. Replace `{group}` and `{user}` with the actual group and user (or
            their ID's) - e.g. `99:100`.

        === ":material-apple: MacOS"

            With the Group and User ID that you would like TCM to execute with,
            run the following command:

            ```bash
            sudo chown -R {group}:{user} ./config # (1)!
            ```

            1. Replace `{group}` and `{user}` with the actual group and user (or
            their ID's) - e.g. `99:100`.

        === ":material-powershell: Windows (Powershell)"

            Changing the permissions is (generally) not necessary on Windows.

        === ":material-microsoft-windows: Windows (Non-Powershell)"

            Changing the permissions is (generally) not necessary on Windows.

    4. Follow [these](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token#creating-a-personal-access-token-classic)
    instructions to get a __classic__ personal access token (PAT). Check the
    `read:packages` checkbox in the third section from the top.

        ??? question "Why is this necessary?"

            Because the repository is private, accessing the Docker container
            requires authentication. You _can_ download the zipped code from the
            website, but this makes getting updates difficult.

            A PAT is required instead of a password because GitHub does not
            allow passwords to be used from the command line.

        ??? warning "Security Warning"

            Keep this access code private, as it can be used to access your
            GitHub account.

    5. Store these login credentials in Docker with the following command. Type
    your GitHub username, and enter the PAT from Step 4 as the password.

        === ":material-linux: Linux"

            ```console
            docker login ghcr.io
            ```

        === ":material-apple: MacOS"

            ```bash
            docker login ghcr.io
            ```

        === ":material-powershell: Windows (Powershell)"

            ```bash
            docker login ghcr.io
            ```

        === ":material-microsoft-windows: Windows (Non-Powershell)"

            ```bash
            docker login ghcr.io
            ```

    6. Determine your timezone, a full list is available
    [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). You
    will want to take note of the text in the _TZ Identifer_ column - e.g.
    `America/Los_Angeles` - for the next step.

    7. Write the following contents to a file named `docker-compose.yml`:

        ```yaml title="docker-compose.yml" hl_lines="8 10"
        version: "3"
          services:
            tcm:
              image: "ghcr.io/titlecardmaker/titlecardmaker-webui:latest"
              container_name: titlecardmaker
              restart: unless-stopped
              environment:
                - TZ=America/Los_Angeles # (1)!
              volumes:
                - ~/Your/Install/Directory/TitleCardMaker/config:/config # (2)!
              ports:
                - 4242:4242
              networks:
                - docker
        networks:
          docker:
            external: true
        ```

        1. Replace this with your timezone.
        2. Replace this with your install directory.

    8. Create (and launch) the Docker container by executing the following
    command.

        === ":material-linux: Linux"

            ```bash
            docker compose up -d
            ```

        === ":material-apple: MacOS"

            ```bash
            docker compose up -d
            ```

        === ":material-powershell: Windows (Powershell)"

            ```bash
            docker compose up -d
            ```

        === ":material-microsoft-windows: Windows (Non-Powershell)"

            ```bash
            docker compose up -d
            ```

=== ":material-docker: Docker"

    1. Open a terminal[^1] of your choice, and go to your desired install
    location.

        ??? example "Example"

            === ":material-linux: Linux"

                ```bash
                cd "~/Your/Install/Directory/TitleCardMaker"
                ```

            === ":material-apple: MacOS"

                ```bash
                cd "~/Your/Install/Directory/TitleCardMaker"
                ```

            === ":material-powershell: Windows (Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\TitleCardMaker'
                ```

            === ":material-microsoft-windows: Windows (Non-Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\TitleCardMaker'
                ```

    2. In this directory, create a subfolder called `config` by executing the
    following command:

        === ":material-linux: Linux"

            ```bash
            mkdir config
            ```

        === ":material-apple: MacOS"

            ```bash
            mkdir config
            ```

        === ":material-powershell: Windows (Powershell)"

            ```bash
            mkdir config
            ```

        === ":material-microsoft-windows: Windows (Non-Powershell)"

            ```bash
            mkdir config
            ```

    3. We now need to make sure this directory has the correct permissions
    assigned to it.

        === ":material-linux: Linux"

            With the Group and User ID that you would like TCM to execute with,
            run the following command:

            ```bash
            sudo chown -R {group}:{user} ./config # (1)!
            ```

            1. Replace `{group}` and `{user}` with the actual group and user (or
            their ID's) - e.g. `99:100`.

        === ":material-apple: MacOS"

            With the Group and User ID that you would like TCM to execute with,
            run the following command:

            ```bash
            sudo chown -R {group}:{user} ./config # (1)!
            ```

            1. Replace `{group}` and `{user}` with the actual group and user (or
            their ID's) - e.g. `99:100`.

        === ":material-powershell: Windows (Powershell)"

            Changing the permissions is (generally) not necessary on Windows.

        === ":material-microsoft-windows: Windows (Non-Powershell)"

            Changing the permissions is (generally) not necessary on Windows.

    4. Follow [these](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token#creating-a-personal-access-token-classic)
    instructions to get a __classic__ personal access token (PAT). Check the
    `read:packages` checkbox in the third section from the top.

        ??? question "Why is this necessary?"

            Because the repository is private, accessing the Docker container
            requires authentication. You _can_ download the zipped code from the
            website, but this makes getting updates difficult.

            A PAT is required instead of a password because GitHub does not
            allow passwords to be used from the command line.

        ??? warning "Security Warning"

            Keep this access code private, as it can be used to access your
            GitHub account.

    5. Store these login credentials in Docker with the following command. Type
    your GitHub username, and enter the PAT from Step 4 as the password.

        === ":material-linux: Linux"

            ```bash
            docker login ghcr.io
            ```

        === ":material-apple: MacOS"

            ```bash
            docker login ghcr.io
            ```

        === ":material-powershell: Windows (Powershell)"

            ```bash
            docker login ghcr.io
            ```

        === ":material-microsoft-windows: Windows (Non-Powershell)"

            ```bash
            docker login ghcr.io
            ```

    6. Determine your timezone, a full list is available
    [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). You
    will want to take note of the text in the _TZ Identifer_ column - e.g.
    `America/Los_Angeles` - for the next step.

    3. Create (and launch) the Docker container by executing the following
    command[^2] - make sure to replace the install directory and timezone with
    _your_ directory (from Step 2) and timezone (from Step 6).

        === ":material-linux: Linux"

            ```bash
            docker run -itd --net="bridge" -v "~/Your/Install/Directory/TitleCardMaker/config/":"/config/" -e TZ="America/Los_Angeles" -p 4242:4242 --name "TitleCardMaker" "ghcr.io/collinheist/titlecardmaker-webui:latest"
            ```

        === ":material-apple: MacOS"

            ```bash
            docker run -itd --net="bridge" -v "~/Your/Install/Directory/TitleCardMaker/config/":"/config/" -e TZ="America/Los_Angeles" -p 4242:4242 --name "TitleCardMaker" "ghcr.io/collinheist/titlecardmaker-webui:latest"
            ```

        === ":material-powershell: Windows (Powershell)"

            ```bash
            docker run -itd --net="bridge" -v "C:/Your/Install/Directory/TitleCardMaker/config":"/config/" -e TZ="America/Los_Angeles" -p 4242:4242 --name "TitleCardMaker" "ghcr.io/collinheist/titlecardmaker-webui:latest"
            ```

        === ":material-microsoft-windows: Windows (Non-Powershell)"

            ```bash
            docker run -itd --net="bridge" -v "C:/Your/Install/Directory/TitleCardMaker/config":"/config/" -e TZ="America/Los_Angeles" -p 4242:4242 --name "TitleCardMaker" ""ghcr.io/collinheist/titlecardmaker-webui:latest"
            ```

=== ":material-language-python: Non-Docker"

    ### Downloading ImageMagick

    === ":material-linux: Linux"

        Depending on your Linux distro, you might be able to use whatever package
        manager comes installed. Some of the common installations are detailed
        [here](https://www.xmodulo.com/install-imagemagick-linux.html). For
        example, the following command works on Debian and Ubuntu:

        ```bash
        sudo apt-get install imagemagick
        ```

        If this is not available, then you must use Docker.

    === ":material-apple: MacOS"

        Follow the ImageMagick installation and setup instructions listed
        [here](https://imagemagick.org/script/download.php).

    === ":material-powershell: Windows (Powershell)"

        Download the Windows Binary Release from the
        [ImageMagick website](https://imagemagick.org/script/download.php#windows).

        During the installation, be sure to check the _Add application directory to
        your system path_ and _Install legacy utilities (e.g. convert) boxes_. The
        other options are optional.

    === ":material-microsoft-windows: Windows (Non-Powershell)"

        Download the Windows Binary Release from the
        [ImageMagick website](https://imagemagick.org/script/download.php#windows).

        During the installation, be sure to check the _Add application directory to
        your system path_ and _Install legacy utilities (e.g. convert) boxes_. The
        other options are optional.

    ### Downloading the Code

    1. Open a terminal[^1] of your choice, and go to your desired install
    location.

        ??? example "Example"

            === ":material-linux: Linux"

                ```bash
                cd "~/Your/Install/Directory/"
                ```

            === ":material-apple: MacOS"

                ```bash
                cd "~/Your/Install/Directory/"
                ```

            === ":material-powershell: Windows (Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\'
                ```

            === ":material-microsoft-windows: Windows (Non-Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\'
                ```

    2. Follow [these](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token#creating-a-personal-access-token-classic)
    instructions to get a __classic__ personal access token (PAT) so that you can
    retrieve the TCM code from git. Check the `repo` scope section. Copy this code.

        ??? question "Why is this necessary?"

            Because the repository is private, the `git clone` command requires
            authentication. You _can_ download the zipped code from the website,
            but this makes getting updates difficult.

            A PAT is required instead of a password because GitHub does not allow
            passwords to be used from the command line.

        ??? warning "Security Warning"

            Keep this access code private, as it can be used to access your GitHub
            account.

    3. In your install directory from Step 1, clone the repository with:

        ```bash
        git clone https://github.com/TitleCardMaker/TitleCardMaker-WebUI.git
        ```

    4. Enter your account Username and the PAT from Step 2. The TCM code will
    now be downloaded into a subdirectory named `TitleCardMaker-WebUI`.

    ### Running TitleCardMaker

    1. Enter the TCM installation directory that was _just_ created.

        ??? example "Example"

            === ":material-linux: Linux"

                ```bash
                cd "~/Your/Install/Directory/TitleCardMaker-WebUI"
                ```

            === ":material-apple: MacOS"

                ```bash
                cd "~/Your/Install/Directory/TitleCardMaker-WebUI"
                ```

            === ":material-powershell: Windows (Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\TitleCardMaker-WebUI'
                ```

            === ":material-microsoft-windows: Windows (Non-Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\TitleCardMaker-WebUI'
                ```

    2. Create a subfolder named `config`.

        === ":material-linux: Linux"

            ```bash
            mkdir config
            ```

        === ":material-apple: MacOS"

            ```bash
            mkdir config
            ```

        === ":material-powershell: Windows (Powershell)"

            ```bash
            mkdir config
            ```

        === ":material-microsoft-windows: Windows (Non-Powershell)"

            ```bash
            mkdir config
            ```

    3. Run the following commands to install the required Python packages and
    launch the TCM interface.

        === ":material-linux: Linux"

            ```bash
            pipenv install
            ```

            ```bash
            pipenv run uvicorn app-main:app --host "0.0.0.0" --port 4242
            ```

        === ":material-apple: MacOS"

            ```bash
            pipenv install
            ```

            ```bash
            pipenv run uvicorn app-main:app --host "0.0.0.0" --port 4242
            ```

        === ":material-powershell: Windows (Powershell)"

            ```bash
            pipenv install
            ```

            ```bash
            pipenv run uvicorn app-main:app --host "0.0.0.0" --port 4242
            ```

        === ":material-microsoft-windows: Windows (Non-Powershell)"

            ```bash
            pipenv install
            ```

            ```bash
            pipenv run uvicorn app-main:app --host "0.0.0.0" --port 4242
            ```
    
    4. You should see an output _like_ this:
    
        ```log
        INFO:     Started server process [17385]
        INFO:     Waiting for application startup.
        INFO:     Application startup complete.
        INFO:     Uvicorn running on http://0.0.0.0:4242 (Press CTRL+C to quit)
        ```

    ??? failure "Interface not accessible?"

        If your log shows

        ```log
        INFO:     Application startup complete.
        ```
        
        And neither the `http://0.0.0.0:4242`, `http://localhost:4242`, or your
        local IP address URL load into the TCM UI, then replace the `0.0.0.0`
        part of the previous command with your _local_ IP address - e.g.
        `192.168.0.10`. If you still have issues, reach out on the Discord.

!!! success "Success"

    TitleCardMaker is now accessible at the `http://0.0.0.0:4242` or
    `http://localhost:4242/` URL. It may also be at your LAN IP.

## Getting Started

The following pages of the tutorial are designed to walk you through all of the
basics of using TitleCardMaker. It covers each step between installing TCM up
through creating example Title Cards. You can skip directly to
[Configuring Connections](./connections/index.md).

It is designed for __completely new users__ of TCM, but is still helpful for
those migrating from TCM v1.0 (the command line tool). For more detailed
information about specific aspects of TitleCardMaker, look at the
[User Guide](../user_guide/index.md).


[^1]:
    - For Linux, I will assume you know what a Terminal is :wink:.
    - For Mac users, this is `Terminal` and can be found via the Spotlight
    - For Windows users, this is `Command Prompt` or `PowerShell`. Both can be
    accessed from the search menu

[^2]:
    The exact purpose of this command breaks down as follow:
    ```bash
    docker run -itd ^ # (1)!
        --net="bridge" ^ # (2)!
        -v ".../config":"/config/" ^ # (3)!
        -e TZ="America/Los_Angeles" ^ # (4)!
        -p 4242:4242 ^ # (5)!
        --name "TitleCardMaker" ^ # (6)!
        "ghcr.io/collinheist/titlecardmaker-webui:latest"
    ```

    1. Launch the container in the background.
    2. Ensure that TCM has access to the ports of your other Docker
    containers.
    3. Make the specified directory available inside the container.
    4. Set the internal timezone equal to your local timezone.
    5. Make the TCM WebUI accessible at port 4242 on your machine.
    6. Name the container TitleCardMaker.

*[PAT]: Personal Access Token
