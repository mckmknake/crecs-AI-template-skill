# `crecs_property_details` — CRECS: Property Details

Generated from the delivery-1 catalog. Source file: `includes/widgets/template_widgets/class-elementor-crecs-property-details-widget.php`.

| | |
| --- | --- |
| Relevance | **core** |
| Why | Auto-formatted property detail block. |
| Elementor categories | `cre-cloud-solutions-property-data` |
| Controls contributed by CRECS | 83 |
| Max instances per page | unlimited |

## Keys from older exports

These appear in the reference `PropertyPage.json` but are **not registered** by the installed plugin. Use the current name.

| key in old exports | current control |
| --- | --- |
| `data_typography_font_size` | `field_data_typography_font_size` |
| `label_typography_font_size` | `field_label_typography_font_size` |

## Controls

#### content / content_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `layout_type` | select | string | no | `list` `two_column` | `"list"` |
| `show_label` | switcher | string ("" or "yes") | no | — | `"yes"` |
| `first_column_alignment` | choose | string | no | `left` `center` `right` | `"left"` |
| `second_column_alignment` | choose | string | no | `left` `center` `right` | `"left"` |

#### style / card_body_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `card_body_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `card_body_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `card_body_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `card_body_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `card_body_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `card_body_border_color` | color | string (hex or rgba) | no | — | `""` |
| `card_body_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `card_body_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `card_body_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `card_body_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |

#### style / card_header_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `card_header_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `card_header_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `card_header_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `card_header_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `card_header_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `card_header_border_color` | color | string (hex or rgba) | no | — | `""` |
| `card_header_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `card_header_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `card_header_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `card_header_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |
| `card_header_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `card_header_typography_font_family` | font | string (font family name) | no | — | `""` |
| `card_header_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `card_header_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `card_header_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `card_header_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `card_header_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `card_header_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `card_header_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `card_header_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `card_header_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `card_header_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `card_header_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

#### style / card_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `card_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `card_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `card_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `card_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `card_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `card_border_color` | color | string (hex or rgba) | no | — | `""` |
| `card_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `card_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `card_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `card_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |

#### style / field_label_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `row_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `row_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `row_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `row_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `row_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `row_border_color` | color | string (hex or rgba) | no | — | `""` |
| `row_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `row_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `row_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `row_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |
| `field_label_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `"yes"` |
| `field_label_typography_font_family` | font | string (font family name) | no | — | `""` |
| `field_label_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":24,"sizes":[]}` |
| `field_label_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `300` |
| `field_label_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `field_label_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `field_label_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `field_label_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"em","size":1.4,"sizes":[]}` |
| `field_label_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `field_label_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `field_label_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `field_label_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `field_label_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |
| `field_data_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `"yes"` |
| `field_data_typography_font_family` | font | string (font family name) | no | — | `""` |
| `field_data_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":24,"sizes":[]}` |
| `field_data_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `300` |
| `field_data_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `field_data_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `field_data_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `field_data_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"em","size":1.4,"sizes":[]}` |
| `field_data_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `field_data_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `field_data_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `field_data_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `field_data_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

