# Delivery 2 — implementation plan

Scope: a reusable package that lets an assistant create and edit, by conversation,
the **single shared** Elementor property template for a CRECS site, and export it as
Elementor JSON. No preview, no publishing, no new endpoints, no per-property
templates, no flyers, no e-mail, no chat UI.

Built on delivery 1. Prerequisite re-checked before starting: revision
`b3844c40bc4131c6a30db402a378a151348d6b40`, catalog `verify-catalog.js` **10/10 PASS**,
so no regeneration was needed.

## Method

Tests before code, per unit. Each unit below has an acceptance check that can be run
independently, and the whole suite runs offline.

## Environment facts that shaped the plan

| Fact | Consequence |
| --- | --- |
| No real Python on the Windows host (only the Microsoft Store stub); Python 3.10.12 exists in WSL Ubuntu | Client scripts target **Python 3.9+, standard library only**, and are tested under WSL. Node stays for the dev-only build tools inherited from delivery 1. |
| `crecs_property_map` emits an **unsuffixed** global JS function `crecs_map_widget_plot_pov` and a fixed `id="property_geodata"` (`class-elementor-crecs-property-map-widget.php:237,247`) | cardinality **max 1** |
| `crecs_property_docs` binds fixed DOM ids: `crecs_ca_docs_modal`, `ca_docs_title`, `crecs_sign_in_new_user`, `crecs_sign_in_user_email`, `property_slug`, `modalMessage`, `formReturnMessage` (`:1244-1319,1383-1426`) | cardinality **max 1** |
| `crecs_property_team_members` renders a fixed `id="contacts"` (`:986`) | cardinality **max 1** |
| `crecs_property_data` writes `$_SESSION['property']`; a second instance would just overwrite it | cardinality **max 1**, and must be the first widget |
| `crecs_property_media`, `_photos`, `_suites`, `_attachments`, `_traffic`, `_demographic`, `_details`, `_fields`, `_rates`, `_sitemap_urls` suffix every DOM id with `$this->get_id()` | multi-instance safe; the reference template's two `crecs_property_suites` are legitimate |
| `crecs_property_docs.popup_template` options come from a `WP_Query` over `elementor_library` popup posts (`get_popup_templates()`, `:1134-1143`) | **open vocabulary**, per site. The catalog snapshot is an example; the validator must not reject an unlisted id, and the value belongs to the target profile. |

## Units

### U1 — Generated references, hash-verified

Canonical catalog stays the delivery-1 artefact. Distributed copies are **generated**
and checked by hash, never hand-maintained.

- `tools/crecs-template-studio/build-references.js` derives, from the catalog:
  one Markdown reference per relevant widget, a dynamic-tag reference, and a reduced
  machine projection for the chat tier.
- Every generated file is listed in `MANIFEST.sha256`.
- **Accept:** regenerating twice produces identical bytes; `verify-package.js`
  recomputes every hash and fails on any mismatch.

### U2 — Base template with full coverage

`skills/crecs-property-template/assets/property-template-all-widgets.json`, derived
from the original `PropertyPage.json`.

- Keeps the visual identity, the classic section/column model, the element order and
  every existing binding.
- Adds the 4 missing relevant widgets — `crecs_property_rates`,
  `crecs_property_map`, `crecs_property_photos`, `crecs_property_meta_tags` — at
  positions that respect their nature: the meta-tags widget is non-visual and is not
  turned into a card; the loader stays first and is not restyled.
- Keeps the two intentional `crecs_property_suites` instances with their
  complementary `hide_*` visibility.
- Drops no example data into settings: no property name, price, description, image or
  broker is frozen, and no fake content is invented to fill an empty block.
- Cross-site resources become **unresolved target-profile mappings**, not copied ids.
- **Accept:** the validator reports full coverage of the 15 required/core/non-visual
  widgets, zero frozen-content findings, and the two expected unresolved-dependency
  ERRORs (loader slug, popup ids) which a profile clears.

### U3 — Complementary fixtures

`assets/fixtures/`. For anything that cannot sit in the single base template, a
separate fixture plus the reason.

- `crecs_dynamic_field_data` — classified `conditional` in delivery 1 and absent from
  the reference template; shipped as a fixture so the widget is still exercised.
- A max-1 demonstration fixture per cardinality-limited widget.
- **Accept:** every relevant widget appears in the base template or in a fixture, and
  the coverage report names which and why.

### U4 — Python CLI: inspect, edit, state, history, undo, diff, export

`skills/crecs-property-template/scripts/` — one entry point, small modules, `--help`
on every command, actionable errors.

- Edits apply to the **latest revision**, preserving existing element ids, unrelated
  properties, structure and bindings.
- State lives outside the chat and outside the importable JSON: working document,
  base revision + hashes, history, decision log.
- Atomic writes (`os.replace`) and a base-revision check that refuses to overwrite an
  external change.
- Working file and final export are separate files.
- **Accept:** the unit tests in U6 cover every command, including resume-in-another-session
  and undo-restores-previous-content.

### U5 — Validator

Tree and envelope against the supported export version, element ids, control
types/values/conditions, repeaters, responsiveness, dependencies and order, bindings
and their encoding, target resources, and the absence of secrets or frozen factual
content.

- Three severities: **ERROR** blocks a "ready" export, **WARNING** and **INFO** do not.
- A newly introduced control key with no confirmed contract is an ERROR. A
  **pre-existing** unknown key or widget is preserved and flagged as a WARNING — the
  distinction comes from a baseline recorded at import, not from guessing.
- Bindings are parsed structurally (attribute scan → URL-decode → JSON parse → shape
  check → `param_name` resolved against the field universe), never by a single regex.
- Empty / `0` / `null` / `""` / `[]` / `{}` are preserved as distinct values.
- Visual preferences are reported as INFO and never as technical restrictions.
- **Accept:** positive and negative tests per rule in U6.

### U6 — Test suites

- `scripts/tests/` — unit and integration tests, Python stdlib `unittest`, offline.
  Negative cases required by the brief: malformed JSON, duplicate ids, invented key,
  corrupted binding, frozen slug, invalid nesting, missing dependency, revision
  conflict, secret, and the documented regressions from delivery 1 (the 52 orphan
  keys, the `_tablet`/`_mobile` rule, the `crecs_property_fields_and_data` alias).
- `tests/conversational/` — the 12 scenarios from the brief as scripted command
  sequences with asserted outcomes, so "tested in the harness" means something.
- Per-widget and per-control-family exercise report, naming what was **not** exercised.
- **Accept:** suite green; coverage report emitted; a clean-session run against the
  distributed package (no private repo) reproduces it.

### U7 — Per-surface packages

`dist/crecs-template-studio/`, self-contained, no symlinks, no paths outside the
package, no secrets, no client data, no commercial fonts.

- Claude Code — skill directory, plus plugin packaging if the official format applies.
- Claude in the browser — importable skill zip, with the file-execution requirement stated.
- Codex — skill/package in the currently supported format.
- ChatGPT in the browser — eligible skill/plugin format, plus a **file kit** and an
  opening instruction for when native installation is unavailable.
- Formats checked against current official documentation; no invented manifest or path.
- No vendor-exclusive hook, variable or tool in the core; adapters stay isolated.
- Existing `AGENTS.md` / `CLAUDE.md` are not modified.
- **Accept:** `verify-package.js` passes per package: manifest hashes, no absolute
  paths, no symlinks, no secret patterns, references resolve inside the package.

### U8 — Documentation and status

Install/update guides per surface, usage examples in Portuguese and English,
and updates to `PATHS.md`, `STATE.md`, `COMPATIBILITY.md` with
PASS/FAIL/BLOCKED/NOT_RUN plus evidence.

Three claim levels kept strictly apart throughout:

1. **static validation passed** — the validator accepted the document;
2. **tested in the harness** — a command sequence ran and asserted an outcome;
3. **Elementor import not yet tested** — no template was imported into WordPress and
   nothing was rendered.

## Explicit non-goals for this delivery

Preview, publishing, remote connection, new property endpoints, per-property or
per-type templates, flyers, e-mails, a chat UI, and any functional fix to plugin
runtime code (which needs separate authorisation).

## Known blockers inherited from delivery 1

| # | Blocker | Effect on delivery 2 |
| --- | --- | --- |
| B1 | The Elementor property-template path is inactive on the dev site | Nothing in this delivery is rendered or imported. All template claims are static. |
| B3 | The CA-credential divergence is unconfirmed against the API | Out of scope here; still listed as a security item. |
