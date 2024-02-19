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
and is inspired by a music player - specifically Spotify.

These cards feature fully adjustable music timeline, media control buttons, and
artwork. This card is one of the most complex types, featuring many
customizations via extras.

<figure markdown="span" style="max-width: 70%">
  ![Example Music Card](./assets/music.webp)
</figure>

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

## Adding Controls

Stylized music controls can be added to the Card, if desired, by setting the
_Control Toggle_ extra as `True`.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="False" data-right-label="True">
        <img src="../assets/music.webp"/>
        <img src="../assets/music-control.webp"/>
    </div>

## Recoloring Controls

If the music controls are [enabled](#adding-controls), then each individual
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

## Player Positioning

The player itself can be repositioned at various pre-defined locations on the
Card. This is controlled by two extras - the _Player Position_ and _Player
Inset_ extras.

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
