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

Then the template goes into WordPress, and the assistant does that part in the browser
(SKILL.md, *Deliver it*): it saves the file in the person's Downloads folder, opens
**Templates → Saved Templates → Import Templates**, the person picks the file and
presses **Import Now**, and, on their yes, the assistant puts the new template's number
in **CRE Cloud Solutions → Custom Property Page Template** (the
`crecs_custom_property_page_template_shortcode` setting). One template serves every
property, so this is done once, not per property.

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

## 13. The search page

The page that lists the properties — map, filters, cards; usually `/properties` — is not
an Elementor template: it has its own tool, `scripts/crecs_search.py`, and goes through
the same preview. In WordPress, **CRE Cloud Solutions → Template preview → Start search
page preview** shows the session file in a box (with `"kind": "search"`). The assistant
reads that box from the page and saves it itself; the person never copies anything:

```bash
python3 scripts/crecs_preview.py connect <<'EOF'
(the box's text, as the page shows it)
EOF
# connected to example.com: the search page preview. Session saved in ~/.crecs/preview-example.com-search.json
```

When the preview later says the session expired or the token changed, **New link** on
that session in the same screen shows a new box: `connect` it the same way.

> "Put the filters in a column on the left, with blue buttons, and make the map shorter
> on phones."

```bash
P=scripts/crecs_preview.py
B=scripts/crecs_search.py
F=./search.json
SESSION=~/.crecs/preview-example.com-search.json    # the session file connect saved

python3 $P current --out $F --session-file $SESSION    # what the preview shows now
python3 $B show --file $F                                     # the tree, with ids

# filters and results side by side, in a box; stacked on tablets and phones
python3 $B add-box --file $F --wrap 5e2a0005,5e2a000d --direction row --id side0001
python3 $B set --file $F --node side0001 --key direction --device tablet --value column
python3 $B set --file $F --node 5e2a0002 --key direction --value column    # the main area follows the layout
python3 $B set --file $F --node 5e2a0005 --key _width --value 300px
python3 $B set --file $F --node 5e2a000d --key _grow --value yes

# the property type button in blue, with a hover colour, and a new label
python3 $B set --file $F --node 5e2a0008 --key button_background_color --value "#0a3d62"
python3 $B set --file $F --node 5e2a0008 --key button_background_color --hover --value "#145a8d"
python3 $B text --file $F --node 5e2a0008 --slot button --value "Type of property"

# a shorter map on phones only
python3 $B set --file $F --node 5e2a0004 --key map_height --device mobile --value 240px

python3 $B validate --file $F
python3 $P apply --document $F --session-file $SESSION    # the preview reloads
```

What the page starts with, and which filters show:

> "Open the page on properties for lease, offer only Office, Retail and Industrial in the
> type list, and hide the rate filter on phones."

```bash
python3 $P options --session-file $SESSION    # the site's own type and broker names
python3 $B set --file $F --node 5e2a0007 --key start_for_lease --value yes
python3 $B set --file $F --node 5e2a0008 --key offer --value "Office, Retail, Industrial"
python3 $B hide --file $F --node 5e2a000a --device mobile
python3 $P apply --document $F --session-file $SESSION
```

A starting value is a default, not a lock: visitors see For Lease ticked and can untick
it, or press Clear, which clears every filter. While nothing is ticked, a cut-down list
searches only the names it offers. Take the names from `options`; one with a comma goes
as JSON: `--value '["Bryan King, CCIM"]'`.

The ids come from `show`. `controls --node <id>` lists every setting a block takes and
what it accepts; `references/search/SEARCH-LAYOUT.md` describes every block. A change the
plugin would refuse is not written, and the command says why — the sort, for one, cannot
go into the filters, because the Clear button would reset it.

None of this changes the site. A person publishes, with the **Publish** button in the
preview and then **Yes, publish** in the bar it shows (administrators only); a green bar
answers. That works in the Claude app's browser too: there is no browser pop-up and no
OK. Only a plugin older than 2.8.10 asks with the browser's own pop-up, which the Claude
app's browser never shows; on such a site, publish from another browser.
`crecs_preview.py published` tells the assistant whether the layout on display is live,
so it checks instead of assuming. The Template preview screen shows what is live and
puts any earlier layout back, or the original one.
