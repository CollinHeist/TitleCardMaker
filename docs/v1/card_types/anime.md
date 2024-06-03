---
title: Anime Card Type (v1)
description: >
    An overview of the built-in Anime card type.
---

# Anime Card Type

This style of title card is based off Reddit user
[/u/Recker_Man](https://www.reddit.com/user/Recker_Man)'s style. Although it is
referred to as the "anime" card style, there is nothing preventing you from
using it for any series. The only thing about this card that indicates its
anime design is the ability to add kanji text above the episode title.

This card type is used whenever `card_type` is specified as `anime`.

## Examples

<div class="image-compare example-card"
    data-starting-point="80"
    data-left-label="Standard" data-right-label="Blurred">
    <img src="../../card_types/assets/anime.webp"/>
    <img src="./assets/anime_blurred.webp"/>
</div>

## Valid `extras` { data-toc-label="Valid Extras" }

Below is a table of all valid series extras parsed by this card. These are
described in greater detail below.

| Label                  | Default Value    | Description                         |
| :--------------------: | :--------------: | :-------------------------------------- |
| `kanji`                | -                | Optional kanji (Japanese) text to place above the title - should be a [translation](https://github.com/CollinHeist/TitleCardMaker/wiki/TMDb-Attributes#title-translation) |
| `require_kanji`        | `#!yaml false`   | Whether to require `kanji` to be provided before a card is created |
| `kanji_color`          | `white`          | Color of the kanji text                 |
| `kanji_font_size`      | `#!yaml 1.0`     | Scalar for the size of the kanji text   |
| `kanji_stroke_color`   | `black`          | Color of the stroke for the kanji text  |
| `kanji_stroke_width`   | `#!yaml 1.0`     | Stroke width of the kanji text          |
| `kanji_vertical_shift` | `#!yaml 0`       | Additional vertical offset to apply to the kanji text |
| `stroke_color`         | `black`          | Custom color to use for the stroke on the title and kanji text |
| `episode_text_color`   | `#CFCFCF`        | Color to utilize for the episode text   |
| `episode_stroke_color` | `black`          | Color of the stroke for the episode text |
| `omit_gradient`        | `#!yaml false`   | Whether to omit the gradient overlay from the card |
| `separator`            | `·`              | Character to separate season and episode text |

## Customization

### Adding Kanji

This card type looks for data under the `kanji` key within a series' datafile.
If present, the text is added above the episode title. This text can be
automatically added by the Maker (with some configuration).

If TMDb is enabled, then these can be queried from TMDb automatically by
utilizing the [title translation](https://github.com/CollinHeist/TitleCardMaker/wiki/TMDb-Attributes#title-translation)
feature of the Maker. The ISO code for Japanese is `ja`, and these titles should
be stored under the `kanji` key, so the YAML must would look something like
this:

```yaml title="tv.yml" hl_lines="4-6"
series:
  "Demon Slayer: Kimetsu no Yaiba (2019)":
    card_type: anime
    translation:
      language: ja
      key: kanji
```

??? question "How do you add kanji manually?"

    If TMDb is not
    [globally](https://github.com/CollinHeist/TitleCardMaker/wiki/TMDb-Attributes)
    enabled, then this data must be entered manually. Within a given datafile,
    add the kanji text like so (for the given example):

    ```yaml title="data.yml" hl_lines="4"
    data:
      Season 3:
        10:
          kanji: 絶対諦めない
          title: Never Give Up
    ```

## Recommended Template

To save repeating this translation syntax for every anime you want Kanji added
to, it's recommended to use a template. An _example_ of which is shown below - 
but feel free to modify for your needs.

```yaml title="tv.yml"
templates:
  anime_with_kanji:
    card_type: anime
    library: Anime # Change to your library name, or delete completely
    translation:
      language: ja
      key: kanji
```

This can then be used like so:

```yaml title="tv.yml" hl_lines="2 11"
templates:
  anime_with_kanji:
    card_type: anime
    library: Anime # Change to your library name, or delete completely
    translation:
      language: ja
      key: kanji

series:
  "Demon Slayer: Kimetsu no Yaiba (2019)":
    template: anime_with_kanji
```

TCM will then automatically look for kanji translations for all series which use
this template.

## Customization

### Kanji 

#### Color (`kanji_color`) { data-toc-label="Color" }

The color of the kanji text can be adjusted with the `kanji_color` extra. This
defaults to `white` (to match the default font color of the title text).

??? example "Example"

    ```yaml title="tv.yml" hl_lines="8"
    series:
      Pokémon (1997):
        card_type: anime
        font:
          case: source
          color: rgb(247,205,70)
        extras:
          kanji_color: rgb(247,205,70)
    ```

#### Requiring Kanji (`require_kanji`) { data-toc-label="Valid Extras" }

By default, if a kanji translation cannot be found or is not present for a given
card, the title card will still be created. This might not be desired behavior,
so the `require_kanji` extra can be specified to skip a card if there is no
Kanji present. This defaults to `false`.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="8"
    series:
      "Demon Slayer: Kimetsu no Yaiba (2019)":
        card_type: anime
        translation:
          language: ja
          key: kanji
        extras:
          require_kanji: true
    ```

If this is present for a given series, then an error will be printed and the
card will be skipped until Kanji has been identified from TMDb, or entered
manually into the datafile.

#### Size (`kanji_font_size`) { data-toc-label="Size" }

The size of the kanji text can be adjusted with the `kanji_font_size` extra.
This defaults to `1.0` (meaning no adjustment). Values above `1.0` will increase
the size, values below `1.0` will decrease it.

??? example "Example"

    The following would reduce the size of the kanji text by 20% (to 80%).

    ```yaml title="tv.yml" hl_lines="8"
    series:
      "Demon Slayer: Kimetsu no Yaiba (2019)":
        card_type: anime
        translation:
          language: ja
          key: kanji
        extras:
          kanji_font_size: 0.8
    ```

#### Stroke Color (`kanji_stroke_color`) { data-toc-label="Stroke Color" }

The stroke of the color for the kanji text can be adjusted with the
`kanji_stroke_color` extra. This defaults to `black`.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="8"
    series:
      "Demon Slayer: Kimetsu no Yaiba (2019)":
        card_type: anime
        translation:
          language: ja
          key: kanji
        extras:
          kanji_stroke_color: red
    ```

#### Vertical Shift (`kanji_vertical_shift`) { data-toc-label="Vertical Shift" }

If kanji text is added, the Kanji text might appear either too high or low
(especially if using a custom font). To fix this, this can be adjusted via the
`kanji_vertical_shift` extra. Positive values move the kanji up, and negative
ones move it down.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="8"
    series:
      "Demon Slayer: Kimetsu no Yaiba (2019)":
        card_type: anime
        translation:
          language: ja
          key: kanji
        extras:
          kanji_vertical_shift: -10 # This would shift the kanji DOWN 10 pixels
    ```

### Episode Text

#### Color (`episode_text_color`) { data-toc-label="Color" }

The color of the episode text can be adjusted with the `episode_text_color`
extra. This defaults to `#CFCFCF`.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      "Mushoku Tensei: Jobless Reincarnation (2021)":
        card_type: anime
        extras:
          episode_text_color: rgb(203, 132, 11)
    ```

#### Stroke Color (`episode_stroke_color`) { data-toc-label="Stroke Color" }

The color of the stroke outline on the episode text can be changed with the
`episode_stroke_color` extra. This defaults to `black`.

### Gradient Overlay (`omit_gradient`) { data-toc-label="Gradient Overlay" }

By default, this card type applys a gradient on top of the source image so that
the text is more legible on the card. This can be disabled by setting the
`omit_gradient` extra to `false`.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      "Mushoku Tensei: Jobless Reincarnation (2021)":
        card_type: anime
        extras:
          omit_gradient: false
    ```

### Separator Character (`separator`) { data-toc-label="Separator Character" }

The character between the season and episode text (a.k.a. the separator) can
be customized with the `separator` extra. By default, a `·` character is used.

??? example "Example"

    ```yaml title="tv.yml" hl_lines="5"
    series:
      "Mushoku Tensei: Jobless Reincarnation (2021)":
        card_type: anime
        extras:
          separator: "/"
    ```

### Stroke Color (`stroke_color`) { data-toc-label="Stroke Color" }

The color of the stroke used for the title text can be adjusted with the
`stroke_color` extra. This defaults to `black` (like all other stroke colors).

??? example "Example"

    ```yaml title="tv.yml" hl_lines="12"
    series:
      Pokémon (1997):
        card_type: anime
        font:
          case: source
          color: rgb(247,205,70)
          file: ./fonts/Pokemon Solid.ttf
          kerning: 50%
          size: 110%
          stroke_width: 500%
        extras:
          stroke_color: rgb(64,107,175)
    ```

    This will produce the following cards:

    ![](../../assets/blueprint_series_light.jpg#only-light){.no-lightbox}
    ![](../../assets/blueprint_series_dark.jpg#only-dark){.no-lightbox}
