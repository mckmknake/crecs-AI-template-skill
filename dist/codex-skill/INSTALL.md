# Install — Codex

Copy the `crecs-property-template/` folder into one of the locations Codex scans:

| scope | path |
| --- | --- |
| this repository | `.agents/skills/crecs-property-template/` |
| the whole machine | `~/.agents/skills/crecs-property-template/` |
| admin-managed | `/etc/codex/skills/crecs-property-template/` |

```bash
mkdir -p .agents/skills
cp -r crecs-property-template .agents/skills/
```

Codex resolves `$CWD/.agents/skills`, `$REPO_ROOT/.agents/skills` and
`$HOME/.agents/skills`, so a repo-scoped copy travels with the repository.

## An AGENTS.md pointer

Codex reads `AGENTS.md` before doing any work, and the combined instruction chain is
capped (32 KiB by default). So put the **pointer** there, not the knowledge:

```markdown
## CRECS property template

Editing the shared Elementor property template? Use the `crecs-property-template` skill in
`.agents/skills/`. Read its `references/widgets/<widget>.md` before touching a
control, and make changes through `scripts/crecs_template.py` rather than editing
the JSON by hand.
```

`adapters/AGENTS.snippet.md` in this package holds that snippet ready to paste. It is
a separate file on purpose: this package does not modify an existing `AGENTS.md`.

## Requirements

Python 3.9+. The scripts are offline, so they work with Codex cloud's default
"no network during the agent phase" setting.

## Codex cloud

The skill works there, but it cannot reach a local WordPress site — nothing in this
package tries to. Everything is file-based.
