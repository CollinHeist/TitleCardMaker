# Welcome to TitleCardMaker
TitleCardMaker is a program and Docker container written in Python that
automates the creation of customized title cards for use in personal
media server services like Plex, Jellyfin, or Emby.

??? question "What is a Title Card?"

    A Title Card is a thumbnail image for an Episode used to add a
    unique look within a personal media server like Emby, Jellyfin, or
    Plex. Some Series have "official" Title Cards featured in the
    Episode itself.

...

# Early Access

!!! info "Availability of Early Access"

    While the TitleCardMaker Web UI is under development, it is only
    accessible to project Sponsors.

## Downloading the Code

Sponsors of the project will be invited to a [private GitHub
repository](https://github.com/CollinHeist/TitleCardMaker-WebUI/). These
steps will walk you through getting the code from that repository.

1. After being invited, you will recieve an email at your GitHub's
associated email address, open it and accept the invitation to
collaborate (while signed into your GitHub account).
2. Once you have access to the repository, the code can be accessed by 
clicking the green `<> Code` button on the repository home page - from
that dropdown, click `Download ZIP`.

## Running TitleCardMaker
1. After the zipped code has been downloaded, unzip it wherever you'd
like the installation to live. Open the unzipped folder.
2. Navigate to the installation directory within the command line:

    === "Linux"

        ```bash
        cd "~/Your/Install/Directory" # (1)
        ```

        1. Replace `~/Your/Install/Directory` with the path to the directory
        from the above Step 2.

    === "MacOS"

        ```bash
        cd "~/Your/Install/Directory" # (1)
        ```

        1. Replace `~/Your/Install/Directory` with the path to the directory
        from the above Step 2.

    === "Windows (Powershell)"

        ```bash
        cd 'C:\Your\Install\Directory' <#(1)#>
        ```

        1. Replace `~/Your/Install/Directory` with the path to the directory
        from the above Step 2.

    === "Windows (Non-Powershell)"

        ```bash
        cd 'C:\Your\Install\Directory' # (1)
        ```

        1. Replace `~/Your/Install/Directory` with the path to the directory
        from the above Step 2.

3. Within the main installation directory, create the required folders
for TCM - these are the `cards`, `logs`, and `source` directories - by
executing the following commands:

    === "Linux"

        ```bash
        mkdir cards logs source
        ```

    === "MacOS"

        ```bash
        mkdir cards logs source
        ```

    === "Windows (Powershell)"

        ```bash
        mkdir cards; mkrdir logs; mkdir source;
        ```

    === "Windows (Non-Powershell)"

        ```bash
        mkdir cards; mkrdir logs; mkdir source;
        ```

6. We now need to make sure these directories have the correct
permissions assigned to them. 

    === "Linux"

        With the Group and User ID that you would like TCM to execute
        with, run the following command:

        ```bash
        sudo chown -R {group}:{user} ./cards ./logs ./source # (1)
        ```

        1. Replace `{group}` and `{user}` with the actual group and user
        (or their ID's) - e.g. `99:100`.

    === "MacOS"

        With the Group and User ID that you would like TCM to execute
        with, run the following command:

        ```bash
        sudo chown -R {group}:{user} ./cards ./logs ./source # (1)
        ```

        1. Replace `{group}` and `{user}` with the actual group and user
        (or their ID's) - e.g. `99:100`.

    === "Windows (Powershell)"

        Changing the permissions is not necessary on Windows.

    === "Windows (Non-Powershell)"

        Changing the permissions is not necessary on Windows.

    !!! info "Choice of Installation"

        You now have the choice of building and running the Docker
        container yourself, or launching the Python script directly.
        Those who wish to (or must) use a Docker container, continue
        [here](#building-the-docker-container). The Python steps
        continue below.

7. Run the following command to install the required Python packages
and launch the TCM interface.

    === "Linux"

        ```bash
        pipenv install; # (1)
        pipenv run uvicorn app-main:app --host "0.0.0.0" --port 4242 # (2)
        ```

        1. This installs the required Python dependencies
        2. This launches a webserver at your `{your IP}:4242` which
        the TCM Web UI is accessible at.

    === "MacOS"

        ```bash
        pipenv install; # (1)
        pipenv run uvicorn app-main:app --host "0.0.0.0" --port 4242 # (2)
        ```

        1. This installs the required Python dependencies
        2. This launches a webserver at your `{your IP}:4242` which
        the TCM Web UI is accessible at.

    === "Windows (Powershell)"

        ```bash
        pipenv install; <#(1)#>
        pipenv run uvicorn app-main:app --host "0.0.0.0" --port 4242 <#(2)#>
        ```

        1. This installs the required Python dependencies
        2. This launches a webserver at your `{your IP}:4242` which
        the TCM Web UI is accessible at.

    === "Windows (Non-Powershell)"

        ```bash
        pipenv install; # (1)
        pipenv run uvicorn app-main:app --host "0.0.0.0" --port 4242 # (2)
        ```

        1. This installs the required Python dependencies
        2. This launches a webserver at your `{your IP}:4242` which
        the TCM Web UI is accessible at.

!!! success "Success"

    TitleCardMaker is now accessible at the `http://0.0.0.0:4242` or
    `http://localhost:4242/` URL.

## Building the Docker Container

1. Build the Docker container by executing the following command:

    === "Linux"

        ```bash
        docker build -t "titlecardmaker" . # (1)
        ```

        1. This will label the built container `titlecardmaker`.

    === "MacOS"

        ```bash
        docker build -t "titlecardmaker" . # (1)
        ```

        1. This will label the built container `titlecardmaker`.

    === "Windows (Powershell)"

        ```bash
        docker build -t "titlecardmaker" . <#(1)#>
        ```

        1. This will label the built container `titlecardmaker`.

    === "Windows (Non-Powershell)"

        ```bash
        docker build -t "titlecardmaker" . # (1)
        ```

        1. This will label the built container `titlecardmaker`.

2. Launch the Docker container by executing the following command:

    === "Linux"

        ```bash
        docker run -itd `# (1)` \
            --net="bridge" `# (2)` \
            -v "$(pwd)/logs/":"/maker/logs/" `# (3)` \
            -v "$(pwd)/source/":"/config/source/" `# (4)` \
            -v "$(pwd)/cards/":"/config/cards/" `# (5)` \
            -p 4242:4242 `# (6)` \
            titlecardmaker
        ```

        1. This launches the container in the background.
        2. This makes the TCM ports available to other Docker containers.
        3. The makes the TCM logs available outside the container.
        4. This mounts the source directory inside the container.
        5. The mounts the cards directory inside the container.
        6. This exposes the _internal_ `4242` port outside the
        container, so that you can access it on your machine.

    === "MacOS"

        ```bash
        docker run -itd `# (1)` \
            --net="bridge" `# (2)` \
            -v "$(pwd)/logs/":"/maker/logs/" `# (3)` \
            -v "$(pwd)/source/":"/config/source/" `# (4)` \
            -v "$(pwd)/cards/":"/config/cards/" `# (5)` \
            -p 4242:4242 `# (6)` \
            titlecardmaker
        ```

        1. This launches the container in the background.
        2. This makes the TCM ports available to other Docker containers.
        3. The makes the TCM logs available outside the container.
        4. This mounts the source directory inside the container.
        5. The mounts the cards directory inside the container.
        6. This exposes the _internal_ `4242` port outside the
        container, so that you can access it on your machine.

    === "Windows (Powershell)"

        ```bash
        docker run -itd <#(1)#> `
            --net="bridge" <# (2) #> `
            -v "$(pwd)\logs":"/maker/logs/" <#(3)#> `
            -v "$(pwd)\source":"/config/source/" <#(4)#> `
            -v "$(pwd)\cards":"/config/cards/" <#(5)#> `
            -p 4242:4242 <#(6)#> `
            titlecardmaker
        ```

        1. This launches the container in the background.
        2. This makes the TCM ports available to other Docker containers.
        3. The makes the TCM logs available outside the container.
        4. This mounts the source directory inside the container.
        5. The mounts the cards directory inside the container.
        6. This exposes the _internal_ `4242` port outside the
        container, so that you can access it on your machine.

    === "Windows (Non-Powershell)"

        ```bash
        docker run -itd `# (1)` ^
            --net="bridge" `# (2)` ^
            -v "$(pwd)\logs":"/maker/logs/" `# (3)` ^
            -v "$(pwd)\source":"/config/source/" `# (4)` ^
            -v "$(pwd)\cards":"/config/cards/" `# (5)` ^
            -p 4242:4242 `# (6)` ^
            titlecardmaker
        ```

        1. This launches the container in the background.
        2. This makes the TCM ports available to other Docker containers.
        3. The makes the TCM logs available outside the container.
        4. This mounts the source directory inside the container.
        5. The mounts the cards directory inside the container.
        6. This exposes the _internal_ `4242` port outside the
        container, so that you can access it on your machine.

!!! success "Success"

    TitleCardMaker is now accessible at the `http://0.0.0.0:4242` or
    `http://localhost:4242/` URL.

# Getting Started
!!! info "Detailed Tutorial"

    For more detailed tutorials that take step-by-step through the
    installation and setup of TitleCardMaker, continue to the __Getting
    Started - Tutorial__ pages.

TitleCardMaker is designed to for an easy "out of the box" setup. The
basic steps are as follows:

1. Install TitleCardMaker (via Docker or locally)
2. Set up your Connections to your other services - such as Sonarr, TMDb,
Plex, Emby, Jellyfin, or Tautulli.
3. Start adding Series to TitleCardMaker - this can be done manually, or
with [Syncs].
4. Customize the look and style of Title Cards to your liking.

*[Media Server]: Plex, Emby, or Jellyfin
*[Media Servers]: Plex, Emby, or Jellyfin
*[TCM]: TitleCardMaker
*[TMDb]: TheMovieDatabase