# <img src="https://user-images.githubusercontent.com/17693271/164274472-c8fa7302-9b38-4fae-94ca-2e683e58d722.png" width="24" alt="logo"> TitleCardMaker
[![](https://img.shields.io/github/release/CollinHeist/TitleCardMaker.svg)](https://github.com/CollinHeist/TitleCardMaker/releases)
[![GitHub Develop Commits](https://img.shields.io/github/commits-since/CollinHeist/TitleCardMaker/latest/develop?label=Commits%20in%20Develop&style=flat)](https://github.com/CollinHeist/TitleCardMaker/tree/develop)
[![Discord](https://img.shields.io/discord/955533113734357125?style=flat&logo=discord&logoColor=white)](https://discord.gg/bJ3bHtw8wH)
[![Support](https://img.shields.io/badge/-Support_Development-9cf?style=flat&color=informational)](https://github.com/sponsors/CollinHeist)

An automated title card maker for Plex.

## Table of Contents
- [Description](#description)
- [Getting Started](#getting-started)
- [Usage and Troubleshooting](#usage-and-troubleshooting)
- [Examples](#examples)
- [Contributing](#contributing)
- [Support](#support)

## Description

`TitleCardMaker` is a Python program intended to be invoked via the command-line to automate the creation of title cards, which are image previews of an episode, for use in personal media services like Plex, Emby, or Jellyfin.

The actual image creation is done using the open-source and free image library called [ImageMagick](https://imagemagick.org/). 

The Maker can be automated such that everything can be pulled without manual intervention (except for a few exceptions). Episode titles can be pulled from an instance of [Sonarr](https://sonarr.tv/), images and logos from [TheMovieDatabase](https://www.themoviedb.org/), and the maker can even automatically refresh Plex after new cards are created.

## Getting Started

Read the [Getting Started](https://github.com/CollinHeist/TitleCardMaker/wiki) page on the Wiki.

## Usage and Troubleshooting
Assuming you're using the default preference filename, invoking the Maker is as simple as:

```console
$ pipenv run python3 main.py --run
```

For invocation and configuration details, read [here](https://github.com/CollinHeist/TitleCardMaker/wiki/Running-the-TitleCardMaker).

> If you have trouble getting the Maker working, or have a problem, [create an issue on GitHub](https://github.com/CollinHeist/TitleCardMaker/issues/new)!

## Examples
Below are some examples of title cards created automatically (when configured correctly) by the TitleCardMaker:

### Mr. Robot S01E02 in the `Standard` card style
<img src="https://preview.redd.it/a6e04h0fwvs71.jpg?width=3200&format=pjpg&auto=webp&s=9015ced06ac3a97b45b8fe1f807ce7b2721c9e44" width="800">

### The Mandalorian S01E03 in the `Star Wars` card style
<img src="https://i.ibb.co/cTwGGyn/The-Mandalorian-2019-S01-E03.jpg" width="800">

### Demon Slayer: Kimetsu no Yaiba S03E10 in the `Anime` card style
<img src="https://i.ibb.co/HDQMFyT/Demon-Slayer-Kimetsu-no-Yaiba-2019-S03-E10.jpg" width="800">

## Contributing
If you'd like to contribute - whether that's a suggested feature, a bug fix, or anything else - please do so on GitHub by creating an issue, or [join the Discord](https://discord.gg/bJ3bHtw8wH). The best way for me to manage technical aspects of the project is on GitHub.

I plan on creating another repository for non-standard title card styles in the future.

## Support
This has taken a pretty substantial amount of effort, so if you find this project useful you can support me on [BuyMeACoffee](https://www.buymeacoffee.com/CollinHeist), or become a [GitHub sponsor](https://github.com/sponsors/CollinHeist) - I would really appreciate it!
