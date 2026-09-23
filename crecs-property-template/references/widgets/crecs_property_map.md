# `crecs_property_map` — CRECS: Property Map

Generated from the delivery-1 catalog. Source file: `includes/widgets/template_widgets/class-elementor-crecs-property-map-widget.php`.

| | |
| --- | --- |
| Relevance | **core** |
| Why | Standalone map for the current property. |
| Elementor categories | `cre-cloud-solutions-property-data` |
| Controls contributed by CRECS | 4 |
| Max instances per page | 1 |

> **Cardinality.** Declares the global JS function crecs_map_widget_plot_pov without an instance suffix and a textarea with the fixed id property_geodata. Two instances redeclare the function and duplicate the id.
>
> Evidence: `includes/widgets/template_widgets/class-elementor-crecs-property-map-widget.php:237,247`

## Controls

#### content / content_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `map_type` | select | string | no | `roadmap` `satellite` `hybrid` `terrain` | `"roadmap"` |
| `width` | slider | object { unit, size, sizes[] } | no | units: px, %, em, rem, custom | `{"unit":"%","size":100,"sizes":[]}` |
| `height` | slider | object { unit, size, sizes[] } | no | units: px, %, em, rem, custom | `{"unit":"px","size":300,"sizes":[]}` |
| `zoom_level` | number | number or numeric string | no | — | `15` |

