# CRECS Template Studio — approved scope and decisions

## What this project is

A portable knowledge core that lets an AI assistant **redesign the shared Elementor
property-page template** for a CRECS site, correctly, without touching property data.

The AI changes the **design**. The existing widgets and dynamic tags keep fetching
property data from the CRE Cloud Solutions API exactly as they do today.

## Approved scope

1. **One shared template per site.** Every property slug on a site renders through a
   single Elementor template. That stays. The project does not introduce per-property
   or per-property-type templates.
2. **Data binding is unchanged.** `crecs_property_data` resolves the property;
   the other `crecs_property_*` widgets and the `crecs-property` dynamic tag read it.
   No new endpoints, no new data layer, no change to how properties are fetched.
3. **Four target surfaces, one knowledge core.** ChatGPT, Codex, Claude and Claude Code.
   Installation differs per surface; the knowledge itself is written once.

## Deliveries

| # | Delivery | Status |
| --- | --- | --- |
| 1 | Audit and verifiable catalog | **this delivery** |
| 2 | Portable skill, complete knowledge base, validation | not started |
| 3 | Import and real-world testing | not started |
| 4 | Elementor preview in a separate window with auto-refresh | not started |

## Out of scope

Flyers, e-mail campaigns, a bespoke chat UI, and per-property or per-type templates.

The supplied `AI-Property-Content-Studio-Developer-Narrative.md` proposes a much
broader product: three content surfaces (website page, flyer, e-mail), a Liquid
templating layer, a template library with per-type defaults, a customer theme
entity, a server-side Claude brokering service, and voice input. **The scope above
supersedes that narrative for this project.** The narrative is preserved as supplied
and its divergences from the approved scope are recorded in
`audit/05-DIVERGENCES.md` rather than quietly reconciled.

The same applies to `CRECloudSolutions-JSON-Data-Interface-Developer-Brief.md`,
which specifies a read-only JSON API on the SaaS side. That is a backend project on
the CRE Cloud Solutions app, not on this WordPress plugin, and delivery 2 does not
depend on it.

## Decisions taken during delivery 1

| Decision | Reason |
| --- | --- |
| The **code and observed behaviour** define the technical contract; the handoff documents are references, not proof of implementation. | Stated requirement, and borne out — the documents guessed several field keys wrongly (see `audit/05-DIVERGENCES.md`). |
| Widget relevance is judged by **what the widget binds to**, not by its name prefix. | Two relevant widgets do not follow the `crecs_property_*` pattern conceptually (`crecs_dynamic_field_data`), and two irrelevant ones use a hyphenated name (`crecs-image-carousel`, `crecs-quick-search`). |
| Control catalogues are built from a **runtime dump merged with a static dump**, never from one alone. | Declaration and effective registration are different things, and Elementor silently reshapes the stack depending on request context. |
| Provenance of "CRECS declared this control" is **measured**, not guessed from prefixes. | `crecs_property_meta_tags` declares zero controls, so its stack is the injected baseline; subtracting it is exact. |
| Device variants (`_tablet`, `_mobile`) are derived from the `is_responsive` flag on each control plus the site's active breakpoints. | Elementor 4.2.1 with responsive duplication mode `off` registers one control and lets the editor JS create device copies. Inventing variants would produce dead settings. |
| The `crecs-property` `param_name` list is recorded as a **dynamic universe with a filter rule**, not a fixed enum. | The dropdown is rebuilt per editor load from the property held in the PHP session, and only non-empty scalar values survive. |
| The extraction tools live in `tools/`, are stand-alone, and are never loaded by the plugin. | Required isolation; the plugin has no autoloader, so an untouched `require_once` list guarantees it. |
| No plugin runtime file was modified in delivery 1. | Required, and verified by `git status` / `git diff` — see `audit/07-VERIFICATION.md`. |

## Non-negotiables carried from `CLAUDE.md`

- Never echo, log or commit `crecs_api_token`, `crecs_google_apikey`,
  `crecs_recaptcha_secretkey` or a CA user's `auth_token`. The option report produced
  during this audit redacts them and records only their length.
- The search slug is configurable (`crecs_search_slug`); never hardcode `properties`.
- Do not touch `jetrouter/`, `includes/class-gamajo-template-loader.php`, the
  third-party `js/` and `css/` libraries, or anything named `*-old.*`, `*-bak.*`,
  `old_*`.
- Do not remove the second, object-oriented virtual-page system
  (`includes/crecs-page.php`, `crecs-controller.php`, `crecs-template-loader2.php`,
  `crecs-virtual-page.php`). It is under investigation.
- Match surrounding code style rather than modernising old files.
