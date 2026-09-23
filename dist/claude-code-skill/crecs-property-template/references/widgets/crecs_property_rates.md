# `crecs_property_rates` — CRECS: Property Rates

Generated from the delivery-1 catalog. Source file: `includes/widgets/template_widgets/class-elementor-crecs-property-rates-widget.php`.

| | |
| --- | --- |
| Relevance | **core** |
| Why | Standalone rate/price block. |
| Elementor categories | `cre-cloud-solutions-property-data` |
| Controls contributed by CRECS | 18 |
| Max instances per page | unlimited |

## Controls

#### content / content_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `property_rate` | select | string | no | `rate_1` `rate_2` `rate_3` `both` | `"rate_1"` |
| `rate_style` | select | string | no | `block` `inline-block` | `"block"` |
| `show_label` | switcher | string ("" or "yes") | no | — | `"yes"` |

#### style / rate_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `rate_alignment` | choose | string | no | `left` `center` `right` | `"left"` |
| `rate_bg_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `rate_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `rate_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `rate_typography_font_family` | font | string (font family name) | no | — | `""` |
| `rate_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `rate_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `rate_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `rate_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `rate_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `rate_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `rate_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `rate_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `rate_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `rate_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

