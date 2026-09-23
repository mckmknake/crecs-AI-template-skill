# `section` — Elementor element type

Controls: 284.

#### advanced / _section_responsive

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `reverse_order_tablet` | switcher |  | no | — | `""` |
| `reverse_order_mobile` | switcher |  | no | — | `""` |
| `heading_visibility` | heading |  | no | — | — |

#### advanced / section_advanced

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `margin` | dimensions |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `padding` | dimensions |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `z_index` | number |  | yes | — | `""` |
| `css_classes` | text |  | no | — | `""` |

#### advanced / section_effects

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `animation` | animation |  | no | — | `""` |
| `animation_tablet` | animation |  | no | — | `""` |
| `animation_mobile` | animation |  | no | — | `""` |
| `animation_delay` | number |  | no | — | `""` |

#### advanced / section_premium_eq_height

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `premium_eq_height_update` | raw_html |  | no | — | — |
| `premium_eq_height_switcher` | switcher |  | no | — | `""` |
| `premium_eq_height_type` | select |  | no | `widget` `custom` | `"widget"` |
| `premium_eq_height_target` | premium-select |  | no | — | `""` |
| `premium_eq_height_custom_target` | text |  | no | — | `""` |
| `premium_eq_height_trigger` | select |  | no | `load` `scroll` | `"load"` |
| `premium_eq_height_enable_on` | select2 |  | no | `desktop` `tablet` `mobile` | `["desktop","tablet","mobile"]` |
| `doc_1` | raw_html |  | no | — | — |
| `doc_2` | raw_html |  | no | — | — |

#### layout / section_layout

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `layout` | select |  | no | `boxed` `full_width` | `"boxed"` |
| `content_width` | slider |  | yes | — | `{"unit":"px","size":"","sizes":[]}` |
| `gap` | select |  | no | `default` `no` `narrow` `extended` `wide` `wider` `custom` | `"default"` |
| `gap_columns_custom` | slider |  | yes | units: px, %, em, rem, vh, vw, custom | `{"unit":"px","size":"","sizes":[]}` |
| `height` | select |  | no | `default` `full` `min-height` | `"default"` |
| `custom_height` | slider |  | yes | units: px, em, rem, vh, vw, custom | `{"unit":"px","size":400,"sizes":[]}` |
| `height_inner` | select |  | no | `default` `full` `min-height` | `"default"` |
| `custom_height_inner` | slider |  | yes | units: px, em, rem, vh, vw, custom | `{"unit":"px","size":400,"sizes":[]}` |
| `column_position` | select |  | no | `stretch` `top` `middle` `bottom` | `"middle"` |
| `content_position` | select |  | no | `` `top` `middle` `bottom` `space-between` `space-around` `space-evenly` | `""` |
| `overflow` | select |  | no | `` `hidden` | `""` |
| `stretch_section` | switcher |  | no | — | `""` |
| `html_tag` | select |  | no | `` `div` `header` `footer` `main` `article` `section` `aside` `nav` | `""` |

#### layout / section_structure

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `structure` | structure |  | no | — | `"10"` |

#### style / hfe_particles_promo

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `hfe_particles_promo_content` | raw_html |  | no | — | — |

#### style / section_background

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `background_background` | choose |  | no | `classic` `gradient` `video` `slideshow` | `""` |
| `background_gradient_notice` | alert |  | no | — | — |
| `background_color` | color |  | no | — | `""` |
| `background_color_stop` | slider |  | yes | units: %, custom | `{"unit":"%","size":0,"sizes":[]}` |
| `background_color_b` | color |  | no | — | `"#f2295b"` |
| `background_color_b_stop` | slider |  | yes | units: %, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `background_gradient_type` | select |  | no | `linear` `radial` | `"linear"` |
| `background_gradient_angle` | slider |  | yes | units: deg, grad, rad, turn, custom | `{"unit":"deg","size":180,"sizes":[]}` |
| `background_gradient_position` | select |  | yes | `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` | `"center center"` |
| `background_image` | media |  | yes | — | `{"url":"","id":"","size":""}` |
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
| `handle_slideshow_asset_loading` | hidden |  | no | — | `""` |
| `background_hover_background` | choose |  | no | `classic` `gradient` | `""` |
| `background_hover_gradient_notice` | alert |  | no | — | — |
| `background_hover_color` | color |  | no | — | `""` |
| `background_hover_color_stop` | slider |  | yes | units: %, custom | `{"unit":"%","size":0,"sizes":[]}` |
| `background_hover_color_b` | color |  | no | — | `"#f2295b"` |
| `background_hover_color_b_stop` | slider |  | yes | units: %, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `background_hover_gradient_type` | select |  | no | `linear` `radial` | `"linear"` |
| `background_hover_gradient_angle` | slider |  | yes | units: deg, grad, rad, turn, custom | `{"unit":"deg","size":180,"sizes":[]}` |
| `background_hover_gradient_position` | select |  | yes | `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` | `"center center"` |
| `background_hover_image` | media |  | yes | — | `{"url":"","id":"","size":""}` |
| `background_hover_position` | select |  | yes | `` `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` `initial` | `""` |
| `background_hover_xpos` | slider |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"px","size":0,"sizes":[]}` |
| `background_hover_ypos` | slider |  | yes | units: px, %, em, rem, vh, custom | `{"unit":"px","size":0,"sizes":[]}` |
| `background_hover_attachment` | select |  | no | `` `scroll` `fixed` | `""` |
| `background_hover_attachment_alert` | raw_html |  | no | — | — |
| `background_hover_repeat` | select |  | yes | `` `no-repeat` `repeat` `repeat-x` `repeat-y` | `""` |
| `background_hover_size` | select |  | yes | `` `auto` `cover` `contain` `initial` | `""` |
| `background_hover_bg_width` | slider |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `background_hover_video_link` | text |  | no | — | `""` |
| `background_hover_video_start` | number |  | no | — | `""` |
| `background_hover_video_end` | number |  | no | — | `""` |
| `background_hover_play_once` | switcher |  | no | — | `""` |
| `background_hover_play_on_mobile` | switcher |  | no | — | `""` |
| `background_hover_privacy_mode` | switcher |  | no | — | `""` |
| `background_hover_video_fallback` | media |  | no | — | `{"url":"","id":"","size":""}` |
| `background_hover_slideshow_gallery` | gallery |  | no | — | — |
| `background_hover_slideshow_loop` | switcher |  | no | — | `"yes"` |
| `background_hover_slideshow_slide_duration` | number |  | no | — | `5000` |
| `background_hover_slideshow_slide_transition` | select |  | no | `fade` `slide_right` `slide_left` `slide_up` `slide_down` | `"fade"` |
| `background_hover_slideshow_transition_duration` | number |  | no | — | `500` |
| `background_hover_slideshow_background_size` | select |  | yes | `` `auto` `cover` `contain` | `""` |
| `background_hover_slideshow_background_position` | select |  | yes | `` `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` | `""` |
| `background_hover_slideshow_lazyload` | switcher |  | no | — | `""` |
| `background_hover_slideshow_ken_burns` | switcher |  | no | — | `""` |
| `background_hover_slideshow_ken_burns_zoom_direction` | select |  | no | `in` `out` | `"in"` |
| `background_hover_transition` | slider |  | no | — | `{"unit":"px","size":0.3,"sizes":[]}` |
| `background_motion_fx_motion_fx_scrolling` | switcher |  | no | — | `""` |
| `background_motion_fx_translateY_effect` | popover_toggle |  | no | — | `""` |
| `background_motion_fx_translateY_direction` | select |  | no | `` `negative` | `""` |
| `background_motion_fx_translateY_speed` | slider |  | no | — | `{"unit":"px","size":4,"sizes":[]}` |
| `background_motion_fx_translateY_affectedRange` | slider |  | no | — | `{"unit":"%","size":"","sizes":{"start":0,"end":100}}` |
| `background_motion_fx_translateX_effect` | popover_toggle |  | no | — | `""` |
| `background_motion_fx_translateX_direction` | select |  | no | `` `negative` | `""` |
| `background_motion_fx_translateX_speed` | slider |  | no | — | `{"unit":"px","size":4,"sizes":[]}` |
| `background_motion_fx_translateX_affectedRange` | slider |  | no | — | `{"unit":"%","size":"","sizes":{"start":0,"end":100}}` |
| `background_motion_fx_opacity_effect` | popover_toggle |  | no | — | `""` |
| `background_motion_fx_opacity_direction` | select |  | no | `out-in` `in-out` `in-out-in` `out-in-out` | `"out-in"` |
| `background_motion_fx_opacity_level` | slider |  | no | — | `{"unit":"px","size":10,"sizes":[]}` |
| `background_motion_fx_opacity_range` | slider |  | no | — | `{"unit":"%","size":"","sizes":{"start":20,"end":80}}` |
| `background_motion_fx_blur_effect` | popover_toggle |  | no | — | `""` |
| `background_motion_fx_blur_direction` | select |  | no | `out-in` `in-out` `in-out-in` `out-in-out` | `"out-in"` |
| `background_motion_fx_blur_level` | slider |  | no | — | `{"unit":"px","size":7,"sizes":[]}` |
| `background_motion_fx_blur_range` | slider |  | no | — | `{"unit":"%","size":"","sizes":{"start":20,"end":80}}` |
| `background_motion_fx_rotateZ_direction` | select |  | no | `` `negative` | `""` |
| `background_motion_fx_rotateZ_speed` | slider |  | no | — | `{"unit":"px","size":1,"sizes":[]}` |
| `background_motion_fx_rotateZ_affectedRange` | slider |  | no | — | `{"unit":"%","size":"","sizes":{"start":0,"end":100}}` |
| `background_motion_fx_scale_effect` | popover_toggle |  | no | — | `""` |
| `background_motion_fx_scale_direction` | select |  | no | `out-in` `in-out` `in-out-in` `out-in-out` | `"out-in"` |
| `background_motion_fx_scale_speed` | slider |  | no | — | `{"unit":"px","size":4,"sizes":[]}` |
| `background_motion_fx_scale_range` | slider |  | no | — | `{"unit":"%","size":"","sizes":{"start":20,"end":80}}` |
| `background_motion_fx_devices` | select2 |  | no | `desktop` `tablet` `mobile` | `["desktop","tablet","mobile"]` |
| `background_motion_fx_range` | select |  | no | `` `viewport` `page` | `""` |
| `background_motion_fx_motion_fx_mouse` | switcher |  | no | — | `""` |
| `background_motion_fx_mouseTrack_effect` | popover_toggle |  | no | — | `""` |
| `background_motion_fx_mouseTrack_direction` | select |  | no | `` `negative` | `""` |
| `background_motion_fx_mouseTrack_speed` | slider |  | no | — | `{"unit":"px","size":1,"sizes":[]}` |
| `background_motion_fx_tilt_direction` | select |  | no | `` `negative` | `""` |
| `background_motion_fx_tilt_speed` | slider |  | no | — | `{"unit":"px","size":4,"sizes":[]}` |
| `background_handle_motion_fx_asset_loading` | hidden |  | no | — | `""` |

#### style / section_background_overlay

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `background_overlay_background` | choose |  | no | `classic` `gradient` | `""` |
| `background_overlay_gradient_notice` | alert |  | no | — | — |
| `background_overlay_color` | color |  | no | — | `""` |
| `background_overlay_color_stop` | slider |  | yes | units: %, custom | `{"unit":"%","size":0,"sizes":[]}` |
| `background_overlay_color_b` | color |  | no | — | `"#f2295b"` |
| `background_overlay_color_b_stop` | slider |  | yes | units: %, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `background_overlay_gradient_type` | select |  | no | `linear` `radial` | `"linear"` |
| `background_overlay_gradient_angle` | slider |  | yes | units: deg, grad, rad, turn, custom | `{"unit":"deg","size":180,"sizes":[]}` |
| `background_overlay_gradient_position` | select |  | yes | `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` | `"center center"` |
| `background_overlay_image` | media |  | yes | — | `{"url":"","id":"","size":""}` |
| `background_overlay_position` | select |  | yes | `` `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` `initial` | `""` |
| `background_overlay_xpos` | slider |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"px","size":0,"sizes":[]}` |
| `background_overlay_ypos` | slider |  | yes | units: px, %, em, rem, vh, custom | `{"unit":"px","size":0,"sizes":[]}` |
| `background_overlay_attachment` | select |  | no | `` `scroll` `fixed` | `""` |
| `background_overlay_attachment_alert` | raw_html |  | no | — | — |
| `background_overlay_repeat` | select |  | yes | `` `no-repeat` `repeat` `repeat-x` `repeat-y` | `""` |
| `background_overlay_size` | select |  | yes | `` `auto` `cover` `contain` `initial` | `""` |
| `background_overlay_bg_width` | slider |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `background_overlay_video_link` | text |  | no | — | `""` |
| `background_overlay_video_start` | number |  | no | — | `""` |
| `background_overlay_video_end` | number |  | no | — | `""` |
| `background_overlay_play_once` | switcher |  | no | — | `""` |
| `background_overlay_play_on_mobile` | switcher |  | no | — | `""` |
| `background_overlay_privacy_mode` | switcher |  | no | — | `""` |
| `background_overlay_video_fallback` | media |  | no | — | `{"url":"","id":"","size":""}` |
| `background_overlay_slideshow_gallery` | gallery |  | no | — | — |
| `background_overlay_slideshow_loop` | switcher |  | no | — | `"yes"` |
| `background_overlay_slideshow_slide_duration` | number |  | no | — | `5000` |
| `background_overlay_slideshow_slide_transition` | select |  | no | `fade` `slide_right` `slide_left` `slide_up` `slide_down` | `"fade"` |
| `background_overlay_slideshow_transition_duration` | number |  | no | — | `500` |
| `background_overlay_slideshow_background_size` | select |  | yes | `` `auto` `cover` `contain` | `""` |
| `background_overlay_slideshow_background_position` | select |  | yes | `` `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` | `""` |
| `background_overlay_slideshow_lazyload` | switcher |  | no | — | `""` |
| `background_overlay_slideshow_ken_burns` | switcher |  | no | — | `""` |
| `background_overlay_slideshow_ken_burns_zoom_direction` | select |  | no | `in` `out` | `"in"` |
| `background_overlay_opacity` | slider |  | yes | — | `{"unit":"px","size":0.5,"sizes":[]}` |
| `css_filters_css_filter` | popover_toggle |  | no | — | `""` |
| `css_filters_blur` | slider |  | no | — | `{"unit":"px","size":0,"sizes":[]}` |
| `css_filters_brightness` | slider |  | no | — | `{"unit":"px","size":100,"sizes":[]}` |
| `css_filters_contrast` | slider |  | no | — | `{"unit":"px","size":100,"sizes":[]}` |
| `css_filters_saturate` | slider |  | no | — | `{"unit":"px","size":100,"sizes":[]}` |
| `css_filters_hue` | slider |  | no | — | `{"unit":"px","size":0,"sizes":[]}` |
| `overlay_blend_mode` | select |  | no | `` `multiply` `screen` `overlay` `darken` `lighten` `color-dodge` `saturation` `color` `luminosity` `difference` `exclusion` `hue` | `""` |
| `background_overlay_hover_background` | choose |  | no | `classic` `gradient` | `""` |
| `background_overlay_hover_gradient_notice` | alert |  | no | — | — |
| `background_overlay_hover_color` | color |  | no | — | `""` |
| `background_overlay_hover_color_stop` | slider |  | yes | units: %, custom | `{"unit":"%","size":0,"sizes":[]}` |
| `background_overlay_hover_color_b` | color |  | no | — | `"#f2295b"` |
| `background_overlay_hover_color_b_stop` | slider |  | yes | units: %, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `background_overlay_hover_gradient_type` | select |  | no | `linear` `radial` | `"linear"` |
| `background_overlay_hover_gradient_angle` | slider |  | yes | units: deg, grad, rad, turn, custom | `{"unit":"deg","size":180,"sizes":[]}` |
| `background_overlay_hover_gradient_position` | select |  | yes | `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` | `"center center"` |
| `background_overlay_hover_image` | media |  | yes | — | `{"url":"","id":"","size":""}` |
| `background_overlay_hover_position` | select |  | yes | `` `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` `initial` | `""` |
| `background_overlay_hover_xpos` | slider |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"px","size":0,"sizes":[]}` |
| `background_overlay_hover_ypos` | slider |  | yes | units: px, %, em, rem, vh, custom | `{"unit":"px","size":0,"sizes":[]}` |
| `background_overlay_hover_attachment` | select |  | no | `` `scroll` `fixed` | `""` |
| `background_overlay_hover_attachment_alert` | raw_html |  | no | — | — |
| `background_overlay_hover_repeat` | select |  | yes | `` `no-repeat` `repeat` `repeat-x` `repeat-y` | `""` |
| `background_overlay_hover_size` | select |  | yes | `` `auto` `cover` `contain` `initial` | `""` |
| `background_overlay_hover_bg_width` | slider |  | yes | units: px, %, em, rem, vw, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `background_overlay_hover_video_link` | text |  | no | — | `""` |
| `background_overlay_hover_video_start` | number |  | no | — | `""` |
| `background_overlay_hover_video_end` | number |  | no | — | `""` |
| `background_overlay_hover_play_once` | switcher |  | no | — | `""` |
| `background_overlay_hover_play_on_mobile` | switcher |  | no | — | `""` |
| `background_overlay_hover_privacy_mode` | switcher |  | no | — | `""` |
| `background_overlay_hover_video_fallback` | media |  | no | — | `{"url":"","id":"","size":""}` |
| `background_overlay_hover_slideshow_gallery` | gallery |  | no | — | — |
| `background_overlay_hover_slideshow_loop` | switcher |  | no | — | `"yes"` |
| `background_overlay_hover_slideshow_slide_duration` | number |  | no | — | `5000` |
| `background_overlay_hover_slideshow_slide_transition` | select |  | no | `fade` `slide_right` `slide_left` `slide_up` `slide_down` | `"fade"` |
| `background_overlay_hover_slideshow_transition_duration` | number |  | no | — | `500` |
| `background_overlay_hover_slideshow_background_size` | select |  | yes | `` `auto` `cover` `contain` | `""` |
| `background_overlay_hover_slideshow_background_position` | select |  | yes | `` `center center` `center left` `center right` `top center` `top left` `top right` `bottom center` `bottom left` `bottom right` | `""` |
| `background_overlay_hover_slideshow_lazyload` | switcher |  | no | — | `""` |
| `background_overlay_hover_slideshow_ken_burns` | switcher |  | no | — | `""` |
| `background_overlay_hover_slideshow_ken_burns_zoom_direction` | select |  | no | `in` `out` | `"in"` |
| `background_overlay_hover_opacity` | slider |  | yes | — | `{"unit":"px","size":0.5,"sizes":[]}` |
| `css_filters_hover_css_filter` | popover_toggle |  | no | — | `""` |
| `css_filters_hover_blur` | slider |  | no | — | `{"unit":"px","size":0,"sizes":[]}` |
| `css_filters_hover_brightness` | slider |  | no | — | `{"unit":"px","size":100,"sizes":[]}` |
| `css_filters_hover_contrast` | slider |  | no | — | `{"unit":"px","size":100,"sizes":[]}` |
| `css_filters_hover_saturate` | slider |  | no | — | `{"unit":"px","size":100,"sizes":[]}` |
| `css_filters_hover_hue` | slider |  | no | — | `{"unit":"px","size":0,"sizes":[]}` |
| `background_overlay_hover_transition` | slider |  | no | — | `{"unit":"px","size":0.3,"sizes":[]}` |

#### style / section_border

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `border_border` | select |  | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `border_width` | dimensions |  | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `border_color` | color |  | no | — | `""` |
| `border_radius` | dimensions |  | yes | units: px, %, em, rem, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `box_shadow_box_shadow_type` | popover_toggle |  | no | — | `""` |
| `box_shadow_box_shadow` | box_shadow |  | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `box_shadow_box_shadow_position` | select |  | no | ` ` `inset` | `" "` |
| `border_hover_border` | select |  | no | `` `none` `solid` `double` `dotted` `dashed` `groove` | `""` |
| `border_hover_width` | dimensions |  | yes | units: px, em, rem, vw, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `border_hover_color` | color |  | no | — | `""` |
| `border_radius_hover` | dimensions |  | yes | units: px, %, em, rem, custom | `{"unit":"px","top":"","right":"","bottom":"","left":"","isLinked":true}` |
| `box_shadow_hover_box_shadow_type` | popover_toggle |  | no | — | `""` |
| `box_shadow_hover_box_shadow` | box_shadow |  | no | — | `{"horizontal":0,"vertical":0,"blur":10,"spread":0,"color":"rgba(0,0,0,0.5)"}` |
| `box_shadow_hover_box_shadow_position` | select |  | no | ` ` `inset` | `" "` |
| `border_hover_transition` | slider |  | no | — | `{"unit":"px","size":0.3,"sizes":[]}` |

#### style / section_premium_global_divider

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `premium_global_divider_sw` | switcher |  | no | — | `""` |
| `premium_gdivider_source` | select |  | no | `default` `custom` | `"default"` |
| `premium_gdivider_defaults` | premium-image-choose |  | no | `shape1` `shape2` `shape3` `shape4` `shape5` `shape6` `shape7` `shape8` `shape9` `shape10` `shape11` `shape12` `shape13` `shape14` `shape15` `shape16` `shape17` `shape18` `shape19` `shape20` `shape21` `shape22` `shape23` `shape24` `shape25` `shape26` `shape27` `shape28` `shape29` `shape30` `shape31` `shape32` `shape33` `shape34` `shape35` `shape36` `shape37` `shape38` `shape39` `shape40` `shape41` `shape42` `shape43` `shape44` `shape45` `shape46` `shape47` `shape48` `shape49` `shape50` `shape51` | `"shape22"` |
| `premium_gdivider_pos` | choose |  | yes | `top` `bottom` `left` `right` | `"bottom"` |
| `pro_options_notice` | raw_html |  | no | — | — |
| `premium_gdivider_height` | slider |  | yes | — | `{"unit":"px","size":150,"sizes":[]}` |
| `premium_gdivider_width` | slider |  | yes | — | `{"unit":"px","size":100,"sizes":[]}` |
| `premium_gdivider_scale` | slider |  | yes | — | `{"unit":"px","size":4,"sizes":[]}` |
| `premium_gdivider_offset` | slider |  | yes | — | `{"unit":"px","size":"","sizes":[]}` |
| `premium_gdivider_animate` | switcher |  | no | — | `"yes"` |
| `premium_gdivider_no_stretch` | switcher |  | no | — | `"yes"` |
| `animation_notice` | raw_html |  | no | — | — |
| `premium_gdivider_anime_speed` | slider |  | yes | — | `{"unit":"px","size":10,"sizes":[]}` |
| `premium_gdivider_anime_dir` | select |  | no | `normal` `reverse` `alternate` | `"alternate"` |
| `premium_gdivider_flip` | switcher |  | no | — | `""` |
| `premium_gdivider_flip_x` | switcher |  | no | — | `""` |
| `premium_gdivider_hide` | select2 |  | no | `desktop` `tablet` `mobile` | — |
| `premium_gdivider_bg_type` | select |  | no | `color` `image` `gradient` | `"color"` |
| `premium_gdivider_fill` | color |  | no | — | `"#afafaf"` |
| `divider_fill_notice` | raw_html |  | no | — | — |
| `premium_gdivider_stroke_width` | slider |  | yes | — | `{"unit":"px","size":"","sizes":[]}` |
| `premium_gdivider_stroke` | color |  | no | — | `""` |
| `premium_gdivider_opacity` | slider |  | no | — | `{"unit":"px","size":0.3,"sizes":[]}` |
| `premium_gdivider_zindex` | number |  | no | — | `""` |

#### style / section_shape_divider

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `shape_divider_top` | visual_choice |  | no | `mountains` `drops` `clouds` `zigzag` `pyramids` `triangle` `triangle-asymmetrical` `tilt` `opacity-tilt` `opacity-fan` `curve` `curve-asymmetrical` `waves` `wave-brush` `waves-pattern` `book` `split` `arrow` | `""` |
| `shape_divider_top_color` | color |  | no | — | `""` |
| `shape_divider_top_width` | slider |  | yes | units: %, vw, custom | `{"unit":"%","size":"","sizes":[]}` |
| `shape_divider_top_height` | slider |  | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `shape_divider_top_flip` | switcher |  | no | — | `""` |
| `shape_divider_top_negative` | switcher |  | no | — | `""` |
| `shape_divider_top_above_content` | switcher |  | no | — | `""` |
| `shape_divider_bottom` | visual_choice |  | no | `mountains` `drops` `clouds` `zigzag` `pyramids` `triangle` `triangle-asymmetrical` `tilt` `opacity-tilt` `opacity-fan` `curve` `curve-asymmetrical` `waves` `wave-brush` `waves-pattern` `book` `split` `arrow` | `""` |
| `shape_divider_bottom_color` | color |  | no | — | `""` |
| `shape_divider_bottom_width` | slider |  | yes | units: %, vw, custom | `{"unit":"%","size":"","sizes":[]}` |
| `shape_divider_bottom_height` | slider |  | yes | units: px, em, rem, custom | `{"unit":"px","size":"","sizes":[]}` |
| `shape_divider_bottom_flip` | switcher |  | no | — | `""` |
| `shape_divider_bottom_negative` | switcher |  | no | — | `""` |
| `shape_divider_bottom_above_content` | switcher |  | no | — | `""` |

#### style / section_typo

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `heading_color` | color |  | no | — | `""` |
| `color_text` | color |  | no | — | `""` |
| `color_link` | color |  | no | — | `""` |
| `color_link_hover` | color |  | no | — | `""` |
| `text_align` | choose |  | yes | `start` `center` `end` `justify` | `""` |

