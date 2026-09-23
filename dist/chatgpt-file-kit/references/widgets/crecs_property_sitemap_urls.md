# `crecs_property_sitemap_urls` — CRECS: Property Sitemap URLs

Generated from the delivery-1 catalog. Source file: `includes/widgets/template_widgets/class-elementor-crecs-property-sitemap-urls-widget.php`.

| | |
| --- | --- |
| Relevance | **core** |
| Why | SEO "discover more" link block. |
| Elementor categories | `cre-cloud-solutions-property-data` |
| Controls contributed by CRECS | 31 |
| Max instances per page | unlimited |

## Keys from older exports

These appear in the reference `PropertyPage.json` but are **not registered** by the installed plugin. Use the current name.

| key in old exports | current control |
| --- | --- |
| `content_width` | **no equivalent** |
| `section_title_text_color` | `sitemap_urls_header_text_color` |
| `section_title_typography_font_family` | `sitemap_urls_header_typography_font_family` |
| `section_title_typography_font_size` | `sitemap_urls_header_typography_font_size` |
| `section_title_typography_font_weight` | `sitemap_urls_header_typography_font_weight` |
| `section_title_typography_typography` | `sitemap_urls_header_typography_typography` |
| `urls_text_color` | `sitemap_urls_text_color` |
| `urls_typography_font_family` | `sitemap_urls_typography_font_family` |
| `urls_typography_font_size` | `sitemap_urls_typography_font_size` |
| `urls_typography_typography` | `sitemap_urls_typography_typography` |

## Controls

#### content / content_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `layout_type` | select | string | no | `columns` | `"columns"` |
| `show_label` | switcher | string ("" or "yes") | no | — | `"yes"` |
| `label` | text | string | no | — | `"Discover more properties"` |

#### style / container_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `container_margin` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, %, em, rem, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `container_padding` | dimensions | object { unit, top, right, bottom, left, isLinked } | no | units: px, %, em, rem, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |

#### style / sitemap_urls_header_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `sitemap_urls_header_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `sitemap_urls_header_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `sitemap_urls_header_typography_font_family` | font | string (font family name) | no | — | `""` |
| `sitemap_urls_header_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `sitemap_urls_header_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `sitemap_urls_header_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `sitemap_urls_header_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `sitemap_urls_header_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `sitemap_urls_header_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `sitemap_urls_header_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `sitemap_urls_header_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `sitemap_urls_header_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `sitemap_urls_header_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

#### style / sitemap_urls_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `sitemap_urls_text_color` | color | string (hex or rgba) | no | — | `"#000000"` |
| `sitemap_urls_typography_typography` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `sitemap_urls_typography_font_family` | font | string (font family name) | no | — | `""` |
| `sitemap_urls_typography_font_size` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `sitemap_urls_typography_font_weight` | select | string | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `sitemap_urls_typography_text_transform` | select | string | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `sitemap_urls_typography_font_style` | select | string | no | `` `normal` `italic` `oblique` | `""` |
| `sitemap_urls_typography_text_decoration` | select | string | no | `` `underline` `overline` `line-through` `none` | `""` |
| `sitemap_urls_typography_line_height` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `sitemap_urls_typography_letter_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `sitemap_urls_typography_word_spacing` | slider | object { unit, size, sizes[] } | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `sitemap_urls_text_shadow_text_shadow_type` | popover_toggle | string ("" or "custom"/"yes") | no | — | `""` |
| `sitemap_urls_text_shadow_text_shadow` | text_shadow | object { horizontal, vertical, blur, color } | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |

