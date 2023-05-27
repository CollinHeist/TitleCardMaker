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

1. Go to the [Python website](https://www.python.org/downloads/windows/),
and download the installer for the latest version of Python 3.10.
2. Run the installer, and make sure to select the `Add to PATH`
checkbox during installation.
3. Enable PowerShell scripts by following [these](https://windowsloop.com/enable-powershell-scripts-execution-windows-10) instructions.

### Installing git

??? note "Git Already Installed?"

    If you believe git is already installed, you can quickly check this
    (and that you have a suitable version), by running the following
    command:

    ```bash
    git --version
    ```

1. Download the 64-bit standalone installer from
[here](https://git-scm.com/download/win).
2. Run the installer, and click through until you get to the "Choosing
the default editor used by Git" step.

    !!! tip "Recommendation"

        I recommend changing the default editor to something other than
        Vim (such as Sublime Text, Notepad++, etc.).

3. Continue clicking through until you get to the "Adjusting your PATH
environment" step and make sure that the (Recommended) option of "Git
from the command line and also from 3rd-party software" option is
selected.

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