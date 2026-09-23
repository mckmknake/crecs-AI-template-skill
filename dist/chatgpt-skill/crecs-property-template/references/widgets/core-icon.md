# `icon` — Icon (Elementor core)

Not a CRECS widget. Catalogued because a property template uses it.

Controls: 16.

#### content / section_icon

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `selected_icon` | icons |  | no | — | `{"value":"fas fa-star","library":"fa-solid"}` |
| `view` | select |  | no | `default` `stacked` `framed` | `"default"` |
| `shape` | select |  | no | `square` `rounded` `circle` | `"circle"` |
| `link` | url |  | no | — | `{"url":"","is_external":"","nofollow":"","custom_attributes":""}` |

#### style / section_style_icon

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `align` | choose |  | yes | `start` `center` `end` | `"center"` |
| `primary_color` | color |  | no | — | `""` |
| `secondary_color` | color |  | no | — | `""` |
| `hover_primary_color` | color |  | no | — | `""` |
| `hover_secondary_color` | color |  | no | — | `""` |
| `hover_animation` | hover_animation |  | no | — | `""` |
| `size` | slider |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `fit_to_size` | switcher |  | no | — | `""` |
| `icon_padding` | slider |  | no | units: px, %, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `rotate` | slider |  | yes | units: deg, grad, rad, turn, custom | `{"unit":"deg","size":"","sizes":[]}` |
| `border_width` | dimensions |  | no | units: px, %, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `border_radius` | dimensions |  | yes | units: px, %, em, rem, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |

