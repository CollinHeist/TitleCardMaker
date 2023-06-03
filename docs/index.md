# Welcome to TitleCardMaker
TitleCardMaker is a program and Docker container written in Python that
automates the creation of customized title cards for use in personal
media server services like Plex, Jellyfin, or Emby.

??? question "What is a Title Card?"

    A Title Card is a thumbnail image for an Episode used to add a
    unique look within a personal media server like Emby, Jellyfin, or
    Plex. Some Series have "official" Title Cards featured in the
    Episode itself.

!!! warning "Under Construction"

    This documentation is actively being developed.

# Early Access

!!! info "Availability of Early Access"

    While the TitleCardMaker Web UI is under development, it is only accessible
    to project Sponsors.

## Downloading the Code

Sponsors of the project will be invited to a [private GitHub
repository](https://github.com/CollinHeist/TitleCardMaker-WebUI/). These steps
will walk you through getting the code from that repository.

1. After being invited, you will recieve an email at your GitHub's associated
email address, open it and accept the invitation to collaborate (while signed
into your GitHub account).

2. Follow [these](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token#creating-a-personal-access-token-classic)
instructions to get a __classic__ personal access token (PAT) so that you can
retrieve the TCM code from git. Copy this code.

    ??? question "Why is this necessary?"

        Because the repository is Private, the `git clone` command requires the
        website, but this makes getting updates difficult. authentication. You
        _can_ download the zipped code from the website, but this makes getting
        updates difficult.

        A PAT is required instead of a password because GitHub does not allow
        passwords to be used from the command line.

    ??? warning "Security Warning"

        Keep this access code private, as it can be used to access your GitHub
        account.

3. Open a terminal of your choice, and go to the desired install location. Then
clone the repository with:

    ```bash
    git clone https://github.com/CollinHeist/TitleCardMaker-WebUI.git
    ```

4. Enter your account Username and the PAT from Step 2. The TCM code
will now be downloaded into that directory.

## Running TitleCardMaker
1. After the zipped code has been downloaded, unzip it wherever you'd like the
installation to live. Open the unzipped folder.
2. Navigate to the installation directory within the command line.

    ??? example "Example"

        === ":material-linux: Linux"

            ```bash
            cd "~/Your/Install/Directory" # (1)!
            ```

            1. Replace `~/Your/Install/Directory` with the path to the directory
            from the above Step 2.

        === ":material-apple: MacOS"

            ```bash
            cd "~/Your/Install/Directory" # (1)!
            ```

            1. Replace `~/Your/Install/Directory` with the path to the directory
            from the above Step 2.

        === ":material-powershell: Windows (Powershell)"

            ```bash
            cd 'C:\Your\Install\Directory' <#(1)#>
            ```

            1. Replace `~/Your/Install/Directory` with the path to the directory
            from the above Step 2.

        === ":material-microsoft-windows: Windows (Non-Powershell)"

            ```bash
            cd 'C:\Your\Install\Directory' # (1)!
            ```

            1. Replace `~/Your/Install/Directory` with the path to the directory
            from the above Step 2.

3. Within the main installation directory, create the required folders for
TCM - these are the `assets`, `cards`, `logs`, and `source` directories - by
executing the following command(s):

    === ":material-linux: Linux"

        ```bash
        mkdir assets cards logs source
        ```

    === ":material-apple: MacOS"

        ```bash
        mkdir assets cards logs source
        ```

    === ":material-powershell: Windows (Powershell)"

        ```bash
        mkdir assets; mkdir cards; mkrdir logs; mkdir source;
        ```

    === ":material-microsoft-windows: Windows (Non-Powershell)"

        ```bash
        mkdir assets; mkdir cards; mkrdir logs; mkdir source;
        ```

6. We now need to make sure these directories have the correct permissions
assigned to them. 

    === ":material-linux: Linux"

        With the Group and User ID that you would like TCM to execute with, run
        the following command:

        ```bash
        sudo chown -R {group}:{user} ./assets/ ./cards ./logs ./source # (1)!
        ```

        1. Replace `{group}` and `{user}` with the actual group and user (or
        their ID's) - e.g. `99:100`.

    === ":material-apple: MacOS"

        With the Group and User ID that you would like TCM to execute with, run
        the following command:

        ```bash
        sudo chown -R {group}:{user} ./assets ./cards ./logs ./source # (1)!
        ```

        1. Replace `{group}` and `{user}` with the actual group and user (or
        their ID's) - e.g. `99:100`.

    === ":material-powershell: Windows (Powershell)"

        Changing the permissions is not necessary on Windows.

    === ":material-microsoft-windows: Windows (Non-Powershell)"

        Changing the permissions is not necessary on Windows.

    !!! info "Choice of Installation"

        You now have the choice of building and running the Docker container
        yourself, or launching the Python script directly. Those who wish to (or
        must) use a Docker container, continue
        [here](#building-the-docker-container). The Python steps continue below.

7. Run the following command to install the required Python packages and launch
the TCM interface.

    === ":material-linux: Linux"

        ```bash
        pipenv install; # (1)!
        pipenv run uvicorn app-main:app --host "0.0.0.0" --port 4242 # (2)!
        ```

        1. This installs the required Python dependencies
        2. This launches a webserver at your `{your IP}:4242` which the TCM Web
        UI is accessible at.

    === ":material-apple: MacOS"

        ```bash
        pipenv install; # (1)!
        pipenv run uvicorn app-main:app --host "0.0.0.0" --port 4242 # (2)!
        ```

        1. This installs the required Python dependencies
        2. This launches a webserver at your `{your IP}:4242` which the TCM Web
        UI is accessible at.

    === ":material-powershell: Windows (Powershell)"

        ```bash
        pipenv install; <#(1)#>
        pipenv run uvicorn app-main:app --host "0.0.0.0" --port 4242 <#(2)#>
        ```

        1. This installs the required Python dependencies
        2. This launches a webserver at your `{your IP}:4242` which the TCM Web
        UI is accessible at.

    === ":material-microsoft-windows: Windows (Non-Powershell)"

        ```bash
        pipenv install; # (1)!
        pipenv run uvicorn app-main:app --host "0.0.0.0" --port 4242 # (2)!
        ```

        1. This installs the required Python dependencies
        2. This launches a webserver at your `{your IP}:4242` which the TCM Web
        UI is accessible at.

!!! success "Success"

    TitleCardMaker is now accessible at the `http://0.0.0.0:4242` or
    `http://localhost:4242/` URL.

## Building the Docker Container

1. Build the Docker container by executing the following command:

    === ":material-linux: Linux"

        ```bash
        docker build -t "titlecardmaker" . # (1)!
        ```

        1. This will label the built container `titlecardmaker`.

    === ":material-apple: MacOS"

        ```bash
        docker build -t "titlecardmaker" . # (1)!
        ```

        1. This will label the built container `titlecardmaker`.

    === ":material-powershell: Windows (Powershell)"

        ```bash
        docker build -t "titlecardmaker" . <#(1)#>
        ```

        1. This will label the built container `titlecardmaker`.

    === ":material-microsoft-windows: Windows (Non-Powershell)"

        ```bash
        docker build -t "titlecardmaker" . # (1)!
        ```

        1. This will label the built container `titlecardmaker`.

2. Launch the Docker container by executing the following command:

    === ":material-linux: Linux"

        ```bash
        docker run -itd `# (1)!` \
            --net="bridge" `# (2)!` \
            -v "$(pwd)/logs/":"/maker/logs/" \
            -v "$(pwd)/assets/":"/config/assets/" \
            -v "$(pwd)/source/":"/config/source/" \
            -v "$(pwd)/cards/":"/config/cards/" `# (3)!` \
            -p 4242:4242 `# (4)!` \
            titlecardmaker
        ```

        1. This launches the container in the background.
        2. This makes the TCM ports available to other Docker containers.
        3. These `-v` commands make your directories accessible inside the
        container.
        4. This exposes the _internal_ `4242` port outside the container, so
        that you can access it on your machine.

    === ":material-apple: MacOS"

        ```bash
        docker run -itd `# (1)!` \
            --net="bridge" `# (2)!` \
            -v "$(pwd)/logs/":"/maker/logs/" \
            -v "$(pwd)/assets/":"/config/assets/" \
            -v "$(pwd)/source/":"/config/source/" \
            -v "$(pwd)/cards/":"/config/cards/" `# (3)!` \
            -p 4242:4242 `# (4)!` \
            titlecardmaker
        ```

        1. This launches the container in the background.
        2. This makes the TCM ports available to other Docker containers.
        3. These `-v` commands make your directories accessible inside the
        container.
        4. This exposes the _internal_ `4242` port outside the container, so
        that you can access it on your machine.

    === ":material-powershell: Windows (Powershell)"

        ```bash
        docker run -itd <#(1)#> `
            --net="bridge" <#(2)#> `
            -v "$(pwd)\logs":"/maker/logs/" `
            -v "$(pwd)\assets":"/config/assets/" `
            -v "$(pwd)\source":"/config/source/" `
            -v "$(pwd)\cards":"/config/cards/" <#(3)#> `
            -p 4242:4242 <#(4)#> `
            titlecardmaker
        ```

        1. This launches the container in the background.
        2. This makes the TCM ports available to other Docker containers.
        3. These `-v` commands make your directories accessible inside the
        container.
        4. This exposes the _internal_ `4242` port outside the container, so
        that you can access it on your machine.

    === ":material-microsoft-windows: Windows (Non-Powershell)"

        ```bash
        docker run -itd `# (1)!` ^
            --net="bridge" `# (2)!` ^
            -v "$(pwd)\logs":"/maker/logs/" ^
            -v "$(pwd)\assets":"/config/assets/" ^
            -v "$(pwd)\source":"/config/source/" ^
            -v "$(pwd)\cards":"/config/cards/" `# (3)!` ^
            -p 4242:4242 `# (4)!` ^
            titlecardmaker
        ```

        1. This launches the container in the background.
        2. This makes the TCM ports available to other Docker containers.
        3. These `-v` commands make your directories accessible inside the
        container.
        4. This exposes the _internal_ `4242` port outside the container, so
        that you can access it on your machine.

!!! success "Success"

    TitleCardMaker is now accessible at the `http://0.0.0.0:4242` or
    `http://localhost:4242/` URL.

# Getting Started
!!! info "Detailed Tutorial"

    For more detailed tutorials that take step-by-step through the installation
    and setup of TitleCardMaker, continue to the Tutorial pages.

TitleCardMaker is designed to for an easy "out of the box" setup. The basic
steps are as follows:

1. Install TitleCardMaker (via Docker or locally)
2. Set up your Connections to your other services - such as Sonarr, TMDb, Plex,
Emby, Jellyfin, or Tautulli.
3. Start adding Series to TitleCardMaker - this can be done manually, or with
[Syncs](./getting_started/first_sync/index.md).
4. Customize the look and style of Title Cards to your liking.

*[PAT]: Personal Access Token