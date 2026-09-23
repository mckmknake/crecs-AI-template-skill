# `crecs_property_team_members` — CRECS: Property Team Members

Generated from the delivery-1 catalog. Source file: `includes/widgets/template_widgets/class-elementor-crecs-property-team-members-widget.php`.

| | |
| --- | --- |
| Relevance | **core** |
| Why | Brokers assigned to the current property. |
| Elementor categories | `cre-cloud-solutions-property-data` |
| Controls contributed by CRECS | 113 |
| Max instances per page | 1 |

> **Cardinality.** Renders a fixed id="contacts" wrapper.
>
> Evidence: `includes/widgets/template_widgets/class-elementor-crecs-property-team-members-widget.php:986`

## Controls

#### content / content_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `layout_type` | select | string | no | `list` | `"list"` |
| `show_label` | switcher | string ("" or "yes") | no | — | `"yes"` |
| `show_image_responsive` | select | string | yes | `block` `none` | `"block"` |
| `show_rounded_image` | switcher | string ("" or "yes") | no | — | `"no"` |
| `image_width` | slider | object { unit, size, sizes[] } | no | units: px, %, em, rem, custom | `{"unit":"px","size":100,"sizes":[]}` |
| `flex_direction` | choose | string | no | `row` `column` | `"row"` |
| `limit` | number | number or numeric string | no | — | `2` |

#### content / phone_content_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `display_phone_labels` | switcher | string ("" or "yes") | no | — | `"no"` |
| `phone_label_start` | text | string | no | — | `""` |
| `phone_label_end` | text | string | no | — | `""` |
| `mobile_label_start` | text | string | no | — | `""` |
| `mobile_label_end` | text | string | no | — | `""` |

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

#### style / team_member_card_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `team_member_card_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `team_member_card_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `team_member_card_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `team_member_card_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `team_member_card_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `team_member_card_border_color` | color | string (hex or rgba) | no | — | `""` |
| `team_member_card_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `team_member_card_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `team_member_card_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `team_member_card_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |

#### style / team_member_email_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `team_member_email_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `team_member_email_alignment` | select | string | no | `left` `right` `center` | `""` |
| `team_member_email_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `team_member_email_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `team_member_email_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `"yes"` |
| `team_member_email_typography_font_family` | font | string (font family name) | no | — | `""` |
| `team_member_email_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":24,"sizes":[]}` |
| `team_member_email_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `300` |
| `team_member_email_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `team_member_email_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `team_member_email_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `team_member_email_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"em","size":1.4,"sizes":[]}` |
| `team_member_email_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `team_member_email_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `team_member_email_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `team_member_email_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

#### style / team_member_header_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `team_member_header_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `team_member_header_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `team_member_header_alignment` | select | string | no | `left` `right` `center` | `""` |
| `team_member_header_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `team_member_header_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `team_member_header_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `team_member_header_typography_font_family` | font | string (font family name) | no | — | `""` |
| `team_member_header_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `team_member_header_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `team_member_header_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `team_member_header_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `team_member_header_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `team_member_header_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `team_member_header_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `team_member_header_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `team_member_header_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `team_member_header_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

#### style / team_member_mobile_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `team_member_mobile_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `team_member_mobile_alignment` | select | string | no | `left` `right` `center` | `""` |
| `team_member_mobile_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `team_member_mobile_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `team_member_mobile_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `"yes"` |
| `team_member_mobile_typography_font_family` | font | string (font family name) | no | — | `""` |
| `team_member_mobile_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":24,"sizes":[]}` |
| `team_member_mobile_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `300` |
| `team_member_mobile_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `team_member_mobile_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `team_member_mobile_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `team_member_mobile_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"em","size":1.4,"sizes":[]}` |
| `team_member_mobile_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `team_member_mobile_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `team_member_mobile_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `team_member_mobile_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

#### style / team_member_name_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `team_member_name_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `team_member_name_alignment` | select | string | no | `left` `right` `center` | `""` |
| `team_member_name_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `team_member_name_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `team_member_name_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `"yes"` |
| `team_member_name_typography_font_family` | font | string (font family name) | no | — | `""` |
| `team_member_name_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":24,"sizes":[]}` |
| `team_member_name_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `300` |
| `team_member_name_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `team_member_name_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `team_member_name_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `team_member_name_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"em","size":1.4,"sizes":[]}` |
| `team_member_name_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `team_member_name_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `team_member_name_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `team_member_name_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

#### style / team_member_phone_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `team_member_phone_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `team_member_phone_alignment` | select | string | no | `left` `right` `center` | `""` |
| `team_member_phone_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `team_member_phone_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `team_member_phone_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `"yes"` |
| `team_member_phone_typography_font_family` | font | string (font family name) | no | — | `""` |
| `team_member_phone_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":24,"sizes":[]}` |
| `team_member_phone_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `300` |
| `team_member_phone_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `team_member_phone_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `team_member_phone_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `team_member_phone_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"em","size":1.4,"sizes":[]}` |
| `team_member_phone_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `team_member_phone_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `team_member_phone_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `team_member_phone_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

