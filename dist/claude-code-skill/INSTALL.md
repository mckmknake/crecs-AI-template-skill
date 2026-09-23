# Install — Claude Code (skill)

Copy the `crecs-property-template/` folder into one of:

| scope | path |
| --- | --- |
| this repository only | `.claude/skills/crecs-property-template/` |
| every project you open | `~/.claude/skills/crecs-property-template/` |

```bash
mkdir -p .claude/skills
cp -r crecs-property-template .claude/skills/
```

Claude Code watches those directories, so the skill is picked up inside a running
session — no restart. Check it loaded:

```bash
python3 .claude/skills/crecs-property-template/scripts/crecs_template.py selftest
```

Then say what you want changed, or type `/crecs-property-template`.

## Requirements

Python 3.9+ on PATH. Nothing else: no network, no WordPress, no PHP, no CRE Cloud
credentials. The bundled test suite runs offline with
`python3 scripts/tests/run_tests.py`.

## Updating

Replace the folder and re-run `selftest`. `MANIFEST.sha256` in this package lists
every file's hash if you need to confirm an install is intact.
