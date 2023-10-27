---
title: Installing TitleCardMaker Locally
decription: >
    How to install TitleCardMaker (and all of the dependencies) outside of a 
    Docker container.
tags:
    - Tutorial
---

# Local Installation

!!! warning "Linux Compatability"

    Some Linux distros either do not support ImageMagick - which is a
    requirement for TitleCardMaker. In this case the
    [Docker installation](./docker/index.md) is required.

## Background
Installing TitleCardMaker locally, instead of in a Docker container,
requires a few additional pieces of software, these are:

- Python
- git
- Pip
- Pipenv
- ImageMagick

The installation of these, as well as TitleCardMaker itself, will be covered
below.

## Instructions
### Installing Python

??? note "Python Already Installed?"

    If you believe Python is already installed, you can quickly check this (and
    that you have a suitable version), by running the following command:

    ```bash
    python3 --version
    ```

    This should output _at least_ `Python 3.9`, ideally `3.11` or higher.

=== ":material-linux: Linux"

    Given the wide diversity of Linux Distros, it is not feasible to cover the
    installation of Python in all circumstances.
    [This guide](https://realpython.com/installing-python/#how-to-install-python-on-linux)
    covers some common installation methods.

=== ":material-apple: MacOS"

    Python comes pre-installed on MacOS, but it can be updated with Homebrew by
    running the following command:

    ```bash
    brew update && brew upgrade python
    ```

=== ":material-microsoft-windows: Windows"

    1. Go to the [Python website](https://www.python.org/downloads/windows/),
    and download the installer for the latest version of Python 3.10.
    2. Run the installer, and make sure to select the `Add to PATH` checkbox 
    during installation.
    3. Enable PowerShell scripts by following [these](https://windowsloop.com/enable-powershell-scripts-execution-windows-10) instructions.

### Installing git

??? note "Git Already Installed?"

    If you believe git is already installed, you can quickly check this by
    running the following command:

    ```bash
    git --version
    ```

=== ":material-linux: Linux"

    Follow [these](https://git-scm.com/download/linux) distro-specific
    instructions.

=== ":material-apple: MacOS"

    ```bash
    brew install git
    ```

=== ":material-microsoft-windows: Windows"

    1. Download the 64-bit standalone installer from
    [here](https://git-scm.com/download/win).
    2. Run the installer, and click through until you get to the "Choosing the
    default editor used by Git" step.

        !!! tip "Recommendation"

            I recommend changing the default editor to something other than
            Vim (such as Sublime Text, Notepad++, etc.).

    3. Continue clicking through until you get to the "Adjusting your PATH
    environment" step and make sure that the (Recommended) option of "Git from
    the command line and also from 3rd-party software" option is selected.


### Upgrading Pip

Execute the following command:

```bash
python3 -m pip install --upgrade pip
```

### Installing Pipenv

TitleCardMaker uses `pipenv` to install the external Python libraries that are
required. Install pipenv by executing the following command:

```bash
pip3 install pipenv
```

Then install the required libraries (dependencies) by executing:

```bash
$ pipenv install
```

!!! failure "Command Failure"

    If this command fails, it is possible `pipenv` has not been added to your
    PATH. Retry this by prefacing the command with `python3 -m`, like so:

    ```bash
    python3 -m pipenv install
    ```

### Installing ImageMagick

ImageMagick is the image manipulation and creation library that TCM uses to
create the Title Cards.

=== ":material-linux: Linux"

    Depending on your Linux distro, you might be able to use whatever package
    manager comes installed. Some of the common installations are detailed
    [here](https://www.xmodulo.com/install-imagemagick-linux.html). It is also
    worth checking the ImageMagick website
    [here](https://imagemagick.org/script/download.php).

    If there is no pre-installed package, and you don't want to use the
    [Docker container](./docker/index.md), then you _can_ build ImageMagick
    yourself. This process is much more complicated and error-prone, but is
    described [here](https://imagemagick.org/script/install-source.php).

=== ":material-apple: MacOS"

    Execute the following command:

    ```bash
    brew install imagemagick
    ```

=== ":material-microsoft-windows: Windows"

    1. Download the Windows Binary Release from
    [here](https://imagemagick.org/script/download.php#windows).
    2. Follow the installer, be sure to check the `Add application directory to
    your system path` and the `Install legacy utilities (e.g. convert)`
    checkboxes during installation.

Verify it is installed by executing the following:

```bash
magick logo: logo.gif
```

This should create a `logo.gif` file of the ImageMagick wizard in that
directory.

### Launching TitleCardMaker

With all the required packages and software installed, you are ready to launch
TitleCardMaker. This can be done by executing the following command:

<!-- termynal -->
```bash
$ pipenv run uvicorn app-main:app --host "0.0.0.0" --port 4242
[DEBUG] Dumped Preferences to "[...]/TitleCardMaker/config/config.pickle"..
INFO:     Started server process [4072]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:4242 (Press CTRL+C to quit)
```

This launches the TitleCardMaker web interface, and you will be able to
access it by going to `http://0.0.0.0:4242` or `http://localhost:4242`
in a browser. 

!!! success "Success"

    Installation is complete, and TitleCardMaker is ready to be
    configured.
