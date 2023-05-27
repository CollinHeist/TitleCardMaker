# Local Linux Installation
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

Follow [this guide](https://docs.python-guide.org/starting/install3/osx/)
to install Python with Homebrew.

### Installing git

??? note "Git Already Installed?"

    If you believe git is already installed, you can quickly check this
    (and that you have a suitable version), by running the following
    command:

    ```bash
    git --version
    ```

Execute the following command:

```bash
brew install git
```

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

*[Media Server]: Plex, Emby, or Jellyfin
*[Media Servers]: Plex, Emby, or Jellyfin
*[TCM]: TitleCardMaker
*[TMDb]: TheMovieDatabase