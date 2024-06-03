# <img src="https://user-images.githubusercontent.com/17693271/164274472-c8fa7302-9b38-4fae-94ca-2e683e58d722.png" width="24" alt="logo"> TitleCardMaker
[![](https://img.shields.io/github/release/CollinHeist/TitleCardMaker.svg)](https://github.com/CollinHeist/TitleCardMaker/releases)
[![Docker Pulls](https://img.shields.io/docker/pulls/collinheist/titlecardmaker)](https://hub.docker.com/r/collinheist/titlecardmaker)
[![GitHub Develop Commits](https://img.shields.io/github/commits-since/CollinHeist/TitleCardMaker/latest/develop?label=Commits%20in%20Develop)](https://github.com/CollinHeist/TitleCardMaker/tree/develop)
[![Discord](https://img.shields.io/discord/955533113734357125?logo=discord&logoColor=white)](https://discord.gg/bJ3bHtw8wH)
[![Support](https://img.shields.io/badge/-Support_Development-9cf?color=informational)](https://github.com/sponsors/CollinHeist)

An automated title card maker for the Plex, Jellyfin, and Emby media servers. All user documentation is available on the [Wiki](https://github.com/CollinHeist/TitleCardMaker/wiki).

> [!IMPORTANT] 
> Version 2.0 - the Web UI - has officially entered pre-release, and is currently available for project [Sponsors](https://github.com/sponsors/CollinHeist).

<img alt="Web UI" src="https://titlecardmaker.com/assets/series_dark.webp"/>

More details are located at [titlecardmaker.com](https://titlecardmaker.com/) - this README (and the Wiki documentation) are primarily geared towards the non-UI (v1).

## Table of Contents
- [Description](#description)
- [Getting Started](#getting-started)
- [Usage and Troubleshooting](#usage-and-troubleshooting)
- [Examples](#examples)
- [Contributing](#contributing)
- [Support](#support)

## Description
`TitleCardMaker` is a program and [Docker container](https://hub.docker.com/r/collinheist/titlecardmaker) written in Python that automates the creation of customized title cards (which are image previews of an episode of TV) for use in personal media server services like [Plex](https://www.plex.tv/), [Jellyfin](https://jellyfin.org/), or [Emby](https://emby.media/).

TitleCardMaker can be automated such that everything can be done without manual intervention. All your series can be read from your media server or Sonarr; episode data can be pulled from Sonarr, your media server, or [TheMovieDatabase](https://www.themoviedb.org/); images from TheMovieDatabase, or your media server; and TitleCardMaker can even utilize an episode's watch status to create "spoiler free" versions of title cards automatically, as shown below:

<img alt="card unblurring process" src="https://user-images.githubusercontent.com/17693271/185819730-a2c55a3a-63cc-4f0e-8061-891edd8d64d0.gif"/>
  
All configuration/automation of the TitleCardMaker is done via YAML files, and the actual image creation is done using the open-source and free image library called [ImageMagick](https://imagemagick.org/).

## Getting Started
> [!NOTE]
> The [Wiki](https://github.com/CollinHeist/TitleCardMaker/wiki) has very extensive documentation on every feature and customization available in TitleCardMaker. I __highly__ recommend looking here as the first step when troubleshooting or customizing your setup. [The Discord](https://discord.gg/bJ3bHtw8wH) is also a great place to get detailed help.

Read the [Getting Started](https://github.com/CollinHeist/TitleCardMaker/wiki) page on the Wiki for the traditional install, or the [Getting Started on Docker](https://github.com/CollinHeist/TitleCardMaker/wiki/Docker-Tutorial) page to install using Docker.

If you're using Unraid, there is a template available for easy setup - just search `titlecardmaker` on the Unraid Community Apps store.

## Usage and Troubleshooting
Assuming you're using the default preference filename, invoking the Maker is as simple as:

```console
pipenv run python main.py --run
```

For invocation and configuration details, read [here](https://github.com/CollinHeist/TitleCardMaker/wiki/Running-the-TitleCardMaker).

> [!TIP]
> If you have trouble getting the Maker working, or have a problem, [create an issue on GitHub](https://github.com/CollinHeist/TitleCardMaker/issues/new), or [join the Discord](https://discord.gg/bJ3bHtw8wH) for help.

## Examples
Below are examples of almost all the types of title card that can be created automatically by TitleCardMaker:

### Built-in Card Types
<img alt="Anime" src="https://titlecardmaker.com/card_types/assets/anime.webp" width="32%"/> <img alt="Banner" src="https://titlecardmaker.com/card_types/assets/banner.webp" width="32%"> <img alt="Calligraphy" src="https://titlecardmaker.com/card_types/assets/calligraphy.webp" width="32%"> <img alt="Comic Book" src="https://titlecardmaker.com/card_types/assets/comic_book.webp" width="32%"/> <img alt="Cutout" src="https://titlecardmaker.com/card_types/assets/cutout.webp" width="32%"/> <img alt="Divider" src="https://titlecardmaker.com/card_types/assets/divider.webp" width="32%"> <img alt="Fade" src="https://titlecardmaker.com/card_types/assets/fade.webp" width="32%"/> <img alt="Formula1" src="https://titlecardmaker.com/card_types/assets/formula.webp" width="32%"> <img alt="Frame" src="https://titlecardmaker.com/card_types/assets/frame.webp" width="32%"/> <img alt="Graph" src="https://titlecardmaker.com/card_types/assets/graph.webp" width="32%"> <img alt="Inset" src="https://titlecardmaker.com/card_types/assets/inset.webp" width="32%"> <img alt="Landscape" src="https://titlecardmaker.com/card_types/assets/landscape.webp" width="32%"> <img alt="Logo" src="https://titlecardmaker.com/card_types/assets/logo.webp" width="32%"> <img alt="Marvel" src="https://titlecardmaker.com/card_types/assets/marvel.webp" width="32%"> <img alt="Music" src="https://titlecardmaker.com/card_types/assets/music.webp" width="32%"> <img alt="Notification" src="https://titlecardmaker.com/card_types/assets/notification.webp" width="32%"> <img alt="Olivier" src="https://titlecardmaker.com/card_types/assets/olivier.webp" width="32%"/> <img alt="Overline" src="https://titlecardmaker.com/card_types/assets/overline.webp" width="32%"> <img alt="Poster" src="https://titlecardmaker.com/card_types/assets/poster.webp" width="32%"> <img alt="Roman" src="https://titlecardmaker.com/card_types/assets/roman_numeral.webp" width="32%"> <img alt="Standard" src="https://titlecardmaker.com/card_types/assets/standard.webp" width="32%"/> <img alt="Striped" src="https://titlecardmaker.com/card_types/assets/striped.webp" width="32%"> <img alt="Shape" src="https://titlecardmaker.com/card_types/assets/shape.webp" width="32%"> <img alt="Star Wars" src="https://titlecardmaker.com/card_types/assets/star_wars.webp" width="32%"> <img alt="tinted Frame" src="https://titlecardmaker.com/card_types/assets/tinted_frame.webp" width="32%"> <img alt="Tinted Glass" src="https://titlecardmaker.com/card_types/assets/tinted_glass.webp" width="32%"> <img alt="White Border" width="32%" src="https://titlecardmaker.com/card_types/assets/white_border.webp">

> The above cards are, in order, the [anime](https://github.com/CollinHeist/TitleCardMaker/wiki/AnimeTitleCard), [banner](https://github.com/CollinHeist/TitleCardMaker/wiki/BannerTitleCard), [calligraphy](https://github.com/CollinHeist/TitleCardMaker/wiki/CalligraphyTitleCard), [comic book](https://github.com/CollinHeist/TitleCardMaker/wiki/ComicBookTitleCard), [cutout](https://github.com/CollinHeist/TitleCardMaker/wiki/CutoutTitleCard), [divider](https://github.com/CollinHeist/TitleCardMaker/wiki/DividerTitleCard), [fade](https://github.com/CollinHeist/TitleCardMaker/wiki/FadeTitleCard), [formula 1](https://titlecardmaker.com/card_types/formula/), [frame](https://github.com/CollinHeist/TitleCardMaker/wiki/FrameTitleCard), [graph](https://titlecardmaker.com/card_types/graph/), [inset](https://github.com/CollinHeist/TitleCardMaker/wiki/InsetTitleCard), [landscape](https://github.com/CollinHeist/TitleCardMaker/wiki/LandscapeTitleCard), [logo](https://github.com/CollinHeist/TitleCardMaker/wiki/LogoTitleCard), [marvel](https://github.com/CollinHeist/TitleCardMaker/wiki/MarvelTitleCard), [music](https://titlecardmaker.com/card_types/music/), [notification](https://titlecardmaker.com/card_types/notification/), [olivier](https://github.com/CollinHeist/TitleCardMaker/wiki/OlivierTitleCard), [overline](https://github.com/CollinHeist/TitleCardMaker/wiki/OverlineTitleCard),  [poster](https://github.com/CollinHeist/TitleCardMaker/wiki/PosterTitleCard), [roman](https://github.com/CollinHeist/TitleCardMaker/wiki/RomanNumeralTitleCard), [standard](https://github.com/CollinHeist/TitleCardMaker/wiki/StandardTitleCard), [striped](https://titlecardmaker.com/card_types/striped/), [shape](https://github.com/CollinHeist/TitleCardMaker/wiki/ShapeTitleCard), [star wars](https://github.com/CollinHeist/TitleCardMaker/wiki/StarWarsTitleCard), [tinted frame](https://github.com/CollinHeist/TitleCardMaker/wiki/TintedFrameTitleCard), [tinted glass](https://github.com/CollinHeist/TitleCardMaker/wiki/TintedGlassTitleCard), and the [white border](https://github.com/CollinHeist/TitleCardMaker/wiki/WhiteBorderTitleCard) title cards.

<details><summary><h3>User-Created Card Types</h3></summary>

The TitleCardMaker can also use user-created and maintained card types hosted on the [companion GitHub](https://github.com/CollinHeist/TitleCardMaker-CardTypes), an example of each type is shown below:

<img src="https://i.ibb.co/tBPsxpc/Westworld-2016-S04-E01.jpg" height="175"/> <img src="https://github.com/Beedman/TitleCardMaker-CardTypes/blob/master/Beedman/The%20Afterparty%20(2022)%20-%20S01E02%20-%20Brett.jpg?raw=true" height="175"/> <img src="https://i.ibb.co/0tnJJ6P/Stranger-Things-2016-S03-E02.jpg" height="175"/> <img src="https://cdn.discordapp.com/attachments/975108033531219979/977614937457303602/S01E04.jpg" height="175"/> <img src="https://raw.githubusercontent.com/Wdvh/TitleCardMaker-CardTypes/c14f1b3759983a63e66982ba6517e2bc3f651dca/Wdvh/S01E01.jpg" height="175"/> <img src="https://user-images.githubusercontent.com/17693271/169709482-6bb023ab-4986-464e-88d6-0e05ad75d0d3.jpg" height="175"/> <img src="https://user-images.githubusercontent.com/1803189/171089736-f60a6ff2-0914-432a-a45d-145323d39c42.jpg" height="175"/> <img src="https://user-images.githubusercontent.com/17693271/169709359-ffc9e109-b327-44e9-b78a-7276f77fe917.jpg" height="175"/> <img src="https://raw.githubusercontent.com/CollinHeist/TitleCardMaker-CardTypes/110c2ec729dbb20d8ed461e7cc5a07c54540f842/Wdvh/S01E07.jpg" height="175"/>  <img src="https://user-images.githubusercontent.com/7379812/187586521-353ba09f-30a8-424b-bbf3-ee9036c9e638.jpg" height="175"/> <img src="https://github.com/khthe8th/TitleCardMaker-CardTypes/assets/5308389/d089a1b1-7458-4eaf-ad8d-59c7f332a7c1" height="175"/>
 
> The above cards are, in order, `Yozora/BarebonesTitleCard`, `Beedman/GradientLogoTitleCard`, `Yozora/RetroTitleCard`, `Yozora/SlimTitleCard`, `Wdvh/StarWarsTitleOnly`, `Wdvh/WhiteTextAbsolute`, `lyonza/WhiteTextBroadcast`, `Wdvh/WhiteTextStandard`, `Wdvh/WhiteTextTitleOnly`, `azuravian/TitleColorMatch`, and `KHthe8th/TintedFramePlusTitleCard`

</details>

## Other Features
In addition to title card creation and management, the TitleCardMaker can also be used for other image-creation functionality. For example, the [mini maker](https://github.com/CollinHeist/TitleCardMaker/wiki/Using-the-Mini-Maker) - a.k.a. `mini_maker.py` - can be used to "manually" create collection posters, genre cards, movie posters, show summaries, and season posters. An example of each is shown below:

<img alt="Example Collection Poster" src="https://user-images.githubusercontent.com/17693271/180630284-57e6d14a-025b-439f-9a84-696749b92c8d.jpg" height="200"/> <img alt="Example Genre Card" src="https://user-images.githubusercontent.com/17693271/166091004-c8cf6afe-7cdf-4ba2-b16d-8a1c13236df8.jpg" height="200"/> <img alt="Example Movie Poster" src="https://user-images.githubusercontent.com/17693271/188292228-c57b7415-63ee-4907-9886-dd94e7d94a6b.jpg" height="200"/> <img alt="Example Genre Card" src="https://user-images.githubusercontent.com/17693271/188784303-a80f0e1c-e1c3-43b0-8591-fa0eb3aafabc.jpg" height="200"/> <img alt="Example Genre Card" src="https://user-images.githubusercontent.com/17693271/172294392-ecababbe-eeef-4e28-b08c-814b7e02f4c7.png" height="200"/>

This is largely done via the command-line, and is described on the wiki [here](https://github.com/CollinHeist/TitleCardMaker/wiki/Using-the-Mini-Maker).

## Contributing
If you'd like to contribute - whether that's a suggested feature, a bug fix, or anything else - please do so on GitHub by creating an issue, or [join the Discord](https://discord.gg/bJ3bHtw8wH). The best way for me to manage technical aspects of the project is on GitHub.

## Support
This has taken a pretty substantial amount of effort, so if you find this project useful you can support me on [BuyMeACoffee](https://www.buymeacoffee.com/CollinHeist), or become a [GitHub sponsor](https://github.com/sponsors/CollinHeist) - I would really appreciate it!

A _huge_ thank you to my current and past sponsors.

<p align="center">
  <img src="https://raw.githubusercontent.com/CollinHeist/static/main/sponsorkit/sponsors.svg/sponsors.svg"/>
</p>
