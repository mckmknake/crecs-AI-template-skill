# Install — Claude in the browser (claude.ai)

Upload `crecs-property-template.zip` under **Settings → Capabilities → Skills** (also reachable
at `claude.ai/customize/skills`). The zip's root is the `crecs-property-template/` folder,
which is the layout claude.ai expects.

## Prerequisite: code execution

Custom skills on claude.ai **require code execution to be enabled**. Without it the
skill will not be available at all. Turn it on in Settings first.

With code execution on, Claude can run `scripts/crecs_template.py` — validate, edit,
export — inside its sandbox, and hand you back the exported JSON file.

If code execution is off or unavailable, the skill can still be read as reference:
Claude will know the real control names and the binding rules, but it **cannot run the
validator**, so treat anything it produces as unverified. Reading the instructions is
not the same as running the checks.

## Scope

Custom skills on claude.ai are per-user. There is no org-wide distribution and no
central admin management, so each person uploads the zip themselves. Version:
**1.0.0** — check it against the version your team is meant to be on.

## Conflicting documentation

Two Anthropic pages disagree on the plan requirement (one lists Pro, Max, Team and
Enterprise; the other adds Free) and on the `description` length limit (1024 vs 200
characters). This skill's description stays under 200 characters to satisfy both.

## Updating

Upload the new zip and remove the old skill entry.
