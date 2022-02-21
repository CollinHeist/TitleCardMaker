# TitleCardMaker
An automated title card maker for Plex.

## Description

`TitleCardMaker` is a Python program intended to be invoked via the command-line to automate the creation of title cards, which are image previews of an episode, for use in personal media services like Plex, Emby, or Jellyfin.

The actual image generation is done using the open-source and free image library called [ImageMagick](https://imagemagick.org/). 

The code is designed to by OS agnostic, and only requires Python and a few packages that are managed by pipenv. I have tested it on MacOS, and UnraidOS - however it _should_ work on Windows.

The maker can be automated, such that everything can be pulled without manual intervention (except for a few exceptions). Episode titles can be pulled from an instance of [Sonarr](https://sonarr.tv/), images are pulled from [TheMovieDatabase](https://www.themoviedb.org/), and the maker can even automatically refresh Plex after new cards are created. Currently, logos (for the creation of Show Summaries) are _not_ automatically grabbed, and any custom fonts must be gathered manually.

## Getting Started

1. Install TitleCardMaker and the required software - see [here]() for details.
2. Create the top-level configuration file necessary to outline how the maker should interact with your services - see [here](https://github.com/CollinHeist/TitleCardMaker/wiki#configuring-the-titlecardmaker) for detailed instructions, or [here](https://github.com/CollinHeist/TitleCardMaker/wiki#complete-example) for an example file you can copy and fill out yourself.
3. Create the series YAML file(s) that list for which series you would like to create title cards for, as well as what those cards should look like - see [here]() for detailed instructions.
4. If you're inspired to create your own types of cards (not just your own cards), see [here](https://github.com/CollinHeist/TitleCardMaker/wiki/Custom-Card-Types#creating-a-custom-card-type) for details on getting started.

## Installation

Download this repo, unzip it, and extract those contents to whatever location you want the program to live.

Ensure you have a 3.0+ version of [Python](https://www.python.org/) installed on your machine, and what few non-standard modules used can be easily installed via [pipenv](https://pypi.org/project/pipenv/).

Finally, the maker needs `ImageMagick`. You can install it from there website [here](https://imagemagick.org/), or if your OS does not support a standalone installation, the maker supports the use of a docker container - I personally use [imagemagick-docker](https://hub.docker.com/r/dpokidov/imagemagick/#!).

Sonarr is not required by the Maker, however if unused you will have to manually enter all episode titles for each show (which is __very__ tedious). I strongly recommend you install this (see [here](https://sonarr.tv/)), even if you're not using it to gather your media itself.

## Usage and Troubleshooting
For usage and configuration details, read the wiki [here](https://github.com/CollinHeist/TitleCardMaker/wiki).

If you have trouble getting the Maker working (and have already read the Wiki), or have a problem, [create an issue on GitHub](https://github.com/CollinHeist/TitleCardMaker/issues/new)!

## Contributing
If you'd like to contribute - whether that's a suggested feature, a bug fix, or anything else - please do so on GitHub by creating an issue. Perhaps I'll setup a Discord in the future, but for now the best way for me to manage the project is on GitHub.

I plan on creating another repository for non-standard title card styles in the future.

## Support
If you find this project useful, you can 
