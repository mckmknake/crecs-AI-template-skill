# `crecs_property_suites` — CRECS: Property Suites

Generated from the delivery-1 catalog. Source file: `includes/widgets/template_widgets/class-elementor-crecs-property-suites-widget.php`.

| | |
| --- | --- |
| Relevance | **core** |
| Why | Available-suite table. Commonly placed twice (desktop table + mobile stack) using Elementor responsive visibility. |
| Elementor categories | `cre-cloud-solutions-property-data` |
| Controls contributed by CRECS | 83 |
| Max instances per page | unlimited |

## Keys from older exports

These appear in the reference `PropertyPage.json` but are **not registered** by the installed plugin. Use the current name.

| key in old exports | current control |
| --- | --- |
| `attachment_text_color` | `attachment_link_text_color` |
| `attachment_text_color_hover` | `attachment_link_text_color_hover` |
| `attachment_typography_font_family` | `attachment_link_typography_font_family` |
| `attachment_typography_font_size` | `attachment_link_typography_font_size` |
| `table_head_text_color` | `card_body_thead_text_color` |
| `table_head_typography_font_family` | `card_body_thead_typography_font_family` |
| `table_head_typography_font_size` | `card_body_thead_typography_font_size` |
| `table_head_typography_font_weight` | `card_body_thead_typography_font_weight` |
| `text_color` | `card_body_text_color` |
| `typography_font_family` | `card_body_typography_font_family` |
| `typography_font_size` | `card_body_typography_font_size` |
| `typography_typography` | `card_body_typography_typography` |

## Controls

#### content / content_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `layout_type` | select | string | no | `list` `table` | `"list"` |
| `show_label` | switcher | string ("" or "yes") | no | — | `"yes"` |

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
| `card_body_thead_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `"yes"` |
| `card_body_thead_typography_font_family` | font | string (font family name) | no | — | `""` |
| `card_body_thead_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":16,"sizes":[]}` |
| `card_body_thead_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `300` |
| `card_body_thead_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `card_body_thead_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `card_body_thead_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `card_body_thead_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"em","size":1.4,"sizes":[]}` |
| `card_body_thead_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `card_body_thead_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `card_body_thead_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `card_body_thead_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `card_body_thead_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |
| `card_body_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `"yes"` |
| `card_body_typography_font_family` | font | string (font family name) | no | — | `""` |
| `card_body_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":16,"sizes":[]}` |
| `card_body_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `300` |
| `card_body_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `card_body_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `card_body_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `card_body_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"em","size":1.4,"sizes":[]}` |
| `card_body_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `card_body_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `card_body_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `card_body_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `card_body_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |
| `attachment_link_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `"yes"` |
| `attachment_link_typography_font_family` | font | string (font family name) | no | — | `""` |
| `attachment_link_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":16,"sizes":[]}` |
| `attachment_link_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `300` |
| `attachment_link_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `attachment_link_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `attachment_link_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `attachment_link_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"em","size":1.4,"sizes":[]}` |
| `attachment_link_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `attachment_link_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `attachment_link_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `attachment_link_text_color_hover` | color | string (hex or rgba) | no | — | `"#000000"` |

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

