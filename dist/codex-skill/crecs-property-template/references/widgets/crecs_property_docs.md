# `crecs_property_docs` — CRECS: Property CA Docs

Generated from the delivery-1 catalog. Source file: `includes/widgets/template_widgets/class-elementor-crecs-property-docs-widget.php`.

| | |
| --- | --- |
| Relevance | **core** |
| Why | Gated CA / investor document library with its login and request-access popups. |
| Elementor categories | `cre-cloud-solutions-property-data` |
| Controls contributed by CRECS | 183 |
| Max instances per page | 1 |

> **Cardinality.** Renders fixed DOM ids (crecs_ca_docs_modal, ca_docs_title, crecs_sign_in_new_user, crecs_sign_in_user_email, property_slug) and binds jQuery handlers to them, so a second instance produces duplicate ids and two competing modals.
>
> Evidence: `includes/widgets/template_widgets/class-elementor-crecs-property-docs-widget.php:1244-1319,1383-1426`

## Keys from older exports

These appear in the reference `PropertyPage.json` but are **not registered** by the installed plugin. Use the current name.

| key in old exports | current control |
| --- | --- |
| `box_background_color` | `card_color` |

## Controls

#### content / content_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `show_label` | switcher | string ("" or "yes") | no | — | `"yes"` |
| `widget_title` | text | string | no | — | `"Investor Documents"` |

#### content / popup_content_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `popup_title` | text | string | no | — | `"Investor Log In"` |
| `login_form_label` | text | string | no | — | `"Existing Investor Log In"` |
| `login_form_text` | textarea | string | no | — | `""` |
| `request_access_label` | text | string | no | — | `"Request Investor Access"` |
| `request_access_text` | wysiwyg | string | no | — | `""` |
| `popup_template` | select | string | no | open (site-derived) | `""` |

#### style / button_form_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `button_form_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `button_form_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `button_form_hover_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `button_form_text_color` | color | string (hex or rgba) | no | — | `"#0985BA"` |
| `button_form_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `button_form_typography_font_family` | font | string (font family name) | no | — | `""` |
| `button_form_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `button_form_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `button_form_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `button_form_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `button_form_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `button_form_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `button_form_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `button_form_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `button_form_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `button_form_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |
| `button_form_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `button_form_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `button_form_border_color` | color | string (hex or rgba) | no | — | `""` |
| `button_form_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `button_form_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `button_form_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `button_form_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |

#### style / button_request_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `button_request_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `button_request_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `button_request_hover_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `button_request_text_color` | color | string (hex or rgba) | no | — | `"#0985BA"` |
| `button_request_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `button_request_typography_font_family` | font | string (font family name) | no | — | `""` |
| `button_request_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `button_request_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `button_request_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `button_request_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `button_request_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `button_request_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `button_request_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `button_request_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `button_request_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `button_request_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |
| `button_request_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `button_request_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `button_request_border_color` | color | string (hex or rgba) | no | — | `""` |
| `button_request_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `button_request_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `button_request_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `button_request_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |

#### style / button_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `button_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `button_size` | select | string | no | `auto` `100%` | `"auto"` |
| `button_align` | choose | string | no | `flex-start` `center` `flex-end` | `"center"` |
| `button_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `button_hover_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `button_text_color` | color | string (hex or rgba) | no | — | `"#0985BA"` |
| `button_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `button_typography_font_family` | font | string (font family name) | no | — | `""` |
| `button_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `button_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `button_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `button_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `button_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `button_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `button_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `button_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `button_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `button_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |
| `button_border_border` | select | string | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `button_border_width` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `button_border_color` | color | string (hex or rgba) | no | — | `""` |
| `button_border_radius` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, % | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `button_box_shadow_box_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `button_box_shadow_box_shadow` | box_shadow | object { horizontal, vertical, blur, spread, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `button_box_shadow_box_shadow_position` | select | string | no | ` ` `inset` | `" "` |

#### style / ca_docs_form_title_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `ca_docs_form_title_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `ca_docs_form_title_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `ca_docs_form_title_text_color` | color | string (hex or rgba) | no | — | `"#0985BA"` |
| `ca_docs_form_title_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `ca_docs_form_title_typography_font_family` | font | string (font family name) | no | — | `""` |
| `ca_docs_form_title_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `ca_docs_form_title_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `ca_docs_form_title_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `ca_docs_form_title_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `ca_docs_form_title_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `ca_docs_form_title_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `ca_docs_form_title_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `ca_docs_form_title_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `ca_docs_form_title_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `ca_docs_form_title_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

#### style / ca_docs_popup_title_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `ca_docs_popup_title_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `ca_docs_popup_title_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `ca_docs_popup_title_text_color` | color | string (hex or rgba) | no | — | `"#0985BA"` |
| `ca_docs_popup_title_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `ca_docs_popup_title_typography_font_family` | font | string (font family name) | no | — | `""` |
| `ca_docs_popup_title_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `ca_docs_popup_title_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `ca_docs_popup_title_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `ca_docs_popup_title_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `ca_docs_popup_title_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `ca_docs_popup_title_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `ca_docs_popup_title_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `ca_docs_popup_title_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `ca_docs_popup_title_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `ca_docs_popup_title_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

#### style / ca_docs_request_title_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `ca_docs_request_title_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `ca_docs_request_title_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `ca_docs_request_title_text_color` | color | string (hex or rgba) | no | — | `"#0985BA"` |
| `ca_docs_request_title_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `ca_docs_request_title_typography_font_family` | font | string (font family name) | no | — | `""` |
| `ca_docs_request_title_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `ca_docs_request_title_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `ca_docs_request_title_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `ca_docs_request_title_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `ca_docs_request_title_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `ca_docs_request_title_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `ca_docs_request_title_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `ca_docs_request_title_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `ca_docs_request_title_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `ca_docs_request_title_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

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

#### style / documents_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `documents_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | yes | units: px, %, em | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `documents_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `documents_hover_color` | color | string (hex or rgba) | no | — | `"#FFFFFF00"` |
| `documents_text_color` | color | string (hex or rgba) | no | — | `"#0985BA"` |
| `documents_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `documents_typography_font_family` | font | string (font family name) | no | — | `""` |
| `documents_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `documents_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `documents_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `documents_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `documents_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `documents_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `documents_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `documents_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `documents_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `documents_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

