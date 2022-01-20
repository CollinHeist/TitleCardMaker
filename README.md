# TitleCardMaker
An automated title card maker for Plex.

## Description

`TitleCardMaker` is a Python program intended to be invoked via the command-line to automate the creation of title cards, which are image previews of an episode, for use in personal media services like Plex, Emby, or Jellyfin.

The actual image generation is done using the open-source and free image library called [ImageMagick](https://imagemagick.org/). 

The code is designed to by OS agnostic, and only requires Python and a few packages that are managed by pipenv. I have tested it on MacOS, and UnraidOS - however it _should_ work on Windows.

The maker can be automated, such that everything can be pulled without manual intervention (except for a few exceptions). Episode titles can be pulled from an instance of [Sonarr](https://sonarr.tv/), images are pulled from [TheMovieDatabase](https://www.themoviedb.org/), and the maker can even automatically refresh Plex after new cards are created. Currently, logos (for the creation of Show Summaries) are _not_ automatically grabbed, and any custom fonts must be gathered manually.

## Installation

Download this repo, unzip it, and extract those contents to whatever location you want the program to live.

Ensure you have a 3.0+ version of [Python](https://www.python.org/) installed on your machine, and what few non-standard modules used can be easily installed via [pipenv](https://pypi.org/project/pipenv/).

Finally, the maker needs `ImageMagick`. You can install it from there website [here](https://imagemagick.org/), or if your OS does not support a standalone installation, the maker supports the use of a docker container - I personally use [imagemagick-docker](https://hub.docker.com/r/dpokidov/imagemagick/#!).

Sonarr is not required by the Maker, however if unused you will have to manually enter all episode titles for each show (which is __very__ tedious). I strongly recommend you install this (see [here](https://sonarr.tv/)), even if you're not using it to gather your media itself.