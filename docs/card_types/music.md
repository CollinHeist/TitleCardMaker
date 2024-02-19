---
title: Music Card Type
description: >
    An overview of the built-in Music card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.js"></script>
<script src="../../javascripts/card_types.js" defer></script>

# Music Card Type

!!! warning "Under Construction"

    This documentation is actively being developed.

This card design was created by [CollinHeist](https://github.com/CollinHeist),
and is inspired by a music player (Spotify in particular).

These cards feature a fully adjustable music timeline, media control buttons,
and artwork. This is one of the most complex card types, featuring many
more than twenty available customizations via extras.

<figure markdown="span" style="max-width: 70%">
  ![Example Music Card](./assets/music.webp)
</figure>

??? note "Labeled Card Elements"

    ![Labeled Music Card Elements](./assets/music-labeled.webp)

## Adjusting the Player Style

Above the title text, various kinds of "album art" can be added to the Card by
adjusting the _Player Style_ extra. This can be `basic`, `artwork`, `logo`, or
`poster`.

!!! tip "Automatically Downloading Artwork"

    If the style is set to `artwork`, backdrops __will not__ be automatically
    downloaded. You will need to download these manually for the Series.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="basic" data-right-label="artwork">
        <img src="../assets/music-basic-style.webp"/>
        <img src="../assets/music.webp"/>
    </div>

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="logo" data-right-label="poster">
        <img src="../assets/music-logo-style.webp"/>
        <img src="../assets/music-poster-style.webp"/>
    </div>

## Controls

### Enabling

Stylized music control icons / buttons can be added to the Card, if desired, by
setting the _Control Toggle_ extra as `True`.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="False" data-right-label="True">
        <img src="../assets/music.webp"/>
        <img src="../assets/music-control.webp"/>
    </div>

### Coloring

If the music controls are [enabled](#enabling), then each individual
control icon can be recolored (or omitted completely) with the _Control Colors_
extra.

This must be a set of five space-separated colors, where each color will be
used on the controls in order.

!!! warning "Colors with Spaces"

    All specified colors __cannot__ have spaces. For example, write
    `rgb(1, 1, 1)` as `rgb(1,1,1)`.

If a color is given as `transparent` or `none`, that control icon will be
removed.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="white crimson skyblue SeaGreen1 yellow" data-right-label="white white white white white">
        <img src="../assets/music-control-colors.webp"/>
        <img src="../assets/music-control.webp"/>
    </div>

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="rgb(29,185,84) none white none rgb(29,185,84)" data-right-label="white white white white white">
        <img src="../assets/music-control-hidden.webp"/>
        <img src="../assets/music-control.webp"/>
    </div>

## Heart Icon

A small heart / like icon can also be added to the top right of the player. This
icon can be toggled and recolored with extras.

!!! warning "Icon Overlap"

    TCM does not implement any logic to prevent the heart icon from overlapping
    album artwork or title text.

### Enabling

The heart icon is disabled by default, but can be enabled by setting the _Heart
Toggle_ extra as `True`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="28"
        data-left-label="False" data-right-label="True">
        <img src="../assets/music.webp"/>
        <img src="../assets/music-heart-toggle.webp"/>
    </div>

### Coloring

The heart icon can be recolored in two ways. The edge / stroke of the icon with
the _Heart Stroke Color_ extra, and the inside / fill of the icon with the
_Heart Fill Color_ extra. These are separated so that the heart can be visible
while not appearing "selected."

??? example "Examples"

    The following shows an adjustment to the _Heart Stroke Color_.

    <div class="image-compare example-card"
        data-starting-point="27.7"
        data-left-label="white" data-right-label="rgb(29,185,84)">
        <img src="../assets/music-heart-toggle.webp"/>
        <img src="../assets/music-heart-stroke.webp"/>
    </div>

    The following shows an adjustment to the _Heart Stroke Color_ __and__
    _Heart Fill Color_ extras.

    <div class="image-compare example-card"
        data-starting-point="27.7"
        data-left-label="white" data-right-label="#FF2733">
        <img src="../assets/music-heart-toggle.webp"/>
        <img src="../assets/music-heart-fill.webp"/>
    </div>

## Timeline

### Coloring

The color of the filled portion of the timeline can be adjusted with the
_Timeline Color_ extra. This only applies to the filled portion - e.g. the
[percentage](#filled-percentage) - and the "bubble".

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="10"
        data-left-label="rgb(29,185,84)" data-right-label="skyblue">
        <img src="../assets/music.webp"/>
        <img src="../assets/music-timeline-color.webp"/>
    </div>

### Filled Percentage

The filled logic for the timeline is greatly customizable with the _Timeline
Fill Percentage_ extra.

If this is set to an explicit number - such as `0.3` - then the timeline will
always be that percent filled. The number will be interpreted as a percentage.

If this is specified as `random` (or left as the default) then each Card will
utilize a random fill percentage.

Finally, this can also be given as a [Format String](../user_guide/variables.md)
in which case TCM will calculate the percentage for each Card. For example, by
setting this extra to `{episode_number / season_episode_max}`, the timeline
percentage will be "filled" from 0% to 100% for each season.

!!! tip "Advanced Format Strings"

    To see the list of available variables that can be used in format strings to
    customize the filled percentage, see [here](../user_guide/variables.md).

!!! warning "Warning About Format Strings"

    Be careful when specifying a self-calculating format string for the filled
    percentage for currently airing Series/seasons. If the format specified
    changes every time a new Episode aires, then all Cards affected by this
    change will be remade and reloaded for each new Episode.

## Player Positioning

### Overall Position

The position of the player can be adjusted by setting _Player Position_ to
either `left`, `middle` or `right`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="66"
        data-left-label="middle" data-right-label="right">
        <img src="../assets/music-middle-position.webp"/>
        <img src="../assets/music-right-position.webp"/>
    </div>

### Player Inset

The _Player Inset_ extra allows more fine-tuned control of how far from the 
edge of the image to place the player. This is applied to both the horizontal
and vertical spacing.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="50" data-right-label="150">
        <img src="../assets/music.webp"/>
        <img src="../assets/music-inset-150.webp"/>
    </div>

## Player Width

The width of the player can also be adjusted with the _Player Width_ extra. All
elements within the player - notably the timeline and any album artwork - are
dynamically resized with the new width.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="33"
        data-left-label="900" data-right-label="1200">
        <img src="../assets/music.webp"/>
        <img src="../assets/music-width-1200.webp"/>
    </div>

## Player Color

The background color of the player can be adjusted with the _Player Background
Color_ extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="rgba(0,0,0,0.50)" data-right-label="rgba(120,120,120,0.50)">
        <img src="../assets/music.webp"/>
        <img src="../assets/music-background-alt.webp"/>
    </div>

<script>
  const viewers = document.querySelectorAll(".image-compare");
  const options = {
    hoverStart: false,
    controlShadow: false,
    addCircle: true,
    addCircleBlur: true,
    showLabels: true,
  };
  const labelOptions = {onHover: true};

  viewers.forEach((element) => {
    let view = new ImageCompare(
        element,
        {
            startingPoint: element.dataset?.startingPoint,
            verticalMode: element.dataset?.verticalMode === "true",
            labelOptions: {
                before: element.dataset?.leftLabel,
                after: element.dataset?.rightLabel,
                ...labelOptions,
            },
            ...options,
        }
    ).mount();
  });
</script>
