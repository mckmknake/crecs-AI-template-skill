# Fixtures

Small, valid documents for anything the single base template cannot carry, plus a
`negative/` folder of documents that are supposed to fail.

## Why these exist separately

`property-template-all-widgets.json` holds every **required**, **core** and
**non-visual** widget — all 15 of them. Two things do not belong in it:

### `dynamic-field-data.json` — the `conditional` widget

`crecs_dynamic_field_data` renders one named field and is classified `conditional` in
the delivery-1 audit: it can legitimately appear on a property page but is not part of
the reference template, so putting it in the shared base would add a block nobody
asked for. It lives here so the widget is still exercised by the test suite and by the
coverage report.

Its `collection` control is a fixed vocabulary (`property_address`, `property_name`,
`managed_property_address`, `managed_property_name`, `work_order_type`,
`work_order_category`, `work_order_priority`) — unlike the property-grid filters,
these are declared in code, not fetched from the API.

### `negative/` — documents that must be rejected

Each file breaks exactly one rule, so a failing validator is obvious:

| file | expected finding |
| --- | --- |
| `malformed.json` | not valid JSON at all |
| `duplicate-ids.json` | `E-ID-DUPLICATE` |
| `invented-key.json` | `E-CONTROL-UNKNOWN` |
| `corrupt-binding.json` | `E-BINDING-CORRUPT` |
| `frozen-slug.json` | `E-FROZEN-SLUG` |
| `invalid-nesting.json` | `E-NESTING` |
| `container-model.json` | `E-ELEMENT-MODEL` |
| `secret.json` | `E-SECRET` |
| `dead-device-variant.json` | `E-RESPONSIVE-UNSUPPORTED` |
| `two-maps.json` | `E-CARDINALITY` |
| `loader-not-first.json` | `E-LOADER-ORDER` |

`negative/` is deliberately outside the folder that `selftest` and the coverage report
scan, since those expect every document they find to parse.

## Widgets that cannot share a page

Four widgets are limited to one instance, and the reason is technical rather than
aesthetic:

| widget | why one only |
| --- | --- |
| `crecs_property_data` | writes `$_SESSION['property']`; a second instance only overwrites it |
| `crecs_property_map` | declares the global JS function `crecs_map_widget_plot_pov` with no instance suffix, plus a fixed `id="property_geodata"` |
| `crecs_property_docs` | renders fixed DOM ids (`crecs_ca_docs_modal`, `crecs_sign_in_new_user`, …) and binds jQuery handlers to them |
| `crecs_property_team_members` | renders a fixed `id="contacts"` wrapper |
| `crecs_property_meta_tags` | would emit duplicate `<title>` and Open Graph tags |

Everything else suffixes its DOM ids with the Elementor element id, so multiple
instances are safe. That is why the base template's **two** `crecs_property_suites`
are legitimate: one is hidden on mobile, the other on desktop and tablet.

## Overlapping, not conflicting

`crecs_property_media` is a tabbed box covering images, map, street view, video and
floor plans. `crecs_property_photos` and `crecs_property_map` are standalone versions
of two of those tabs. All three are in the base template because all three are
relevant and none of them breaks the others — they each scope their DOM ids by element
id. Most designs keep either the media box or the standalone pair; remove whichever
the client does not want, with `remove --reason "..."`, and the catalog still supports
adding it back later.
