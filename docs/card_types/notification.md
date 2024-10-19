---
title: Notification Card Type
description: >
    An overview of the built-in Notification card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Notification Card Type

This card design was created by [CollinHeist](https://github.com/CollinHeist),
and is a relatively simple card which borrows a lot of the design elements of
the [Tinted Glass](./tinted_glass.md) card, but was directly inspired by the UI notifications
from Palworld.

These cards feature two compact rectangular frames which contain the title,
season, and episode text. These frames, as well as the text, can be
re-positioned, colored, and sized with extras.

<figure markdown="span" style="max-width: 70%">
  ![Example Notification Card](./assets/notification.webp)
</figure>

??? note "Labeled Card Elements"

    ![Labeled Notification Card Elements](./assets/notification-labeled.webp)

## Edge Adjustments

The edge element refers to the small colored rectangle on the inner side of the
frames.

### Coloring

The color of the edge can be adjusted with the _Edge Color_ extra. If the color
is set to `transparent`, then the edge will be removed completely.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="75.87"
        data-left-label="white" data-right-label="crimson">
        <img src="../assets/notification.webp"/>
        <img src="../assets/notification-edge-color.webp"/>
    </div>

### Width

The width of the edge can be adjusted with the _Edge Width_ extra. TCM does not
perform any validation to ensure the edge does not overlap the title text.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="75.87"
        data-left-label="5" data-right-label="15">
        <img src="../assets/notification.webp"/>
        <img src="../assets/notification-edge-width.webp"/>
    </div>

## Episode Text Adjustments

For adjustments, the "episode text" refers to the combined season and episode
text.

### Color

The color of the episode text can be adjusted with the _Episode Text Color_
extra. If unspecified, this matches the Font color.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="88.91"
        data-left-label="white" data-right-label="crimson">
        <img src="../assets/notification.webp"/>
        <img src="../assets/notification-etc.webp"/>
    </div>

### Size

The size of the episode text can be adjusted with the _Episode Text Font Size_
extra. The background notification rectangle size will be dynamically resized to
fit the episode text. TCM does not perform any validation to ensure the episode
text does not overlap the title text.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="88.91"
        data-left-label="1.0" data-right-label="1.5">
        <img src="../assets/notification.webp"/>
        <img src="../assets/notification-etfs.webp"/>
    </div>

### Vertical Position

The vertical position of the episod text can be adjusted with the _Episode Text
Vertical Shift_ extra. Positive values will move the text up, negative values
will move the text down. The background rectangle will be moved with the episode
text.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="88.91"
        data-left-label="0" data-right-label="-30">
        <img src="../assets/notification.webp"/>
        <img src="../assets/notification-etvs.webp"/>
    </div>

## Background Color

The background color of the player can be adjusted with the _Notification
Background Color_ extra.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="88.91"
        data-left-label="rgba(0,0,0,0.50)" data-right-label="rgba(5, 122, 246, 0.5)">
        <img src="../assets/notification.webp"/>
        <img src="../assets/notification-background-color.webp"/>
    </div>

## Notification Position

The position of the text can be adjusted by setting _Notification Position_ to
either `left`, or `right`. This affects the position of both boxes (title and
episode text).

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="left" data-right-label="right">
        <img src="../assets/notification-position-left.webp"/>
        <img src="../assets/notification.webp"/>
    </div>

## Separator Character

If both the season and episode text are displayed on the Card, then a separator
character is added between them. This character can be adjusted with the
_Separator Character_ extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="90"
        data-left-label="/" data-right-label="||">
        <img src="../assets/notification.webp"/>
        <img src="../assets/notification-separator.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

!!! example "Example"

    <div class="image-compare example-card"
        data-starting-point="83"
        data-left-label="Mask Image" data-right-label="Resulting Title Card">
        <img src="../assets/notification-mask-raw.webp"/>
        <img src="../assets/notification-mask.webp"/>
    </div>
