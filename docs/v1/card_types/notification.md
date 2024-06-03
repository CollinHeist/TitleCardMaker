---
title: Notification Card Type (v1)
description: >
    An overview of the built-in Notification card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../../javascripts/imageCompare.js" defer></script>

# Notification Card Type

This card type features two compact rectangular frames, styled to resemble a
notification prompt. These "notifications" can be resized, positioned, and
colored with extras.

This card type is used whenever `card_type` is specified as `notification`.

## Example

<div class="image-compare example-card"
    data-starting-point="80"
    data-left-label="Standard" data-right-label="Blurred">
    <img src="../../../card_types/assets/notification.webp"/>
    <img src="../assets/notification_blurred.webp"/>
</div>

## Valid `extras` { data-toc-label="Valid Extras" }

Below is a table of all valid series extras parsed by this card. These are
described in greater detail below.

| Label                         | Default Value      | Description                                          |
| :---------------------------: | :----------------: | :--------------------------------------------------- |
| `edge_color`                  | _Matches the font_ | Color of the edge of each notification box           |
| `edge_width`                  | `#!yaml 5`         | How wide to make the edge coloring                   |
| `episode_text_color`          | _Matches the font_ | Color of the index text                              |
| `episode_text_font_size`      | `#!yaml 1.0`       | Size adjustment for the index text                   |
| `episode_text_vertical_shift` | `#!yaml 0`         | Additional vertical shift to index text              |
| `glass_color`                 | `rgba(0,0,0,0.50)` | Background color of both text boxes                  |
| `position`                    | `right`            | Where to position the notifications                  |
| `box_adjustments`             | `0 0 0 0`          | Adjustments to the bounds of the notification boxes  |
| `separator`                   | `-`                | Character that separates the season and episode text |

## Customization

### Edge

#### Color (`edge_color`) { data-toc-label="Color" }

The color of each notification's edge can be adjusted with the `edge_color`
extra. This matches the font color by default.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Succession (2018):
        card_type: notification
        extras:
          edge_color: crimson
    ```

    <div class="image-compare example-card"
        data-starting-point="75.87"
        data-left-label="white" data-right-label="crimson">
        <img src="../../../../card_types/assets/notification.webp"/>
        <img src="../../../../card_types/assets/notification-edge-color.webp"/>
    </div>

#### Width (`edge_width`) { data-toc-label="Width" }

The width of each notification's edge can be adjusted with the `edge_width`
extra. This defaults to `#!yaml 5`, and is in pixels.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Succession (2018):
        card_type: notification
        extras:
          edge_width: 15
    ```

    <div class="image-compare example-card"
        data-starting-point="75.87"
        data-left-label="5" data-right-label="15">
        <img src="../../../card_types/assets/notification.webp"/>
        <img src="../../../card_types/assets/notification-edge-width.webp"/>
    </div>

### Episode Text

#### Color (`episode_text_color`) { data-toc-label="Color" }

The color of the episode text can be adjusted with the `episode_text_color`
extra. This matches the font color by default.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Succession (2018):
        card_type: notification
        extras:
          episode_text_color: crimson
    ```

    <div class="image-compare example-card"
        data-starting-point="88.91"
        data-left-label="white" data-right-label="crimson">
        <img src="../../../card_types/assets/notification.webp"/>
        <img src="../../../card_types/assets/notification-etc.webp"/>
    </div>

#### Size (`episode_text_font_size`) { data-toc-label="Size" }

The size of the episode text can be adjusted with the `episode_text_font_size`
extra. This defaults to `#!yaml 1.0`.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Succession (2018):
        card_type: notification
        extras:
          episode_text_font_size: 1.5
    ```

    <div class="image-compare example-card"
        data-starting-point="88.91"
        data-left-label="1.0" data-right-label="1.5">
        <img src="../../../card_types/assets/notification.webp"/>
        <img src="../../../card_types/assets/notification-etfs.webp"/>
    </div>

#### Vertical Shift (`episode_text_vertical_shift`) { data-toc-label="Vertical Shift" }

The vertical positioning of the index text (and the matching notification box)
can be adjusted with the `episode_text_vertical_shift` extra. Positive values
shift the box (and text) up, negative values down.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Succession (2018):
        card_type: notification
        extras:
          episode_text_vertical_shift: -30
    ```

    <div class="image-compare example-card"
        data-starting-point="88.91"
        data-left-label="0" data-right-label="-30">
        <img src="../../../card_types/assets/notification.webp"/>
        <img src="../../../card_types/assets/notification-etvs.webp"/>
    </div>

### Notification

#### Adjustments (`box_adjustments`) { data-toc-label="Adjustments" }

If you'd like to adjust the dimensions of the title text's notification box to
either appear further/closer to your title text (especially when using a custom
font), then the `box_adjustments` extra can be used to individually adjust the
boundaries of each of the box's faces.

This is specified in clockwise order, like so `{top} {right} {bottom} {left}`,
with positive values moving the face _in_, negative _out_. The default is
`0 0 0 0`, meaning no adjustments are made.

??? example "Example"

    The following will move the bounds of the title text box in 20 pixels on
    the top, 10 pixels out on the right, 5 pixels in on the botton, and make no
    adjustment on the left.

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Succession (2018):
        card_type: notification
        extras:
          box_adjustments: -20 10 -5 0
    ```

#### Color (`glass_color`) { data-toc-label="Color" }

The background color of both notification boxes can be adjusted with the
`glass_color` extra. This defaults to `rgba(0,0,0,0.50)` - which corresponds to
black at 50% opacity. A transparent color can be specified.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Succession (2018):
        card_type: notification
        extras:
          glass_color: rgba(5, 122, 246, 0.5)
    ```

    <div class="image-compare example-card"
        data-starting-point="88.91"
        data-left-label="rgba(0,0,0,0.50)" data-right-label="rgba(5, 122, 246, 0.5)">
        <img src="../../../card_types/assets/notification.webp"/>
        <img src="../../../card_types/assets/notification-background-color.webp"/>
    </div>

#### Position (`position`) { data-toc-label="Position" }

The position of both notification boxes can be adjusted with the `position`
extra. This can be either `left` or `right`, and defaults to `right`.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Succession (2018):
        card_type: notification
        extras:
          position: right
    ```

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="left" data-right-label="right">
        <img src="../../../card_types/assets/notification-position-left.webp"/>
        <img src="../../../card_types/assets/notification.webp"/>
    </div>

### Separator Character (`separator`) { data-toc-label="Separator Character" }

If both the season and episode text are displayed on the Card, then a separator
character is added between them. This character can be adjusted with the
`separator` extra.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Succession (2018):
        card_type: notification
        extras:
          separator: "||"
    ```

    <div class="image-compare example-card"
        data-starting-point="90"
        data-left-label="/" data-right-label="||">
        <img src="../../../card_types/assets/notification.webp"/>
        <img src="../../../card_types/assets/notification-separator.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

!!! example "Example"

    <div class="image-compare example-card"
        data-starting-point="83"
        data-left-label="Mask Image"
        data-right-label="Resulting Title Card">
        <img src="../../../../card_types/assets/notification-mask-raw.webp"/>
        <img src="../../../../card_types/assets/notification-mask.webp"/>
    </div>

*[Index Text]: Season and episode text
