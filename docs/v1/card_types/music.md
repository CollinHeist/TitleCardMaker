---
title: Music Card Type (v1)
description: >
    An overview of the built-in Music card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../../javascripts/imageCompare.js" defer></script>

# Music Card Type

These cards feature a fully adjustable music timeline, media control buttons,
and artwork. This is one of the more complex card types, featuring more than 
twenty available extra customizations.

This card type is used whenever `card_type` is specified as `music` or
`spotify`.

## Example

<div class="image-compare example-card"
    data-starting-point="80"
    data-left-label="Standard" data-right-label="Blurred">
    <img src="../../../card_types/assets/music.webp"/>
    <img src="../assets/music_blurred.webp"/>
</div>

??? note "Labeled Card Elements"

    ![Labeled Music Card Elements](./assets/music-labeled.webp)

## Valid `extras` { data-toc-label="Valid Extras" }

| Label                | Default Value                   | Description                                              |
| :------------------: | :-----------------------------: | :------------------------------------------------------- |
| `add_controls`       | `#!yaml false`                  | Whether to display the media controls                    |
| `album_cover`        | -                               | File to use for the album image                          |
| `album_size`         | `#!yaml 1.0`                    | Scalar for how much to scale the size of the album image |
| `control_colors`     | `white white white white white` | Color of the media control elements                      |
| `draw_heart`         | `#!yaml false`                  | Whether to draw the heart                                |
| `episode_text_color` | _Matches the font_              | Color to utilize for the episode text                    |
| `heart_color`        | `transparent`                   | Color to fill the heart with                             |
| `heart_stroke_color` | `white`                         | Color to use for the outline of the heart                |
| `pause_or_play`      | `play`                          | Which icon to display in the media controls              |
| `percentage`         | `random`                        | Filled percentage of the timeline                        |
| `player_color`       | `rgba(0,0,0,0.50)`              | Background of the player                                 |
| `player_inset`       | `#!yaml 75`                     | How far to inset the player from the edges               |
| `player_position`    | `left`                          | Where to position the player on the image                |
| `player_style`       | `logo`                          | Which style of the player to display                     |
| `player_width`       | `#!yaml 900`                    | Width of the player                                      |
| `round_corners`      | `#!yaml true`                   | Whether to round the corners of the album image          |
| `subtitle`           | -                               | Text to display below the title                          |
| `timeline_color`     | `rgb(29,185,84)`                | Color of the filled timeline                             |

## Customization

### Album Cover (`album_cover`) { data-toc-label="Album Cover" }

If the card's [Player Style](#player-style-player_style) is anything other than
`basic`, then the image to display above title text should be specified with the
`album_cover` extra.

This can be a file name - e.g. `logo.png` - in which case TCM will automatically
search alongside the specified source image for a file of that name.

!!! example "Example"

    ```yaml title="tv.yml" hl_lines="5-6"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          album_cover: logo.png
          player_style: logo
    ```

This can also be a fully specified file path.

!!! example "Example"

    ```yaml title="tv.yml" hl_lines="5-6"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          album_cover: ./backdrop.jpg
          player_style: artwork
    ```

### Player Style (`player_style`) { data-toc-label="Player Style" }

Above the title text, various kinds of "album art" can be added to the Card by
adjusting the `player_style` extra. This can be `basic`, `artwork`, `logo`, or
`poster`. The default value is `logo`.

!!! tip "Automatically Downloading Artwork"

    If the style is set to `artwork`, backdrops __will not__ be automatically
    downloaded. You will need to download these manually for the Series.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          player_style: artwork
    ```

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="basic" data-right-label="artwork">
        <img src="../../../../card_types/assets/music-basic-style.webp"/>
        <img src="../../../../card_types/assets/music.webp"/>
    </div>

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="logo" data-right-label="poster">
        <img src="../../../../card_types/assets/music-logo-style.webp"/>
        <img src="../../../../card_types/assets/music-poster-style.webp"/>
    </div>

### Controls

#### Enabling (`add_controls`) { data-toc-label="Enabling" }

Stylized music control icons / buttons can be added to the Card, if desired, by
setting the `#!yaml add_controls: true` extra.

??? example "Examples"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          add_controls: true
    ```

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="false" data-right-label="true">
        <img src="../../../../card_types/assets/music.webp"/>
        <img src="../../../../card_types/assets/music-control.webp"/>
    </div>

#### Coloring (`control_colors`) { data-toc-label="Coloring" }

If the music controls are [enabled](#enabling-add_controls), then each
individual control icon can be recolored (or omitted completely) with the
`control_colors` extra.

This must be a set of five space-separated colors, where each color will be
used on the controls in order. The default value is
`white white white white white`.

!!! warning "Colors with Spaces"

    No specified colors can have spaces. For example, write `rgb(1, 1, 1)` as
    `rgb(1,1,1)`.

If a color is given as `transparent` or `none`, that control icon will be
removed.

??? example "Examples"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          control_colors: rgb(29,185,84) none white none rgb(29,185,84)
    ```

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="white crimson skyblue SeaGreen1 yellow" data-right-label="white white white white white">
        <img src="../../../../card_types/assets/music-control-colors.webp"/>
        <img src="../../../../card_types/assets/music-control.webp"/>
    </div>

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="rgb(29,185,84) none white none rgb(29,185,84)" data-right-label="white white white white white">
        <img src="../../../../card_types/assets/music-control-hidden.webp"/>
        <img src="../../../../card_types/assets/music-control.webp"/>
    </div>


#### Pause or Play Icon (`pause_or_play`) { data-toc-label="Pause or Play Icon" }

The middle icon on the controls can be toggled between a pause and play icon
with the `pause_or_play` extra. This can be `pause`, `play`, or `watched`.

If set to `watched`, then the icon will match the watched status of the Episode.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          pause_or_play: play
    ```

    <div class="image-compare example-card"
        data-starting-point="15.5"
        data-left-label="pause" data-right-label="play">
        <img src="../../../../card_types/assets/music-control-pause.webp"/>
        <img src="../../../../card_types/assets/music-control.webp"/>
    </div>

### Heart Icon

A small heart / like icon can also be added to the top right of the player. This
icon can be toggled and recolored with extras.

!!! warning "Icon Overlap"

    TCM does not implement any logic to prevent the heart icon from overlapping
    album artwork or title text.

#### Enabling (`draw_heart`) { data-toc-label="Enabling" }

The heart icon is disabled by default, but can be enabled by setting
`#!yaml draw_heart: true`.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          draw_heart: true
    ```

    <div class="image-compare example-card"
        data-starting-point="28"
        data-left-label="false" data-right-label="true">
        <img src="../../../../card_types/assets/music.webp"/>
        <img src="../../../../card_types/assets/music-heart-toggle.webp"/>
    </div>

#### Coloring (`heart_color` and `heart_stroke_color`) { data-toc-label="Coloring" }

The heart icon can be recolored in two ways. The edge / stroke of the icon with
the `heart_stroke_color` extra, and the inside / fill of the icon with the
`heart_fill_color` extra. These are separated so that the heart can be visible
while not appearing "selected."

??? example "Examples"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          heart_stroke_color: rgb(29,185,84)
    ```

    <div class="image-compare example-card"
        data-starting-point="27.7"
        data-left-label="white" data-right-label="rgb(29,185,84)">
        <img src="../../../../card_types/assets/music-heart-toggle.webp"/>
        <img src="../../../../card_types/assets/music-heart-stroke.webp"/>
    </div>

    ```yaml title="tv.yml" hl_lines="5-6"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          heart_color: "#FF2733"
          heart_stroke_color: "#FF2733"
    ```

    <div class="image-compare example-card"
        data-starting-point="27.7"
        data-left-label="white" data-right-label="#FF2733">
        <img src="../../../../card_types/assets/music-heart-toggle.webp"/>
        <img src="../../../../card_types/assets/music-heart-fill.webp"/>
    </div>

### Timeline

#### Coloring (`timeline_color`) { data-toc-label="Coloring" }

The color of the filled portion of the timeline can be adjusted with the
`timeline_color` extra. This only applies to the filled portion - e.g. the
[percentage](#filled-percentage) - and the "bubble".

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          timeline_color: skyblue
    ```

    <div class="image-compare example-card"
        data-starting-point="10"
        data-left-label="rgb(29,185,84)" data-right-label="skyblue">
        <img src="../../../../card_types/assets/music.webp"/>
        <img src="../../../../card_types/assets/music-timeline-color.webp"/>
    </div>

#### Filled Percentage (`percentage`) { data-toc-label="Filled Percentage" }

The filled logic for the timeline is customizable with the `percentage` extra.

If this is set to an explicit number - such as `#!yaml 0.3` - then the timeline
will always be that percent filled. The number will be interpreted as a
percentage between `0.0` and `1.0`.

If this is specified as `random` (or left as the default) then each Card will
utilize a random fill percentage.

### Player Position

#### Overall Position (`player_position`) { data-toc-label="Overall Position" }

The position of the player can be adjusted by setting `player_position` to
either `left`, `middle` or `right`. The default value is `left`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="66"
        data-left-label="middle" data-right-label="right">
        <img src="../../../../card_types/assets/music-middle-position.webp"/>
        <img src="../../../../card_types/assets/music-right-position.webp"/>
    </div>

#### Inset (`player_inset`) { data-toc-label="Inset" }

The `player_inset` extra allows more fine-tuned control of how far from the edge
of the image to place the player. This is applied to both the horizontal and
vertical spacing. The defalut value is `#!yaml 75`, but can be any value between
`0` and `1200`.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          player_inset: 150
    ```

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="50" data-right-label="150">
        <img src="../../../../card_types/assets/music.webp"/>
        <img src="../../../../card_types/assets/music-inset-150.webp"/>
    </div>

### Player Width (`player_width`) { data-toc-label="Player Width" }

The width of the player can also be adjusted with the `player_width` extra. All
elements within the player - notably the timeline and any album artwork - are
dynamically resized with the specified width. The default value is `#!yaml 900`,
but can be any value between `400` and `3000`.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          player_with: 1200
    ```

    <div class="image-compare example-card"
        data-starting-point="33"
        data-left-label="900" data-right-label="1200">
        <img src="../../../../card_types/assets/music.webp"/>
        <img src="../../../../card_types/assets/music-width-1200.webp"/>
    </div>

### Player Color (`player_color`) { data-toc-label="Player Color" }

The background color of the player can be adjusted with the `player_color`
extra. The default value is `rgba(0,0,0,0.50)`.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          player_color: rgba(120,120,120,0.5)
    ```

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="rgba(0,0,0,0.50)" data-right-label="rgba(120,120,120,0.50)">
        <img src="../../../../card_types/assets/music.webp"/>
        <img src="../../../../card_types/assets/music-background-alt.webp"/>
    </div>

### Subtitle Text (`subtitle`) { data-toc-label="Subtitle Text" }

The text below the title is referred to as the subtitle. This text can be
edited via the `subtitle` extra.

If omitted, then the subtitle will not be displayed at all, or it can be
included in a template to dynamically add to each series.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          subtitle: Atlanta (2016)
    ```

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="<<title>>" data-right-label="<<title>> (<<year>>)">
        <img src="../../../../card_types/assets/music-control.webp"/>
        <img src="../../../../card_types/assets/music-subtitle.webp"/>
    </div>

### Album Image Corner Rounding (`round_corners`) {data-toc-label="Album Image Corner Rounding" }

To add to the "album art" aesthetic, the corners of images are rounded when the
[Player Style](#player-style-player_style) is set to `artwork` or `poster`.

This can be disabled by setting `#!yaml round_corners: false`.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      Atlanta (2016):
        card_type: music
        extras:
          round_corners: false
    ```

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="true" data-right-label="false">
        <img src="../../../../card_types/assets/music-control.webp"/>
        <img src="../../../../card_types/assets/music-rounded.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

!!! example "Example"

    <div class="image-compare example-card"
        data-starting-point="30"
        data-left-label="Mask Image"
        data-right-label="Resulting Title Card">
        <img src="../../../../card_types/assets/music-mask-raw.webp"/>
        <img src="../../../../card_types/assets/music-mask.webp"/>
    </div>
