# Install — ChatGPT

Agent skills use the same `SKILL.md` layout as Codex, and the ChatGPT surfaces read
them from the `.agents/skills` locations. `crecs-property-template/agents/openai.yaml` adds
the display name and description for the skills list; `SKILL.md` stays the only
required file.

## Desktop app

Copy `crecs-property-template/` into `~/.agents/skills/`. It appears in the Skills section of
the sidebar.

```bash
mkdir -p ~/.agents/skills
cp -r crecs-property-template ~/.agents/skills/
```

## Web

Skills reach ChatGPT on the web when they are bundled inside a plugin; the web app
does not read local Codex configuration. If you cannot install natively — no plugin,
or an admin-restricted workspace — use the **chatgpt-file-kit** package instead.

## What was NOT verified

Whether the ChatGPT **web** app executes a skill's bundled `scripts/` was not
confirmed against the documentation. The docs describe `scripts/` as part of the
format and list ChatGPT web among the surfaces that load skills, but do not state that
web executes them. Assume it may not: if the validator cannot run, what you get is
reference knowledge, not verified output. Say so rather than implying it was checked.

## Requirements

Python 3.9+ wherever the scripts actually run.
