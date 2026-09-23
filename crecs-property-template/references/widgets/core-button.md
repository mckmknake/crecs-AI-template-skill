# `button` — Button (Elementor core)

Not a CRECS widget. Catalogued because a property template uses it: Carries flyer_url through crecs-property on its `link` control (URL category), and Elementor Pro popup bindings on the same control.

Controls: 108.

#### content / section_button

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `button_type` | select |  | no | `` `info` `success` `warning` `danger` | `""` |
| `text` | text |  | no | — | `"Click here"` |
| `link` | url |  | no | — | `{"url":"#","is_external":"","nofollow":"","custom_attributes":""}` |
| `size` | select |  | no | `xs` `sm` `md` `lg` `xl` | `"sm"` |
| `selected_icon` | icons |  | no | — | `{"value":"","library":""}` |
| `icon_align` | choose |  | no | `row` `row-reverse` | `"row"` |
| `icon_indent` | slider |  | no | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `button_css_id` | text |  | no | — | `""` |

#### style / section_style

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `align` | choose |  | no | `left` `center` `right` `justify` | `""` |
| `align_tablet` | choose |  | no | `left` `center` `right` `justify` | `""` |
| `align_mobile` | choose |  | no | `left` `center` `right` `justify` | `""` |
| `content_align` | choose |  | yes | `start` `center` `end` `space-between` | `""` |
| `typography_typography` | popover_toggle |  | no | — | `""` |
| `typography_font_family` | font |  | no | — | `""` |
| `typography_font_size` | slider |  | yes | units: px, em, rem, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `typography_font_weight` | select |  | no | `100` `200` `300` `400` `500` `600` `700` `800` `900` `` `normal` `bold` | `""` |
| `typography_text_transform` | select |  | no | `` `uppercase` `lowercase` `capitalize` `none` | `""` |
| `typography_font_style` | select |  | no | `` `normal` `italic` `oblique` | `""` |
| `typography_text_decoration` | select |  | no | `` `underline` `overline` `line-through` `none` | `""` |
| `typography_line_height` | slider |  | yes | units: px, em, rem, lh, rlh, custom | `{"unit":"px","size":"","sizes":[]}` |
| `typography_letter_spacing` | slider |  | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `typography_word_spacing` | slider |  | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `text_shadow_text_shadow_type` | popover_toggle |  | no | — | `""` |
| `text_shadow_text_shadow` | text_shadow |  | no | — | `{"horizontal":0,"vertical":0,"blur":10,"color":"rgba(0,0,0,0.3)"}` |
| `button_text_color` | color |  | no | — | `""` |
| `background_background` | choose |  | no | `classic` `gradient` | `"classic"` |
| `background_gradient_notice` | alert |  | no | — | — |
| `background_color` | color |  | no | — | `""` |
| `background_color_stop` | slider |  | yes | units: %, custom | `{"unit":"%","size":0,"sizes":[]}` |
| `background_color_b` | color |  | no | — | `"#f2295b"` |
| `background_color_b_stop` | slider |  | yes | units: %, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `background_gradient_type` | select |  | no | `linear` `radial` | `"linear"` |
| `background_gradient_angle` | slider |  | yes | units: deg, grad, rad, turn, custom | `{"unit":"deg","size":180,"sizes":[]}` |
| `background_gradient_position` | select |  | yes | `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` | `"center center"` |
| `background_position` | select |  | yes | `` `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` `initial` | `""` |
| `background_xpos` | slider |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"px","size":0,"sizes":[]}` |
| `background_ypos` | slider |  | yes | units: px, %, em, rem, vh, custom | `{"unit":"px","size":0,"sizes":[]}` |
| `background_attachment` | select |  | no | `` `scroll` `fixed` | `""` |
| `background_attachment_alert` | raw_html |  | no | — | — |
| `background_repeat` | select |  | yes | `` `no-repeat` `repeat` `repeat-x` `repeat-y` | `""` |
| `background_size` | select |  | yes | `` `auto` `cover` `contain` `initial` | `""` |
| `background_bg_width` | slider |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `background_video_link` | text |  | no | — | `""` |
| `background_video_start` | number |  | no | — | `""` |
| `background_video_end` | number |  | no | — | `""` |
| `background_play_once` | switcher |  | no | — | `""` |
| `background_play_on_mobile` | switcher |  | no | — | `""` |
| `background_privacy_mode` | switcher |  | no | — | `""` |
| `background_video_fallback` | media |  | no | — | `{"url":"","id":"","size":""}` |
| `background_slideshow_gallery` | gallery |  | no | — | — |
| `background_slideshow_loop` | switcher |  | no | — | `"yes"` |
| `background_slideshow_slide_duration` | number |  | no | — | `5000` |
| `background_slideshow_slide_transition` | select |  | no | `fade` `slide_right` `slide_left` `slide_up` `slide_down` | `"fade"` |
| `background_slideshow_transition_duration` | number |  | no | — | `500` |
| `background_slideshow_background_size` | select |  | yes | `` `auto` `cover` `contain` | `""` |
| `background_slideshow_background_position` | select |  | yes | `` `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` | `""` |
| `background_slideshow_lazyload` | switcher |  | no | — | `""` |
| `background_slideshow_ken_burns` | switcher |  | no | — | `""` |
| `background_slideshow_ken_burns_zoom_direction` | select |  | no | `in` `out` | `"in"` |
| `button_box_shadow_box_shadow_type` | popover_toggle |  | no | — | `""` |
| `button_box_shadow_box_shadow` | box_shadow |  | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `button_box_shadow_box_shadow_position` | select |  | no | ` ` `inset` | `" "` |
| `hover_color` | color |  | no | — | `""` |
| `button_background_hover_background` | choose |  | no | `classic` `gradient` | `"classic"` |
| `button_background_hover_gradient_notice` | alert |  | no | — | — |
| `button_background_hover_color` | color |  | no | — | `""` |
| `button_background_hover_color_stop` | slider |  | yes | units: %, custom | `{"unit":"%","size":0,"sizes":[]}` |
| `button_background_hover_color_b` | color |  | no | — | `"#f2295b"` |
| `button_background_hover_color_b_stop` | slider |  | yes | units: %, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `button_background_hover_gradient_type` | select |  | no | `linear` `radial` | `"linear"` |
| `button_background_hover_gradient_angle` | slider |  | yes | units: deg, grad, rad, turn, custom | `{"unit":"deg","size":180,"sizes":[]}` |
| `button_background_hover_gradient_position` | select |  | yes | `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` | `"center center"` |
| `button_background_hover_position` | select |  | yes | `` `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` `initial` | `""` |
| `button_background_hover_xpos` | slider |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"px","size":0,"sizes":[]}` |
| `button_background_hover_ypos` | slider |  | yes | units: px, %, em, rem, vh, custom | `{"unit":"px","size":0,"sizes":[]}` |
| `button_background_hover_attachment` | select |  | no | `` `scroll` `fixed` | `""` |
| `button_background_hover_attachment_alert` | raw_html |  | no | — | — |
| `button_background_hover_repeat` | select |  | yes | `` `no-repeat` `repeat` `repeat-x` `repeat-y` | `""` |
| `button_background_hover_size` | select |  | yes | `` `auto` `cover` `contain` `initial` | `""` |
| `button_background_hover_bg_width` | slider |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `button_background_hover_video_link` | text |  | no | — | `""` |
| `button_background_hover_video_start` | number |  | no | — | `""` |
| `button_background_hover_video_end` | number |  | no | — | `""` |
| `button_background_hover_play_once` | switcher |  | no | — | `""` |
| `button_background_hover_play_on_mobile` | switcher |  | no | — | `""` |
| `button_background_hover_privacy_mode` | switcher |  | no | — | `""` |
| `button_background_hover_video_fallback` | media |  | no | — | `{"url":"","id":"","size":""}` |
| `button_background_hover_slideshow_gallery` | gallery |  | no | — | — |
| `button_background_hover_slideshow_loop` | switcher |  | no | — | `"yes"` |
| `button_background_hover_slideshow_slide_duration` | number |  | no | — | `5000` |
| `button_background_hover_slideshow_slide_transition` | select |  | no | `fade` `slide_right` `slide_left` `slide_up` `slide_down` | `"fade"` |
| `button_background_hover_slideshow_transition_duration` | number |  | no | — | `500` |
| `button_background_hover_slideshow_background_size` | select |  | yes | `` `auto` `cover` `contain` | `""` |
| `button_background_hover_slideshow_background_position` | select |  | yes | `` `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` | `""` |
| `button_background_hover_slideshow_lazyload` | switcher |  | no | — | `""` |
| `button_background_hover_slideshow_ken_burns` | switcher |  | no | — | `""` |
| `button_background_hover_slideshow_ken_burns_zoom_direction` | select |  | no | `in` `out` | `"in"` |
| `button_hover_border_color` | color |  | no | — | `""` |
| `button_hover_box_shadow_box_shadow_type` | popover_toggle |  | no | — | `""` |
| `button_hover_box_shadow_box_shadow` | box_shadow |  | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `button_hover_box_shadow_box_shadow_position` | select |  | no | ` ` `inset` | `" "` |
| `button_hover_transition_duration` | slider |  | no | units: s, ms, custom | `{"unit":"s","size":"","sizes":[]}` |
| `hover_animation` | hover_animation |  | no | — | `""` |
| `border_border` | select |  | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `border_width` | dimensions |  | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `border_color` | color |  | no | — | `""` |
| `border_radius` | dimensions |  | yes | units: px, %, em, rem, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `text_padding` | dimensions |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |

