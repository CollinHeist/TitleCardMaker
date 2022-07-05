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

`TitleCardMaker` is a program and [Docker container](https://hub.docker.com/r/collinheist/titlecardmaker) written in Python that automates the creation of customized title cards (which are image previews of an episode of TV) for use in personal media services like [Plex](https://www.plex.tv/), [Emby](https://emby.media/), or [Jellyfin](https://jellyfin.org/).

The Maker can be automated such that everything can be pulled without manual intervention (except for a few exceptions). Episode titles can be pulled from an instance of [Sonarr](https://sonarr.tv/), images and logos from [TheMovieDatabase](https://www.themoviedb.org/) and Plex, and the maker can even utilize an episode's watch status within Plex to create "spoiler free" versions of title cards automatically, as shown below:

<img src="https://user-images.githubusercontent.com/17693271/174520069-d981b33e-df93-4166-a4dc-b898af82eb3f.jpg"/>
  
The actual image creation is done using the open-source and free image library called [ImageMagick](https://imagemagick.org/).

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
Below are some examples of each style of title card that can be created automatically by the TitleCardMaker:

### Built-in Card Types

<img src="https://i.ibb.co/HDQMFyT/Demon-Slayer-Kimetsu-no-Yaiba-2019-S03-E10.jpg" height="175"/> <img src="https://user-images.githubusercontent.com/17693271/172227163-0ee4990a-b0a8-4dbd-91b3-3f57dfe6e732.jpg" height="175"/>  <img src="https://user-images.githubusercontent.com/17693271/173495131-5712c9ff-e0f4-4370-8f95-d99c5192df60.jpg" height="175"> 
<img src="https://user-images.githubusercontent.com/17693271/162633928-9c943ede-b309-4cf0-9798-9a196ed8791e.jpg" height="175">  <img src="https://user-images.githubusercontent.com/17693271/170836059-136fa6eb-40ef-4cd7-9aca-8ad8e0537239.jpg" height="175"/> <img src="https://user-images.githubusercontent.com/17693271/170836149-423f9a95-1269-4738-9f41-8cf296cd2ab7.jpg" height="175"/> 

> The above cards are, in order, the [AnimeTitleCard](https://github.com/CollinHeist/TitleCardMaker/wiki/AnimeTitleCard), [LogoTitleCard](https://github.com/CollinHeist/TitleCardMaker/wiki/LogoTitleCard), [RomanTitleCard](https://github.com/CollinHeist/TitleCardMaker/wiki/RomanTitleCard), [StandardTitleCard](https://github.com/CollinHeist/TitleCardMaker/wiki/StandardTitleCard), [StarWarsTitleCard](https://github.com/CollinHeist/TitleCardMaker/wiki/StarWarsTitleCard), and the [TextlessTitleCard](https://github.com/CollinHeist/TitleCardMaker/wiki/TextlessTitleCard)

<details><summary><h3>User-Created Card Types</h3></summary>
  
The TitleCardMaker can also use user-created and maintained card types hosted on the [companion GitHub](https://github.com/CollinHeist/TitleCardMaker-CardTypes), an example of each type is shown below:

<img src="https://i.ibb.co/tBPsxpc/Westworld-2016-S04-E01.jpg" height="175"/> <img src="https://github.com/Beedman/TitleCardMaker-CardTypes/blob/master/Beedman/The%20Afterparty%20(2022)%20-%20S01E02%20-%20Brett.jpg?raw=true" height="175"/> <img src="https://i.ibb.co/0tnJJ6P/Stranger-Things-2016-S03-E02.jpg" height="175"/>

<img src="https://cdn.discordapp.com/attachments/975108033531219979/977614937457303602/S01E04.jpg" height="175"/> <img src="https://github.com/Wdvh/TitleCardMaker-CardTypes/blob/c14f1b3759983a63e66982ba6517e2bc3f651dca/Wdvh/S01E01.jpg" height="175"/> <img src="https://user-images.githubusercontent.com/17693271/169709482-6bb023ab-4986-464e-88d6-0e05ad75d0d3.jpg" height="175"/>

<img src="https://user-images.githubusercontent.com/1803189/171089736-f60a6ff2-0914-432a-a45d-145323d39c42.jpg" height="175"/> <img src="https://user-images.githubusercontent.com/17693271/169709359-ffc9e109-b327-44e9-b78a-7276f77fe917.jpg" height="175"/> <img src="https://github.com/CollinHeist/TitleCardMaker-CardTypes/blob/110c2ec729dbb20d8ed461e7cc5a07c54540f842/Wdvh/S01E07.jpg" height="175"/>
 
> The above cards are, in order, `Yozora/BarebonesTitleCard`, `Beedman/GradientLogoTitleCard`, `Yozora/RetroTitleCard`, `Yozora/SlimTitleCard`, `Wdvh/StarWarsTitleOnly`, `Wdvh/WhiteTextAbsolute`, `lyonza/WhiteTextBroadcast`, `Wdvh/WhiteTextStandard`, and `Wdvh/WhiteTextTitleOnly`

</details>

## Contributing
If you'd like to contribute - whether that's a suggested feature, a bug fix, or anything else - please do so on GitHub by creating an issue, or [join the Discord](https://discord.gg/bJ3bHtw8wH). The best way for me to manage technical aspects of the project is on GitHub.

## Support
This has taken a pretty substantial amount of effort, so if you find this project useful you can support me on [BuyMeACoffee](https://www.buymeacoffee.com/CollinHeist), or become a [GitHub sponsor](https://github.com/sponsors/CollinHeist) - I would really appreciate it!
