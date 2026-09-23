## CRECS property template

Editing the shared Elementor property template? Use the `crecs-property-template` skill in
`.agents/skills/`. Read its `references/widgets/<widget>.md` before touching a
control, and make changes through `scripts/crecs_template.py` rather than editing the
JSON by hand — it validates before writing and keeps element ids stable.

Key rules the skill enforces: `crecs_property_data` must be the first widget;
`<control>_tablet`/`_mobile` only exist on controls the reference marks responsive;
control names differ per widget; `crecs_property_fields_and_data` does not exist.
