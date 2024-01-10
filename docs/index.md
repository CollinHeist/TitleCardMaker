---
title: Welcome to TitleCardMaker
description: >
    Automate the creation and customization of Title Cards for Plex, Jellyfin,
    and Emby.
hide:
    - navigation
---
<script src="../../javascripts/home.js" defer></script>
# Welcome to TitleCardMaker

!!! warning "Under Construction"

    This documentation is actively being developed.

TitleCardMaker (TCM) is a program and Docker container written in Python that
automates the creation of customized Title Cards for use in personal media
server services like Plex, Jellyfin, or Emby.

<div class="scroller">
  <div class="scroller__inner">
    <img class="no-lightbox" src="./assets/home_poster_light.webp#only-light">
    <img class="no-lightbox" src="./assets/home_poster_dark.webp#only-dark">
    <a href="./user_guide/series"><img class="no-lightbox" src="./assets/series_light.webp#only-light"></a>
    <a href="./user_guide/series"><img class="no-lightbox" src="./assets/series_dark.webp#only-dark"></a>
    <a href="./user_guide/new_series"><img class="no-lightbox" src="./assets/add_series_light.webp#only-light"></a>
    <a href="./user_guide/new_series"><img class="no-lightbox" src="./assets/add_series_dark.webp#only-dark"></a>
    <a href="./blueprints"><img class="no-lightbox" src="./assets/blueprint_all_light.webp#only-light"></a>
    <a href="./blueprints"><img class="no-lightbox" src="./assets/blueprint_all_dark.webp#only-dark"></a>
    <a href="./user_guide/fonts"><img class="no-lightbox" src="./assets/fonts_light.webp#only-light"></a>
    <a href="./user_guide/fonts"><img class="no-lightbox" src="./assets/fonts_dark.webp#only-dark"></a>
    <img class="no-lightbox" src="./assets/home_table_light.webp#only-light">
    <img class="no-lightbox" src="./assets/home_table_dark.webp#only-dark">
  </div>
</div>

# What is a Title Card?

A Title Card is a thumbnail image for an Episode of television that can be used
to add a unique look within a personal media server like Plex, Emby, or
Jellyfin. Some Series have "official" Title Cards featured in the Episode
itself, but TCM specializes in creating and customizing "unofficial" Title
Cards. The following Cards have all been designed by me, and were created with
TitleCardMaker:

![Tinted Frame](./assets/card_example0.jpg){id="preview0" width="48%"} ![Anime](./assets/card_example1.jpg){id="preview1" width="48%"}

# Download TitleCardMaker

While the TCM Web UI is under active development, it is only accessible to
project Sponsors. If you are interested, sponsor on
[GitHub](https://github.com/sponsors/CollinHeist) for access.

Installation and startup instructions are [here](./getting_started/index.md).

# Getting Started

!!! info "Detailed Tutorial"

    For more detailed tutorials that take you step-by-step through the
    installation and setup of TitleCardMaker, continue to the
    [Getting Started](./getting_started/index.md) tutorial.

TitleCardMaker is designed to for an easy "out of the box" setup. The basic
steps are as follows:

1. Install TitleCardMaker (via Docker or locally).

2. Set up your Connections to your other services - such as Sonarr, TMDb, Plex,
Emby, Jellyfin, or Tautulli.

3. Start adding Series to TitleCardMaker - this can be done manually, or with
[Syncs](./getting_started/first_sync/index.md).

4. Customize the look and style of Title Cards to your liking.

*[PAT]: Personal Access Token
