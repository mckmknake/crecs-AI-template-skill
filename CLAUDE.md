# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

The **CRECS property template skill**: an AI skill that edits the shared Elementor
property-page template of a CRE Cloud Solutions WordPress site and exports importable
Elementor JSON. Python 3.9+, standard library only — no network, no WordPress, no PHP.

It was extracted from the `crecs-wp-plugin` repository on 2026-09-23, and since
2026-09-25 **this repository is the only copy**. The plugin repository no longer holds the
skill, its packages or its packaging tools.

## Layout

```
crecs-property-template/   the skill — SKILL.md, references/, assets/, scripts/
dist/                      six packaged surfaces, GENERATED — never edit by hand
tools/                     packaging, delivery ZIPs, fixtures, package verification
docs/                      scope, compatibility sources, the acceptance script
```

**Nothing but the skill goes inside `crecs-property-template/`.** `build-skill-packages.js`
copies that folder whole into every package, so a stray file there ships to every client.

## Where this repository meets the plugin

Exactly two places, both taking a path as an argument. Nothing is copied by hand.

| Direction | What | Run from |
| --- | --- | --- |
| plugin → skill | `build-references.js` and `build-base-template.js` write `crecs-property-template/references/` and `assets/` | the plugin repository — they need its catalog, which needs WordPress and Elementor |
| skill → plugin | `build-preview-index.js --skill <this repo>/crecs-property-template` regenerates the plugin's `includes/preview/data/crecs-preview-index.json` | the plugin repository |

Consequences:

- **The catalog cannot be regenerated here.** `references/catalog/` comes from PHP extractors
  in the plugin repository. Do not hand-edit it.
- **A change to `references/` needs a plugin release too**, because the plugin's preview
  index is derived from it. The two record the same `catalog_sha256`; the plugin's preview
  suite case XR-01 compares them when `CRECS_SKILL_ROOT` points here.
- The contract number `CONTRACT` in `scripts/crecs_preview.py` must match `'contract'` in the
  plugin's `includes/preview/class-crecs-preview-rest.php`.

The full regeneration sequence is in the plugin repository's
`tools/crecs-template-studio/README.md`, under *Regenerating after an Elementor or plugin
change*.

## Commands

```bash
python crecs-property-template/scripts/crecs_template.py selftest
python crecs-property-template/scripts/tests/run_tests.py
node tools/build-negative-fixtures.js crecs-property-template
node tools/build-skill-packages.js crecs-property-template dist
node tools/verify-package.js dist/claude-code-skill
node tools/build-release-zips.js --out release
node tools/tests/build-release-zips.test.js
```

After **any** change under `crecs-property-template/`, rebuild `dist/` before committing —
`build-release-zips.js` refuses to package a `dist/` that has drifted from the source.

## Which ZIP for which client

| Client uses | Send | Why that one |
| --- | --- | --- |
| claude.ai, in the browser | `…-claude-web.zip` | uploaded as-is: one top-level folder, `SKILL.md` inside. Its install notes travel beside it |
| Claude Code | `…-claude-code-skill.zip` | unpacked, folder copied to `~/.claude/skills/` |
| Claude Code, inside one project | `…-claude-code-plugin.zip` | a plugin layout |
| Codex | `…-codex-skill.zip` | `.agents/skills/` |
| ChatGPT | `…-chatgpt-skill.zip` | same layout plus `agents/openai.yaml` |
| ChatGPT, no install | `…-chatgpt-file-kit.zip` | loose files and an opening instruction |

Uploading any archive but `claude-web` to claude.ai fails with *"All files must be inside
the top-level folder"* — they carry `INSTALL.md` and `MANIFEST.sha256` beside the skill.

## Hard rules

- **Test first, and prove the test can fail.** A test asserting that a finding code is
  absent passes forever if the code does not exist. `tests/test_base_template.py` was once
  entirely vacuous for exactly that reason. Break a copy, require the finding to appear,
  then require the shipped artefact to be free of it.
- **The skill never guesses a control name** and never invents one. That is the whole point
  of the catalog; a relaxation there is a product change, not a fix.
- **No secrets, ever** — no API token, no client credential, no session token. Target
  profiles hold site ids and hosts only.
- **Plain language to the person, precision in the record.** Ids, control names and
  `__dynamic__` never go in front of a client; they belong in `decisions.md` and reports.
- Repository artefacts — code, comments, docs, commit messages — are **in English**.
  Conversation with the user is in Portuguese.
- Do not commit unless asked. Line endings are LF in the repository (`.gitattributes`); the
  "LF will be replaced by CRLF" warnings on Windows are expected.

## Known open items

- `assets/property-template-all-widgets.json` is derived from a reference
  `PropertyPage.json` that is in **no** repository. It cannot be rebuilt from a clean
  checkout, here or in the plugin repository.
- A client only learns their skill is stale when an edit fails to appear. The staleness
  check — comparing the site's `catalog_sha256` through an authenticated preview session —
  is designed and not built; see the plugin repository's `STATE.md`.
- `crecs_preview.py` talks to the plugin's preview module, which lives in the plugin
  repository with its own design notes and test plan.
