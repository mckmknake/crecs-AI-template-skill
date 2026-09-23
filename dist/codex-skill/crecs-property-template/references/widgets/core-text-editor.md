# `text-editor` — Text Editor (Elementor core)

Not a CRECS widget. Catalogued because a property template uses it.

Controls: 41.

#### content / section_editor

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `editor` | wysiwyg |  | no | — | `"<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut elit tellus, luctus nec ullamcorper mattis, pulvinar dapibus leo.</p>"` |
| `drop_cap` | switcher |  | no | — | `""` |
| `text_columns` | select |  | yes | `1` `2` `3` `4` `5` `6` `7` `8` `9` `10` `` | `""` |
| `column_gap` | slider |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |

#### style / section_drop_cap

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `drop_cap_view` | select |  | no | `default` `stacked` `framed` | `"default"` |
| `drop_cap_primary_color` | color |  | no | — | `""` |
| `drop_cap_secondary_color` | color |  | no | — | `""` |
| `drop_cap_shadow_text_shadow_type` | popover_toggle |  | no | — | `""` |
| `drop_cap_shadow_text_shadow` | text_shadow |  | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |
| `drop_cap_size` | slider |  | no | units: px, em, rem, custom | `{"unit":"px","size":5,"sizes":[]}` |
| `drop_cap_space` | slider |  | no | units: px, em, rem, custom | `{"unit":"px","size":10,"sizes":[]}` |
| `drop_cap_border_radius` | slider |  | no | units: px, %, em, rem, custom | `{"unit":"%","size":"","sizes":[]}` |
| `drop_cap_border_width` | dimensions |  | no | units: px, %, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `drop_cap_typography_typography` | popover_toggle |  | no | — | `""` |
| `drop_cap_typography_font_family` | font |  | no | — | `""` |
| `drop_cap_typography_font_size` | slider |  | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `drop_cap_typography_font_weight` | select |  | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `drop_cap_typography_text_transform` | select |  | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `drop_cap_typography_font_style` | select |  | no | `` `normal` `italic` `oblique` | `""` |
| `drop_cap_typography_text_decoration` | select |  | no | `` `underline` `overline` `line-through` `none` | `""` |
| `drop_cap_typography_line_height` | slider |  | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `drop_cap_typography_word_spacing` | slider |  | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |

#### style / section_style

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
| `text_shadow_text_shadow_type` | popover_toggle |  | no | — | `""` |
| `text_shadow_text_shadow` | text_shadow |  | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |
| `paragraph_spacing` | slider |  | yes | units: px, em, rem, vh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `separator` | divider |  | no | — | — |
| `text_color` | color |  | no | — | `""` |
| `link_color` | color |  | no | — | `""` |
| `link_hover_color` | color |  | no | — | `""` |
| `link_hover_color_transition_duration` | slider |  | no | units: s, ms, custom | `{"unit":"s","size":"","sizes":[]}` |

