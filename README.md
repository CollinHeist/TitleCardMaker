# <img src="https://user-images.githubusercontent.com/17693271/164274472-c8fa7302-9b38-4fae-94ca-2e683e58d722.png" width="24" alt="logo"> TitleCardMaker
[![](https://img.shields.io/github/release/CollinHeist/TitleCardMaker.svg?style=flat)](https://github.com/CollinHeist/TitleCardMaker/releases)
![Docker Build](https://img.shields.io/docker/pulls/collinheist/titlecardmaker?style=flat)
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

TitleCardMaker can be automated such that everything can be pulled without manual intervention. All your series can be read from [Sonarr](https://sonarr.tv/) or Plex; episode data can be pulled from Sonarr, Plex or [TheMovieDatabase](https://www.themoviedb.org/); images from TheMovieDatabase or Plex; and TitleCardMaker can even utilize an episode's watch status within Plex to create "spoiler free" versions of title cards automatically, as shown below:

<img alt="card unblurring process" src="https://user-images.githubusercontent.com/17693271/185819730-a2c55a3a-63cc-4f0e-8061-891edd8d64d0.gif"/>
  
All configuration/automation of the TitleCardMaker is done via YAML files, and the actual image creation is done using the open-source and free image library called [ImageMagick](https://imagemagick.org/).

## Getting Started
Read the [Getting Started](https://github.com/CollinHeist/TitleCardMaker/wiki) page on the Wiki for the traditional install, or the [Getting Started on Docker](https://github.com/CollinHeist/TitleCardMaker/wiki/Docker-Tutorial) page to install using Docker.

If you're using Unraid, there is a template available for easy setup - just search `titlecardmaker` on the Unraid Community Apps store.

## Usage and Troubleshooting
Assuming you're using the default preference filename, invoking the Maker is as simple as:

```console
pipenv run python main.py --run
```

For invocation and configuration details, read [here](https://github.com/CollinHeist/TitleCardMaker/wiki/Running-the-TitleCardMaker).

> If you have trouble getting the Maker working, or have a problem, [create an issue on GitHub](https://github.com/CollinHeist/TitleCardMaker/issues/new)!

## Examples
Below are some examples of each style of title card that can be created automatically by the TitleCardMaker:

### Built-in Card Types
<img alt="Anime" src="https://user-images.githubusercontent.com/17693271/185820454-4e3dca1c-c0df-4fa0-a7a7-81e070aa9e69.jpg" height="175"/> <img alt="Cutout" src="https://user-images.githubusercontent.com/17693271/212500535-e88daff6-ecc0-4cc8-8627-82069114c7e0.jpg" height="175"/> <img alt="Frame" src="https://user-images.githubusercontent.com/17693271/202352614-155a176a-fdb0-4476-9f11-6a3a20533a54.jpg" height="175"/> <img alt="Landscape" src="https://user-images.githubusercontent.com/17693271/202352137-b411da21-65ce-4bed-991b-90428c71ec34.jpg" height="175"/> <img alt="Logo" src="https://user-images.githubusercontent.com/17693271/172227163-0ee4990a-b0a8-4dbd-91b3-3f57dfe6e732.jpg" height="175"/> <img alt="Olivier" src="https://user-images.githubusercontent.com/17693271/212500009-067f14ff-4f48-4f75-bacd-7311a9aba716.jpg" height="175"/> <img alt="Poster" src="https://user-images.githubusercontent.com/17693271/180627387-f72bb58e-e001-4608-b4be-82a26263c628.jpg" height="175"/> <img alt="Roman" src="https://user-images.githubusercontent.com/17693271/203910966-4dde1466-6c7e-4422-923b-1f9222ad49e9.jpg" height="175"/> <img alt="Standard" src="https://user-images.githubusercontent.com/17693271/212500240-ae946f2c-a5c8-4881-85f2-83ccb45bf46e.jpg" height="175"/> <img alt="Star Wars" src="https://user-images.githubusercontent.com/17693271/170836059-136fa6eb-40ef-4cd7-9aca-8ad8e0537239.jpg" height="175"/> <img alt="Tinted Glass" src="https://user-images.githubusercontent.com/17693271/213939482-6018b2be-28c5-42dd-988d-d7b9733fe0e8.jpg" height="175"/> 

> The above cards are, in order, the [anime](https://github.com/CollinHeist/TitleCardMaker/wiki/AnimeTitleCard), [cutout](https://github.com/CollinHeist/TitleCardMaker/wiki/CutoutTitleCard), [frame](https://github.com/CollinHeist/TitleCardMaker/wiki/FrameTitleCard), [landscape](https://github.com/CollinHeist/TitleCardMaker/wiki/LandscapeTitleCard), [logo](https://github.com/CollinHeist/TitleCardMaker/wiki/LogoTitleCard), [olivier](https://github.com/CollinHeist/TitleCardMaker/wiki/OlivierTitleCard), [poster](https://github.com/CollinHeist/TitleCardMaker/wiki/PosterTitleCard), [roman](https://github.com/CollinHeist/TitleCardMaker/wiki/RomanNumeralTitleCard), [standard](https://github.com/CollinHeist/TitleCardMaker/wiki/StandardTitleCard), [star wars](https://github.com/CollinHeist/TitleCardMaker/wiki/StarWarsTitleCard), and the [tinted glass](https://github.com/CollinHeist/TitleCardMaker/wiki/TintedGlassTitleCard) title cards - the [textless](https://github.com/CollinHeist/TitleCardMaker/wiki/TitleCard) card is not shown.

<details><summary><h3>User-Created Card Types</h3></summary>

The TitleCardMaker can also use user-created and maintained card types hosted on the [companion GitHub](https://github.com/CollinHeist/TitleCardMaker-CardTypes), an example of each type is shown below:

<img src="https://i.ibb.co/tBPsxpc/Westworld-2016-S04-E01.jpg" height="175"/> <img src="https://github.com/Beedman/TitleCardMaker-CardTypes/blob/master/Beedman/The%20Afterparty%20(2022)%20-%20S01E02%20-%20Brett.jpg?raw=true" height="175"/> <img src="https://i.ibb.co/0tnJJ6P/Stranger-Things-2016-S03-E02.jpg" height="175"/> <img src="https://cdn.discordapp.com/attachments/975108033531219979/977614937457303602/S01E04.jpg" height="175"/> <img src="https://github.com/Wdvh/TitleCardMaker-CardTypes/blob/c14f1b3759983a63e66982ba6517e2bc3f651dca/Wdvh/S01E01.jpg" height="175"/> <img src="https://user-images.githubusercontent.com/17693271/169709482-6bb023ab-4986-464e-88d6-0e05ad75d0d3.jpg" height="175"/> <img src="https://user-images.githubusercontent.com/1803189/171089736-f60a6ff2-0914-432a-a45d-145323d39c42.jpg" height="175"/> <img src="https://user-images.githubusercontent.com/17693271/169709359-ffc9e109-b327-44e9-b78a-7276f77fe917.jpg" height="175"/> <img src="https://github.com/CollinHeist/TitleCardMaker-CardTypes/blob/110c2ec729dbb20d8ed461e7cc5a07c54540f842/Wdvh/S01E07.jpg" height="175"/>  <img src="https://user-images.githubusercontent.com/7379812/187586521-353ba09f-30a8-424b-bbf3-ee9036c9e638.jpg" height="175"/>
 
> The above cards are, in order, `Yozora/BarebonesTitleCard`, `Beedman/GradientLogoTitleCard`, `Yozora/RetroTitleCard`, `Yozora/SlimTitleCard`, `Wdvh/StarWarsTitleOnly`, `Wdvh/WhiteTextAbsolute`, `lyonza/WhiteTextBroadcast`, `Wdvh/WhiteTextStandard`, `Wdvh/WhiteTextTitleOnly`, and `azuravian/TitleColorMatch`

</details>

## Other Features
In addition to title card creation and management, the TitleCardMaker can also be used for other image-creation functionality. For example, the [mini maker](https://github.com/CollinHeist/TitleCardMaker/wiki/Using-the-Mini-Maker) - a.k.a. `mini_maker.py` - can be used to "manually" create collection posters, genre cards, movie posters, show summaries, and season posters. An example of each is shown below:

<img alt="Example Collection Poster" src="https://user-images.githubusercontent.com/17693271/180630284-57e6d14a-025b-439f-9a84-696749b92c8d.jpg" height="200"/> <img alt="Example Genre Card" src="https://user-images.githubusercontent.com/17693271/166091004-c8cf6afe-7cdf-4ba2-b16d-8a1c13236df8.jpg" height="200"/> <img alt="Example Movie Poster" src="https://user-images.githubusercontent.com/17693271/188292228-c57b7415-63ee-4907-9886-dd94e7d94a6b.jpg" height="200"/> <img alt="Example Genre Card" src="https://user-images.githubusercontent.com/17693271/188784303-a80f0e1c-e1c3-43b0-8591-fa0eb3aafabc.jpg" height="200"/> <img alt="Example Genre Card" src="https://user-images.githubusercontent.com/17693271/172294392-ecababbe-eeef-4e28-b08c-814b7e02f4c7.png" height="200"/>

This is largely done via the command-line, and is described on the wiki [here](https://github.com/CollinHeist/TitleCardMaker/wiki/Using-the-Mini-Maker).

## Contributing
If you'd like to contribute - whether that's a suggested feature, a bug fix, or anything else - please do so on GitHub by creating an issue, or [join the Discord](https://discord.gg/bJ3bHtw8wH). The best way for me to manage technical aspects of the project is on GitHub.

## Support
This has taken a pretty substantial amount of effort, so if you find this project useful you can support me on [BuyMeACoffee](https://www.buymeacoffee.com/CollinHeist), or become a [GitHub sponsor](https://github.com/sponsors/CollinHeist) - I would really appreciate it!
