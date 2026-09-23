# `crecs_property_data` — CRECS: Load Property Data

Generated from the delivery-1 catalog. Source file: `includes/widgets/class-elementor-crecs-property-data-widget.php`.

| | |
| --- | --- |
| Relevance | **required** |
| Why | Resolves the property and publishes it into $_SESSION["property"]; every other property widget and the crecs-property tag read it from there. Must be the first element on the page. |
| Elementor categories | `cre-cloud-solutions-property-data` |
| Controls contributed by CRECS | 1 |
| Max instances per page | 1 |
| Position | **must be the first widget in document order** |

> **Cardinality.** render() assigns $_SESSION['property']; a second instance only overwrites it, and every other property widget reads that key in its own render(), so the loader must be the first element in document order.
>
> Evidence: `includes/widgets/class-elementor-crecs-property-data-widget.php:156`

## Controls

#### content / content_section

| key | type | value shape | responsive | allowed values | default |
| --- | --- | --- | --- | --- | --- |
| `slug` | text | string | no | — | `""` |

