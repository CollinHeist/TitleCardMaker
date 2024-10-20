---
title: Negative Space Card Type
description: >
    An overview of the built-in Negative Space card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Negative Space Card Type

This card design was created by [CollinHeist](https://github.com/CollinHeist),
and is based the video transitions in
[this video](https://www.youtube.com/watch?v=anSjZS63T7s) by _Not David_.

<figure markdown="span" style="max-width: 70%">
  ![Example Negative Space Card](./assets/negative_space.webp)
</figure>

??? note "Labeled Card Elements"

    ![Labeled Negative Space Card Elements](./assets/negative_space-labeled.webp)

## Text Positioning

The overall position of both the episode/numeral and title text can be set to
the left or right side of the image. This is controlled with the _Text Side_
extra. This can be set to `left`, `right`, or `random`. If set to `random`, then
TCM will randomly select a side when the Card is generated.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="left" data-right-label="right">
        <img src="../assets/negative_space.webp"/>
        <img src="../assets/negative_space-side.webp"/>
    </div>

## Episode Text Adjustments

In the Negative Space card, the episode text is the large numeral which is
positioned on the side of the image.

### Color

The color of the episode text can be adjusted with the _Episode Text Color_
extra. If unspecified, it defaults to matching the font color.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="11.9"
        data-left-label="white" data-right-label="MediumGoldenRod">
        <img src="../assets/negative_space.webp"/>
        <img src="../assets/negative_space-etc.webp"/>
    </div>

### Size

The size of the episode text can be adjusted with the _Episode Text Font Size_
extra. Values above `1.0` increase the size of the text, and values below `1.0`
decrease it.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="11.9"
        data-left-label="1.0" data-right-label="0.8">
        <img src="../assets/negative_space.webp"/>
        <img src="../assets/negative_space-etfs.webp"/>
    </div>

### Position

#### Horizontal Shift

The horizontal position of the episode/numeral text can be adjusted with the
_Episode Text Horizontal Shift_ extra. Positive values shift the episode text
towards the opposite side of the card, and negative ones shift it out.

TCM uses a different base horizontal offset for the number based on the first
number of the episode text. For example - the number `14` (starting with `1`)
will be positioned slightly differently than `61` (starting with `6`).

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="11.9"
        data-left-label="0" data-right-label="200">
        <img src="../assets/negative_space.webp"/>
        <img src="../assets/negative_space-eths.webp"/>
    </div>

#### Vertical Shift

The vertical position of the episode/numeral text can be adjusted with the
_Episode Text Vertical Shift_ extra. Positive values shift the episode text
down, and negative values shift it up.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="11.9"
        data-left-label="0" data-right-label="300">
        <img src="../assets/negative_space.webp"/>
        <img src="../assets/negative_space-etvs.webp"/>
    </div>

## Title Text Horizontal Shift

The horizontal position of the title text can be adjusted with the
_Title Text Horizontal Shift_ extra. The

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="11.9"
        data-left-label="0" data-right-label="250">
        <img src="../assets/negative_space.webp"/>
        <img src="../assets/negative_space-tths.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

!!! example "Example"

    <div class="image-compare example-card"
        data-starting-point="14.25"
        data-left-label="Mask Image" data-right-label="Resulting Title Card">
        <img src="../assets/negative_space-mask-raw.webp"/>
        <img src="../assets/negative_space-mask.webp"/>
    </div>
