# Install — Claude Code (plugin)

This is a Claude Code plugin: `.claude-plugin/plugin.json` plus
`skills/crecs-property-template/`. Skills under `skills/<name>/SKILL.md` are discovered
automatically, so the manifest carries metadata only.

## From a local directory marketplace

Point Claude Code at the directory that contains this package and install it by name:

```
/plugin marketplace add <path to the directory containing this package>
/plugin install crecs-template-studio
```

Then invoke it as `/crecs-template-studio:crecs-property-template`, or just describe the change
you want.

## Or skip the plugin

If you only want the skill, use the `claude-code-skill` package instead and copy the
folder into `.claude/skills/`. The plugin wrapper exists for teams that distribute
through a marketplace.

## Requirements

Python 3.9+ on PATH.

## Not verified here

The exact marketplace catalog format is configured outside the plugin and was not
exercised in this delivery. What was verified against the current documentation is the
manifest path (`.claude-plugin/plugin.json`), that `name` is the only required
field, and that `skills/<name>/SKILL.md` is auto-discovered.
