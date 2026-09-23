# `crecs_property_photos` — CRECS: Property Photos

Generated from the delivery-1 catalog. Source file: `includes/widgets/template_widgets/class-elementor-crecs-property-photos-widget.php`.

| | |
| --- | --- |
| Relevance | **core** |
| Why | Standalone photo gallery for the current property. |
| Elementor categories | `cre-cloud-solutions-property-data` |
| Controls contributed by CRECS | 51 |
| Max instances per page | unlimited |

## Controls

#### content / content_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `layout_type` | select | string | no | `slide` `grid` | `"Slide"` |
| `show_banner` | switcher | string ("" or "yes") | no | — | `"yes"` |
| `show_thumbnails` | switcher | string ("" or "yes") | no | — | `"yes"` |
| `columns` | slider | object { unit, size, sizes[] } | yes | — | `{"unit":"px","size":"","sizes":[]}` |
| `max_height` | slider | object { unit, size, sizes[] } | yes | — | `{"unit":"px","size":"","sizes":[]}` |
| `limit` | number | number or numeric string | no | — | `6` |
| `initial_image` | number | number or numeric string | no | — | `1` |

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

#### style / photo_item

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `photo_item_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `photo_item_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `photo_item_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `photo_item_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `photo_item_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `photo_item_border_color` | color | string (hex or rgba) | no | — | `""` |
| `photo_item_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `photo_item_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `photo_item_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `photo_item_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |

#### style / photos_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `photos_section_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `photos_section_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `photos_section_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `photos_section_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `photos_section_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `photos_section_border_color` | color | string (hex or rgba) | no | — | `""` |
| `photos_section_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `photos_section_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `photos_section_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `photos_section_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |

