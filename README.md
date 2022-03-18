# TitleCardMaker
An automated title card maker for Plex.

## Table of Contents
- [Description](#description)
- [Getting Started](#getting-started)
- [Installation](#installation)
   - [Installing the Maker](#installing-the-maker)
   - [Python](#python)
   - [ImageMagick](#imagemagick)
   - [Sonarr](#sonarr)
- [Usage and Troubleshooting](#usage-and-troubleshooting)
- [Examples](#examples)
- [Contributing](#contributing)
- [Support](#support)

## Description

`TitleCardMaker` is a Python program intended to be invoked via the command-line to automate the creation of title cards, which are image previews of an episode, for use in personal media services like Plex, Emby, or Jellyfin.

The actual image creation is done using the open-source and free image library called [ImageMagick](https://imagemagick.org/). 

The Maker can be automated such that everything can be pulled without manual intervention (except for a few exceptions). Episode titles can be pulled from an instance of [Sonarr](https://sonarr.tv/), images and logos from [TheMovieDatabase](https://www.themoviedb.org/), and the maker can even automatically refresh Plex after new cards are created.

## Getting Started

1. Install TitleCardMaker and the required software - see [here](#installation) for details.
2. Create the top-level configuration file necessary to outline how the maker should interact with your services - see [here](https://github.com/CollinHeist/TitleCardMaker/wiki#configuring-the-titlecardmaker) for detailed instructions, or [here](https://github.com/CollinHeist/TitleCardMaker/wiki#complete-example) for an example file you can copy and fill out yourself.
3. Create the series YAML file(s) that list for which series you would like to create title cards for, as well as what those cards should look like - see [here](https://github.com/CollinHeist/TitleCardMaker/wiki/Series-YAML-Files) for details.
4. If you're inspired to create your own _types of cards_ (not just your own cards), see [here](https://github.com/CollinHeist/TitleCardMaker/wiki/Custom-Card-Types#creating-a-custom-card-type) for details on getting started.

> For more details on any particular aspect of the Maker, read the [Wiki](https://github.com/CollinHeist/TitleCardMaker/wiki).

## Installation
### Installing the Maker
#### Using Git
Using Git is preferred. Navigate to your desired directory, and execute the following:

```console
$ git clone https://github.com/CollinHeist/TitleCardMaker/
```

#### Without Git
Download this repo, unzip it, and extract those contents to whatever location you want the program to live. 

> This method isn't recommended, as there is no easy way to get new versions of the Maker.

### Python
The Maker requires [Python](https://www.python.org/) version of at least 3.8+. All package management is done via [pipenv](https://pypi.org/project/pipenv/), or pip with the `requirements.txt` file. Installing the required packages is accomplished with one of the following:

```console
$ pipenv install
```

```console
$ pip3 install -r requirements.txt
```

### ImageMagick
ImageMagick is required to create all cards. Check their [website](https://imagemagick.org/) for installation details. If your OS does not support a standalone installation, the maker supports the use of a docker container - I personally use [imagemagick-docker](https://hub.docker.com/r/dpokidov/imagemagick/). Just make sure you specify this container within the [preferences file](https://github.com/CollinHeist/TitleCardMaker/wiki/ImageMagick-Attributes).

### Sonarr
Sonarr is not required by the Maker, however if unused you will have to manually enter all episode titles for each show (which is __very__ tedious). I strongly recommend you install this (see [here](https://sonarr.tv/)), even if you're not using it to gather your media itself.

## Usage and Troubleshooting
Assuming you're using the default preference filename, invoking the Maker is as simple as:

```console
$ pipenv run python3 main.py --run
```

For invocation and configuration details, read the [Wiki](https://github.com/CollinHeist/TitleCardMaker/wiki).

If you have trouble getting the Maker working (and have already read the Wiki), or have a problem, [create an issue on GitHub](https://github.com/CollinHeist/TitleCardMaker/issues/new)!

## Examples
Below are some examples of title cards created automatically (when configured correctly) by the TitleCardMaker:

### Mr. Robot S01E02 in the `Standard` card style
<img src="https://preview.redd.it/a6e04h0fwvs71.jpg?width=3200&format=pjpg&auto=webp&s=9015ced06ac3a97b45b8fe1f807ce7b2721c9e44" width="800">

### The Mandalorian S01E03 in the `Star Wars` card style
<img src="https://i.ibb.co/cTwGGyn/The-Mandalorian-2019-S01-E03.jpg" width="800">

### Demon Slayer: Kimetsu no Yaiba S03E10 in the `Anime` card style
<img src="https://i.ibb.co/HDQMFyT/Demon-Slayer-Kimetsu-no-Yaiba-2019-S03-E10.jpg" width="800">

## Contributing
If you'd like to contribute - whether that's a suggested feature, a bug fix, or anything else - please do so on GitHub by creating an issue. Perhaps I'll setup a Discord in the future, but for now the best way for me to manage the project is on GitHub.

I plan on creating another repository for non-standard title card styles in the future.

## Support
This has taken a pretty substantial amount of effort, so if you find this project useful you can support me on [BuyMeACoffee](https://www.buymeacoffee.com/CollinHeist), or become a [GitHub sponsor](https://github.com/sponsors/CollinHeist) - I would really appreciate it!
