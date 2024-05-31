---
title: Graph Card Type (v1)
description: >
    An overview of the built-in Graph card type.
---

# Graph Card Type

This card type features a bar graph progress bar which can be used to indicate
the total series progress. This "progress" is parsed from the episode text,
which should be entered as a fraction - for example:

```yaml
episode_text_format: "{season_number} / {season_episode_max}"
```

Will update the "progress" of the graph from 0% to 100% for all episodes in a
season (e.g. the first episode is near 0%, the last episode 100%). This is the
default behavior.

This card type is used whenever `card_type` is specified as `graph`.

## Example

<div class="image-compare example-card"
    data-starting-point="80"
    data-left-label="Standard" data-right-label="Blurred">
    <img src="../../../card_types/assets/graph.webp"/>
    <img src="../assets/graph_blurred.webp"/>
</div>

## Valid `extras` { data-toc-label="Valid Extras" }

Below is a table of all valid series extras parsed by this card. These are
described in greater detail below.

| Label                    | Default Value           | Description                                          |
| :----------------------: | :---------------------: | :--------------------------------------------------- |
| `graph_background_color` | `rgba(140,140,140,0.5)` | Background color of the graph                        |
| `graph_color`            | `rgb(99,184,255)`       | Color of the filled-in portion of the graph coloring |
| `graph_inset`            | `75`                    | How far to inset the graph from the edges            |
| `graph_radius`           | `175`                   | Radius of the graph                                  |
| `graph_text_font_size`   | `1.0`                   | Size adjustment for the graph text                   |
| `graph_width`            | `25`                    | The width of the graph                               |
| `fill_scale`             | `0.6`                   | Scale for how wide the filled graph should appear    |
| `omit_gradient`          | `#!yaml false`          | Whether to omit the gradient overlay                 |
| `percentage`             | -                       | Manual fill percentage of the graph                  |
| `text_position`          | `lower left`            | Where on the image to position the graph and text    |

## Customization

### Graph

#### Background Color (`graph_background_color`) { data-toc-label="Background Color" }

The background color of the graph can be adjusted with the
`graph_background_color` extra. This color can transparency so that part of the
image behind the graph can be seen. This defaults to `rgba(140,140,140,0.5)`
(a neutral gray with 50% opacity).

??? example "Example"

    ```yaml hl_lines="5"
    series:
      Reacher (2022):
        card_type: graph
        extras:
          graph_background_color: "rgba(232,232,232,0.2)"
    ```

    <div class="image-compare example-card"
        data-starting-point="12.5"
        data-left-label="rgba(140,140,140,0.5)" data-right-label="rgba(232,232,232,0.2)">
        <img src="../../../../card_types/assets/graph.webp"/>
        <img src="../../../../card_types/assets/graph-background.webp"/>
    </div>

#### Fill Color (`graph_color`) { data-toc-label="Fill Color" }

The filled portion of the graph (as well as the color of the inside numerator
and denominator) can be adjusted with the `graph_color` extra. This defaults to
`rgb(99,184,255)` (which is a light blue).

This color is also used for the numerator (the top part of the fraction), and
the line/denominator (the bottom part of the fraction) if the filled percentage
is 100% (see the example below).

??? example "Example"

    ```yaml hl_lines="5"
    series:
      Reacher (2022):
        card_type: graph
        extras:
          graph_color: SpringGreen1
    ```

    <div class="image-compare example-card"
        data-starting-point="12.5"
        data-left-label="rgb(99,184,255)" data-right-label="SpringGreen1">
        <img src="../../../../card_types/assets/graph.webp"/>
        <img src="../../../../card_types/assets/graph-color.webp"/>
    </div>

    <div class="image-compare example-card"
        data-starting-point="12.5"
        data-left-label="rgb(99,184,255)" data-right-label="SpringGreen1">
        <img src="../../../../card_types/assets/graph.webp"/>
        <img src="../../../../card_types/assets/graph-color-filled.webp"/>
    </div>

#### Fill Percentage (`percentage`) { data-toc-label="Fill Percentage" }

This card determines how "filled" to make the graph by parsing the episode text.
This means that _by default_, the progress of the graph will be based on the
episode number and how many episodes are in that season.

If you'd like to set the percentage to a _fixed_ number (e.g. something that
does not change), then the `percentage` extra can be specified. This must be
a number (intepreted as a percentage) between `0.0` and `1.0`.

This can be specified for the entire series, or per-episode in the data file.

??? example "Example"

    === "Per-Series"

        ```yaml title="tv.yml" hl_lines="5"
        series:
          Reacher (2022):
            card_type: graph
            extras:
              percentage: 0.3 # (1)!
        ```

        1. This indicates 30% filled

    === "Per-Episode"

        ```yaml title="data.yml" hl_lines="5 8"
        data:
          Season 1:
            1:
              title: Welcome to Margrave
              percentage: 0.125 # (1)!
            2:
              title: First Dance
              percentage: 0.250 # (2)!
        ```

        1. 12.5% filled
        2. 25.0% filled

#### Fill Scale (`fill_scale`) { data-toc-label="Fill Scale" }

How full relative to the background of the graph that the filled portion of the
graph appears can be adjusted with the `fill_scale` extra. This defaults to
`0.6`, meaning 60% of the width of the graph will be colored. This can be any
value between `0.0` (no fill at all) and `1.0` (completely filled).

??? example "Example"

    ```yaml hl_lines="5"
    series:
      Reacher (2022):
        card_type: graph
        extras:
          fill_scale: 0.2
    ```

    <div class="image-compare example-card"
        data-starting-point="12.5"
        data-left-label="0.6" data-right-label="0.2">
        <img src="../../../../card_types/assets/graph.webp"/>
        <img src="../../../../card_types/assets/graph-fill_scale.webp"/>
    </div>

#### Font Size (`graph_text_font_size`) { data-toc-label="Font Size" }

!!! note "Title Text Size"

    The font size of the title text is separately controlled with the normal
    `font` `size` value.

The font size of the fractional text inside the graph can be adjusted with the
`graph_text_font_size` extra. This is a scalar value greater than `0.0`, and
indicates how much to decrease or increase the size of the font from the
default.

??? example "Example"

    ```yaml hl_lines="5"
    series:
      Reacher (2022):
        card_type: graph
        extras:
          graph_text_font_size: 1.35
    ```

    <div class="image-compare example-card"
        data-starting-point="12.5"
        data-left-label="1.0" data-right-label="1.35">
        <img src="../../../../card_types/assets/graph.webp"/>
        <img src="../../../../card_types/assets/graph-font_size.webp"/>
    </div>

#### Inset (`graph_inset`) { data-toc-label="Inset" }

#### Radius (`graph_radius`) { data-toc-label="Radius" }

#### Width (`graph_width`) { data-toc-label="Width" }

### Gradient Overlay (`omit_gradient`) { data-toc-label="Gradient Overlay" }

### Position (`text_position`) { data-toc-label="Position" }

Where to position the graph and text can be controlled with the `text_position`
extra. This defaults to `lower left`, but can be `upper left`, `upper right`,
`left`, `right`, `lower left` or `lower right`.

The position will also adjust the orientation of the gradient overlay, if
[not disabled](#gradient-overlay-omit_gradient).

??? example "Example"

    ```yaml hl_lines="5"
    series:
      Reacher (2022):
        card_type: graph
        extras:
          text_position: right
    ```

    <div class="image-compare example-card"
        data-starting-point="12.5"
        data-left-label="lower left" data-right-label="right">
        <img src="../../../../card_types/assets/graph.webp"/>
        <img src="../../../../card_types/assets/graph-position.webp"/>
    </div>
