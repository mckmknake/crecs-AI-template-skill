# `crecs_property_media` — CRECS: Property Media Box

Generated from the delivery-1 catalog. Source file: `includes/widgets/template_widgets/class-elementor-crecs-property-media-widget.php`.

| | |
| --- | --- |
| Relevance | **core** |
| Why | Tabbed media box (images / map / street view / video / floor plans) for the current property. |
| Elementor categories | `cre-cloud-solutions-property-data` |
| Controls contributed by CRECS | 92 |
| Max instances per page | unlimited |

## Controls

#### content / content_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `first_box` | select | string | no | `image` `map` `street_view` `video` | `"image"` |
| `show_map_box` | switcher | string ("" or "yes") | no | — | `"yes"` |
| `show_street_view_box` | switcher | string ("" or "yes") | no | — | `"yes"` |
| `show_image_box` | switcher | string ("" or "yes") | no | — | `"yes"` |
| `show_video_box` | switcher | string ("" or "yes") | no | — | `"yes"` |

#### content / image_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `show_thumbnails` | switcher | string ("" or "yes") | no | — | `"yes"` |
| `image_width` | slider | object { unit, size, sizes[] } | no | units: px, %, em, rem, custom | `{"unit":"%","size":100,"sizes":[]}` |

#### content / map_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `map_type` | select | string | no | `roadmap` `satellite` `hybrid` `terrain` | `"roadmap"` |
| `width` | slider | object { unit, size, sizes[] } | no | units: px, %, em, rem, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `height` | slider | object { unit, size, sizes[] } | no | units: px, %, em, rem, custom | `{"unit":"px","size":500,"sizes":[]}` |
| `zoom_level` | number | number or numeric string | no | — | `15` |

#### content / street_view_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `street_view_width` | slider | object { unit, size, sizes[] } | no | units: px, %, em, rem, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `street_view_height` | slider | object { unit, size, sizes[] } | no | units: px, %, em, rem, custom | `{"unit":"px","size":500,"sizes":[]}` |

#### content / video_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `video_width` | slider | object { unit, size, sizes[] } | no | units: px, %, em, rem, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `video_height` | slider | object { unit, size, sizes[] } | no | units: px, %, em, rem, custom | `{"unit":"px","size":500,"sizes":[]}` |

#### style / images_banner_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `images_banner_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `images_banner_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `images_banner_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `images_banner_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `images_banner_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `images_banner_border_color` | color | string (hex or rgba) | no | — | `""` |
| `images_banner_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `images_banner_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `images_banner_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `images_banner_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |
| `images_banner_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `images_banner_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `"yes"` |
| `images_banner_typography_font_family` | font | string (font family name) | no | — | `""` |
| `images_banner_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":24,"sizes":[]}` |
| `images_banner_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `300` |
| `images_banner_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `images_banner_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `images_banner_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `images_banner_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"em","size":1.4,"sizes":[]}` |
| `images_banner_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `images_banner_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `images_banner_text_alignment` | choose | string | no | `left` `center` `right` | `"left"` |
| `images_banner_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `images_banner_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

#### style / media_box_body_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `media_box_body_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `media_box_body_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `media_box_body_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `media_box_body_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `media_box_body_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `media_box_body_border_color` | color | string (hex or rgba) | no | — | `""` |
| `media_box_body_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `media_box_body_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `media_box_body_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `media_box_body_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |

#### style / media_box_header_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `media_box_header_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `media_box_header_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `media_box_header_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `media_box_header_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `media_box_header_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `media_box_header_border_color` | color | string (hex or rgba) | no | — | `""` |
| `media_box_header_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `media_box_header_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `media_box_header_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `media_box_header_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |
| `media_box_header_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `media_box_header_typography_font_family` | font | string (font family name) | no | — | `""` |
| `media_box_header_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `media_box_header_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `media_box_header_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `media_box_header_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `media_box_header_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `media_box_header_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `media_box_header_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `media_box_header_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `media_box_header_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `media_box_header_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `media_box_header_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

#### style / media_box_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `media_box_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `media_box_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `media_box_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `media_box_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `media_box_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `media_box_border_color` | color | string (hex or rgba) | no | — | `""` |
| `media_box_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `media_box_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `media_box_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `media_box_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |

#### style / tabs_row_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `tabs_row_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `tabs_row_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `tabs_row_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `tabs_row_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `tabs_row_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `tabs_row_border_color` | color | string (hex or rgba) | no | — | `""` |
| `tabs_row_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `tabs_row_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `tabs_row_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `tabs_row_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |

