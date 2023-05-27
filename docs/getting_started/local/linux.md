# Local Linux Installation

!!! warning "Linux Compatability"

    Some Linux distros __do not__ support ImageMagick - which is a
    requirement for TitleCardMaker - in this case the [Docker
    installation](../docker/index.md) is required.

## Background
Installing TitleCardMaker locally, instead of in a Docker container,
requires a few additional pieces of software, these are:

- Python
- git (_recommended_)
- Pip
- Pipenv
- ImageMagick

The installation of these, as well as TitleCardMaker itself, will be
covered in this step.

## Instructions
### Installing Python

??? note "Python Already Installed?"

    If you believe Python is already installed, you can quickly check
    this (and that you have a suitable version), by running the
    following command:

    ```bash
    python3 --version
    ```

    This should output _at least_ `Python 3.9`.

Given the wide diversity of Linux Distros, it is not feasible to cover
the installation of Python in all circumstances. [This
guide](https://realpython.com/installing-python/#how-to-install-python-on-linux)
covers some common installation methods.

### Installing git

??? note "Git Already Installed?"

    If you believe git is already installed, you can quickly check this
    (and that you have a suitable version), by running the following
    command:

    ```bash
    git --version
    ```

Follow [these](https://git-scm.com/download/linux) instructions.

### Upgrading Pip

Execute the following command:

```bash
python3 -m pip install --upgrade pip
```

### Installing Pipenv

Execute the following command:

```bash
pip3 install pipenv
```

### Installing ImageMagick

=== "Linux"

    Depending on your Linux distro, you might be able to use
    whatever package manager comes installed. Some of the common
    installations are detailed
    [here](https://www.xmodulo.com/install-imagemagick-linux.html).

=== "MacOS"

    ```bash
    brew install imagemagick
    ```

=== "Windows (Powershell)"

    1. Download the Windows Binary Release from
    [here](https://imagemagick.org/script/download.php#windows).
    2. Follow the installer, be sure to check the `Add application
    directory to your system path` and the `Install legacy utilities
    (e.g. convert)` checkboxes during installation.

=== "Windows (Non-Powershell)"

    ```bash
    pipenv install; # (1)
    pipenv run uvicorn app-main:app --host "0.0.0.0" --port 4242 # (2)
    ```

    1. This installs the required Python dependencies
    2. This launches a webserver at your `{your IP}:4242` which
    the TCM Web UI is accessible at.

*[Media Server]: Plex, Emby, or Jellyfin
*[Media Servers]: Plex, Emby, or Jellyfin
*[TCM]: TitleCardMaker
*[TMDb]: TheMovieDatabase