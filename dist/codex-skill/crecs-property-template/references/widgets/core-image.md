# `image` — Image (Elementor core)

Not a CRECS widget. Catalogued because a property template uses it.

Controls: 53.

#### content / section_image

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `image` | media |  | no | — | `{"url":"http://kingrealty.local/wp-content/plugins/elementor/assets/images/placeholder.png","id":"","size":""}` |
| `image_size` | select |  | no | `thumbnail` `medium` `medium_large` `large` `1536x1536` `2048x2048` `ocean-thumb-m` `ocean-thumb-ml` `ocean-thumb-l` `full` `custom` | `"large"` |
| `image_custom_dimension` | image_dimensions |  | no | — | `{"width":"","height":""}` |
| `caption_source` | select |  | no | `none` `attachment` `custom` | `"none"` |
| `caption` | text |  | no | — | `""` |
| `link_to` | select |  | no | `none` `file` `custom` | `"none"` |
| `link` | url |  | no | — | `{"url":"","is_external":"","nofollow":"","custom_attributes":""}` |
| `open_lightbox` | select |  | no | `default` `yes` `no` | `"default"` |

#### style / section_style_caption

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `caption_align` | choose |  | yes | `start` `center` `end` `justify` | `""` |
| `text_color` | color |  | no | — | `""` |
| `caption_background_color` | color |  | no | — | `""` |
| `caption_typography_typography` | popover_toggle |  | no | — | `""` |
| `caption_typography_font_family` | font |  | no | — | `""` |
| `caption_typography_font_size` | slider |  | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `caption_typography_font_weight` | select |  | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `caption_typography_text_transform` | select |  | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `caption_typography_font_style` | select |  | no | `` `normal` `italic` `oblique` | `""` |
| `caption_typography_text_decoration` | select |  | no | `` `underline` `overline` `line-through` `none` | `""` |
| `caption_typography_line_height` | slider |  | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `caption_typography_letter_spacing` | slider |  | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `caption_typography_word_spacing` | slider |  | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `caption_text_shadow_text_shadow_type` | popover_toggle |  | no | — | `""` |
| `caption_text_shadow_text_shadow` | text_shadow |  | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |
| `caption_space` | slider |  | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |

#### style / section_style_image

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `align` | choose |  | yes | `start` `center` `end` | `""` |
| `width` | slider |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"%","size":"","sizes":[]}` |
| `space` | slider |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"%","size":"","sizes":[]}` |
| `height` | slider |  | yes | units: px, %, em, rem, vh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `object-fit` | select |  | yes | `` `fill` `cover` `contain` `scale-down` | `""` |
| `object-position` | select |  | yes | `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` | `"center center"` |
| `separator_panel_style` | divider |  | no | — | — |
| `opacity` | slider |  | no | — | `{"unit":"px","size":"","sizes":[]}` |
| `css_filters_css_filter` | popover_toggle |  | no | — | `""` |
| `css_filters_blur` | slider |  | no | — | `{"unit":"px","size":0,"sizes":[]}` |
| `css_filters_brightness` | slider |  | no | — | `{"unit":"px","size":100,"sizes":[]}` |
| `css_filters_contrast` | slider |  | no | — | `{"unit":"px","size":100,"sizes":[]}` |
| `css_filters_saturate` | slider |  | no | — | `{"unit":"px","size":100,"sizes":[]}` |
| `css_filters_hue` | slider |  | no | — | `{"unit":"px","size":0,"sizes":[]}` |
| `opacity_hover` | slider |  | no | — | `{"unit":"px","size":"","sizes":[]}` |
| `css_filters_hover_css_filter` | popover_toggle |  | no | — | `""` |
| `css_filters_hover_blur` | slider |  | no | — | `{"unit":"px","size":0,"sizes":[]}` |
| `css_filters_hover_brightness` | slider |  | no | — | `{"unit":"px","size":100,"sizes":[]}` |
| `css_filters_hover_contrast` | slider |  | no | — | `{"unit":"px","size":100,"sizes":[]}` |
| `css_filters_hover_saturate` | slider |  | no | — | `{"unit":"px","size":100,"sizes":[]}` |
| `css_filters_hover_hue` | slider |  | no | — | `{"unit":"px","size":0,"sizes":[]}` |
| `background_hover_transition` | slider |  | no | — | `{"unit":"px","size":"","sizes":[]}` |
| `hover_animation` | hover_animation |  | no | — | `""` |
| `image_border_border` | select |  | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `image_border_width` | dimensions |  | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `image_border_color` | color |  | no | — | `""` |
| `image_border_radius` | dimensions |  | yes | units: px, %, em, rem, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `image_box_shadow_box_shadow_type` | popover_toggle |  | no | — | `""` |
| `image_box_shadow_box_shadow` | box_shadow |  | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |

