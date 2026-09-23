# dist/crecs-template-studio

Per-surface packages of the `crecs-property-template` skill, version **1.0.0**.
Generated from `skills/crecs-property-template` by
`tools/crecs-template-studio/build-skill-packages.js`. Do not edit these — regenerate.

| package | surface | layout |
| --- | --- | --- |
| `claude-code-skill` | claude-code-skill | .claude/skills/<name>/ |
| `claude-code-plugin` | claude-code-plugin | .claude-plugin/plugin.json + skills/ |
| `claude-web` | claude-web | zip, root = skill folder |
| `codex-skill` | codex-skill | .agents/skills/<name>/ |
| `chatgpt-skill` | chatgpt-skill | .agents/skills/<name>/ + agents/openai.yaml |
| `chatgpt-file-kit` | chatgpt-file-kit | loose files + opening instruction |

Each package carries its own `INSTALL.md` and `MANIFEST.sha256`. Verify one with:

```bash
node tools/crecs-template-studio/verify-package.js dist/crecs-template-studio/<package>
```

## Which one do I want?

- **Claude Code** — `claude-code-skill` for a drop-in folder, or
  `claude-code-plugin` if your team distributes through a marketplace.
- **Claude in the browser** — `claude-web`. Needs code execution enabled.
- **Codex** (CLI, IDE extension, cloud) — `codex-skill`, plus the `AGENTS.md`
  snippet it ships in `adapters/`.
- **ChatGPT desktop** — `chatgpt-skill`.
- **Anywhere a skill cannot be installed** — `chatgpt-file-kit`.

## What every package promises

- self-contained: no symlink, no path outside the package;
- offline: Python 3.9+ standard library only, no network, no WordPress, no PHP, no
  CRE Cloud credentials;
- no client data: the API-derived vocabularies (962 cities, 472 sub-markets, broker
  names) are stripped from the catalog projection, with a count and a reason left in
  their place;
- no secrets, and the target profile is refused if its keys look like credentials.

## Claim level

Everything in these packages has been statically validated and exercised by the
offline test suite. **No template has been imported into Elementor and nothing has
been rendered.** Importing and looking at the result is the next step, and it belongs
to delivery 3.
