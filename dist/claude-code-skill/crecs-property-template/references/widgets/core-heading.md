# `heading` — Heading (Elementor core)

Not a CRECS widget. Catalogued because a property template uses it: Carries scalar property values through the crecs-property dynamic tag on its `title` control (TEXT category).

Controls: 25.

#### content / section_title

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `title` | textarea |  | no | — | `"Add Your Heading Text Here"` |
| `link` | url |  | no | — | `{"url":"","is_external":"","nofollow":"","custom_attributes":""}` |
| `size` | select |  | no | `default` `small` `medium` `large` `xl` `xxl` | `"default"` |
| `header_size` | select |  | no | `h1` `h2` `h3` `h4` `h5` `h6` `div` `span` `p` | `"h2"` |

#### style / section_title_style

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `align` | choose |  | yes | `start` `center` `end` `justify` | `""` |
| `typography_typography` | popover_toggle |  | no | — | `""` |
| `typography_font_family` | font |  | no | — | `""` |
| `typography_font_size` | slider |  | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `typography_font_weight` | select |  | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `typography_text_transform` | select |  | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `typography_font_style` | select |  | no | `` `normal` `italic` `oblique` | `""` |
| `typography_text_decoration` | select |  | no | `` `underline` `overline` `line-through` `none` | `""` |
| `typography_line_height` | slider |  | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `typography_letter_spacing` | slider |  | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `typography_word_spacing` | slider |  | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `text_stroke_text_stroke_type` | popover_toggle |  | no | — | `""` |
| `text_stroke_text_stroke` | slider |  | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `text_stroke_stroke_color` | color |  | no | — | `"#000"` |
| `text_shadow_text_shadow_type` | popover_toggle |  | no | — | `""` |
| `text_shadow_text_shadow` | text_shadow |  | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |
| `blend_mode` | select |  | no | `` `multiply` `screen` `overlay` `darken` `lighten` `color-dodge` `saturation` `color` `difference` `exclusion` `hue` `luminosity` | `""` |
| `separator` | divider |  | no | — | — |
| `title_color` | color |  | no | — | `""` |
| `title_hover_color` | color |  | no | — | `""` |
| `title_hover_color_transition_duration` | slider |  | no | units: s, ms, custom | `{"unit":"s","size":"","sizes":[]}` |

