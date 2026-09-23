# Updating

## When the client's plugin or Elementor version changes

The catalog is a snapshot. `references/catalog/crecs-controls.min.json` records under
`provenance` exactly what it was generated from:

```bash
python3 scripts/crecs_template.py selftest
```

prints the CRECS version, the Elementor version and the plugin revision. If the
client's site runs something else, control names, options and responsive flags may
differ — and the whole point of this package is that it never guesses. Regenerate
rather than patching the projection by hand.

Regeneration is a developer task and needs the plugin repository, PHP and a WordPress
install with Elementor. The sequence lives in
`tools/crecs-template-studio/README.md`; in short:

```bash
# 1. re-extract, on a disposable site running the client's versions
php  tools/crecs-template-studio/extract-static-controls.php  <plugin-dir> <out>
php  tools/crecs-template-studio/extract-runtime-controls.php <wp-load.php> <out> <host>
php  tools/crecs-template-studio/extract-core-controls.php    <wp-load.php> <out> <host>
php  tools/crecs-template-studio/extract-property-fields.php  <plugin-dir> <out>

# 2. rebuild the catalog and verify it
node tools/crecs-template-studio/build-catalog.js  <runtime> <static> <fields> <catalogDir>
node tools/crecs-template-studio/verify-catalog.js <catalog> <plugin-dir> 1

# 3. regenerate what the skill ships
node tools/crecs-template-studio/build-references.js <catalog> <core> <fields> <notes> <skillRoot> <runtime>
node tools/crecs-template-studio/build-base-template.js <PropertyPage.json> <catalog> <notes> <skillRoot> <projection>
node tools/crecs-template-studio/build-negative-fixtures.js <skillRoot>

# 4. re-test and repackage
python3 skills/crecs-property-template/scripts/tests/run_tests.py
node tools/crecs-template-studio/build-skill-packages.js <skillRoot> dist/crecs-template-studio
node tools/crecs-template-studio/verify-package.js dist/crecs-template-studio/*
```

`build-references.js` is deterministic: two runs produce identical bytes, so a real
change in the catalog is visible in the diff and a rerun is not.

## When a control name looks wrong

Do not edit `references/`. Every file there is generated, and
`references/catalog/MANIFEST.sha256` will flag the drift on the next `selftest`.

If a control genuinely exists on the client's site but is missing from the catalog,
that is a version difference — regenerate. If it does not exist anywhere, the request
needs widget development, which is outside this package.

## When a judgement needs changing

Cardinality limits, legacy key mappings, open-vocabulary flags and naming hazards are
**manual observations** and live in `tools/crecs-template-studio/notes.manual.json`,
each with the file and line that justifies it. Edit that file, then regenerate. Keeping
them there is what lets the catalog be rebuilt without losing the knowledge.

## Updating an installed copy

| surface | how |
| --- | --- |
| Claude Code (skill) | replace the folder in `.claude/skills/` or `~/.claude/skills/`; it is picked up in a running session |
| Claude Code (plugin) | `/plugin update crecs-template-studio`, or reinstall from the marketplace directory |
| claude.ai | upload the new zip, delete the old skill entry — per-user, so everyone repeats it |
| Codex / ChatGPT | replace the folder in `.agents/skills/` or `~/.agents/skills/` |
| file kit | re-attach the new files |

After any update, run `selftest`. It verifies the manifest, so a partial copy is
caught rather than silently used.

## Version

The package version lives in `scripts/crecs/__init__.py` (`__version__`) and is
stamped into the plugin manifest and `dist/crecs-template-studio/packages.json`. Bump
it whenever the shipped catalog or the scripts change, since claude.ai has no central
update path and the version string is how a user knows what they have.
