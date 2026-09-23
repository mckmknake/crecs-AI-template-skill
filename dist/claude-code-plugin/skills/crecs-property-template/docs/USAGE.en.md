# Usage — worked examples

Every example uses `S=scripts/crecs_template.py` and a workspace at `./work`. Add
`--json` to any command for machine-readable output, and `--help` to any command for
its options.

## 0. Set up

```bash
S=scripts/crecs_template.py

# Copy the profile and fill in the client's values.
cp assets/target-profile.example.json ./acme-profile.json
# edit: site_host, preview_slug, popups

python3 $S init \
    --from assets/property-template-all-widgets.json \
    --workdir ./work \
    --profile ./acme-profile.json
```

Starting from the client's own export instead:

```bash
python3 $S init --from ./their-current-export.json --workdir ./work --profile ./acme-profile.json
```

Confirm the package is intact before you trust anything it says:

```bash
python3 $S selftest
```

## 1. Change one colour

> "Make the property-fields card white."

```bash
python3 $S inspect --workdir ./work --widgets
# ...  b133d6f  crecs_property_fields  #3:section/...

python3 $S set --workdir ./work --element b133d6f \
    --key card_color --value "#FFFFFF" \
    --decision "Acme asked for white field cards."

python3 $S diff --workdir ./work
```

The diff shows one line. Nothing else moved.

## 2. Reorder blocks

> "Put the details card above the media box."

```bash
python3 $S move --workdir ./work --element 39f1774c --before 61b0cce6
```

Element ids survive a move, so bindings and styling follow. `move` refuses anything
that would put a widget before the loader.

## 3. Mobile only

> "Tighter card padding on phones, leave desktop alone."

```bash
python3 $S set --workdir ./work --element b133d6f \
    --key card_padding --device mobile \
    --value '{"unit":"px","top":"6","right":"6","bottom":"6","left":"6","isLinked":true}'
```

Only `card_padding_mobile` is written. Try the same with `card_color` and it is
refused — that control is not responsive, so Elementor would never read the variant:

```
'card_color' on crecs_property_fields is not a responsive control (is_responsive is
false), so Elementor never reads a mobile variant of it.
```

## 4. Typography and hover

> "Suite attachment links bolder, different hover colour, smaller on tablet."

```bash
python3 $S set --workdir ./work --element 39f1774c --key attachment_link_typography_typography --value custom
python3 $S set --workdir ./work --element 39f1774c --key attachment_link_typography_font_weight --value 700
python3 $S set --workdir ./work --element 39f1774c --key attachment_link_text_color_hover --value "#3B82F6"
python3 $S set --workdir ./work --element 39f1774c \
    --key attachment_link_typography_font_size --device tablet \
    --value '{"unit":"px","size":13,"sizes":[]}'
```

`--value 700` is stored as the string `"700"`, because that is what the control's
option list holds — the command says so when it does that.

Watch out: `attachment_link_*` exists on `crecs_property_suites` and **not** on
`crecs_property_attachments`, where the link is styled through `card_body_*`. The tool
refuses and names the right control.

## 5. Add a widget

```bash
python3 $S inspect --workdir ./work --tree --json | head -40   # find a column id
python3 $S add-widget --workdir ./work --widget crecs_property_rates --into 6f64db7d \
    --settings '{"property_rate":"both","rate_style":"inline-block"}'
```

A second `crecs_property_map` is refused, with the reason:

```
crecs_property_map already appears 1 time(s) and at most 1 can work on one page.
Declares the global JS function crecs_map_widget_plot_pov without an instance suffix
and a textarea with the fixed id property_geodata.
```

## 6. Remove a block

```bash
python3 $S remove --workdir ./work --element 552329d1 \
    --reason "Acme never fills in demographics."
```

`--reason` is mandatory and lands in `decisions.md`. Removing the loader needs
`--force` and tells you what breaks first. A property that simply has no data for a
block is not a reason to remove it from the template every property shares — the
widget renders nothing when empty.

## 7. Bind a property field

```bash
python3 $S catalog --params | grep -i size
python3 $S bind --workdir ./work --element 31338650 --control title --param property_name
python3 $S unbind --workdir ./work --element 31338650 --control title
```

The wrong casing is caught:

```
'size-available_sf' is not a param_name that
Crecs_Functions::crecs_parse_property_data() produces. The real key is
'size-available_SF' — keys are compared exactly, including case.
```

## 7b. Retarget the contact popups

The shipped template binds its two contact buttons to the reference site's Elementor
Pro popups, 4554 and 4646. Those ids mean nothing on anyone else's site, so `validate`
refuses the export until they are retargeted. The example profile ships placeholder
popup ids for the same reason: a numeric id in there would look like an assertion that
the popup exists.

```bash
python3 $S popup --workdir ./work --list
```

```
ELEMENT    TYPE                     CONTROL    POPUP    DECLARED
2121e6fe   button                   link       4554     NO
55f63989   button                   link       4646     NO

2 binding(s) point at a popup this profile does not declare.
Retarget each one, with the id of a popup on the client's site:
  popup --element 2121e6fe --control link --set <id> --decision ...
```

Add the client's real ids to the profile's `popups` map, then:

```bash
python3 $S popup --workdir ./work --element 2121e6fe --control link \
    --set 4581 --decision "Acme's own advisor popup."
```

An id the profile does not declare is refused, and so is a non-numeric one. If the
client has no equivalent popup, `--clear` removes the binding; leaving it pointed at a
stranger's id is the one thing not on offer.

## 8. Validate

```bash
python3 $S validate --workdir ./work
python3 $S validate --workdir ./work --level error     # only what blocks an export
python3 $S validate --workdir ./work --json | python3 -m json.tool | head -40
```

Exit code is `0` with no errors and `2` when errors remain.

## 9. Undo, history, resume

```bash
python3 $S history --workdir ./work
python3 $S undo --workdir ./work
python3 $S undo --workdir ./work --steps 3
```

`history` prints everything a later session needs: revision, document hash, profile,
catalog version and every recorded decision. Undo is itself a revision.

If someone edits `work/document.json` in another tool, the next command refuses rather
than overwriting it:

```
document.json changed outside this tool since revision 4, so committing would discard
that edit. Re-run with --accept-external to take the file as it is now.
```

## 10. Export

```bash
python3 $S export --workdir ./work --out ./acme-property-page.json
```

Two files appear: the Elementor JSON, and `acme-property-page.json.report.json` with
the counts, the profile mappings applied, and the claim level. A blocked export writes
nothing and names every blocking finding. `--allow-draft` saves an incomplete draft,
labelled as one.

Then, in WordPress: **Templates → Saved Templates → Import**, and point the CRECS
setting `crecs_custom_property_page_template_shortcode` at the imported template id.
One template serves every property, so this is done once, not per property.

### Without a project directory

Nothing above needs a folder of your own. Leave `--workdir` out and the workspace goes
to a fixed directory under the system temp, which every command prints; `$CRECS_WORKDIR`
moves it. Ask for `--out -` and the Elementor JSON goes to stdout instead of a file:

```bash
python3 $S init --from assets/property-template-all-widgets.json --profile ./acme.json
python3 $S set --element 39f1774c --key card_header_color --value "#FFFFFF"
python3 $S export --out - > acme-property-page.json
```

Stdout carries the JSON and nothing else — the summary and any refusal go to stderr —
so it redirects cleanly or gets attached to a reply. No `.report.json` is written in
that mode, because there is no path to put one beside; run `validate` for the findings.

**Nothing in this package has been imported or rendered.** A passing export means the
JSON is structurally valid and consistent with the installed plugin's controls. Whether
it looks right is a question only the browser answers.

## 11. Explore the catalog

```bash
python3 $S catalog --list-widgets
python3 $S catalog --widget crecs_property_suites --controls
python3 $S catalog --widget crecs_property_suites --controls --section card_body_section
python3 $S catalog --params
python3 $S coverage
```

Or read `references/widgets/<widget>.md`, which is the same information laid out for
a person.

## 12. Run the tests

```bash
python3 scripts/tests/run_tests.py              # everything, plus a coverage report
python3 scripts/tests/run_tests.py --unit       # fast
python3 scripts/tests/run_tests.py --conversational
python3 scripts/tests/run_tests.py --json
```

Offline, standard library only.
