# Compatibility matrix — ChatGPT · Codex · Claude · Claude Code

## Delivery-4 addendum, consulted 2026-09-21

The preview needs a transport, and that is where the four surfaces genuinely differ.

| Surface | Reaches a preview service how | Delivery-4 status |
| --- | --- | --- |
| **Claude Code** | local process, stdio MCP, localhost | **PASS** — CLI adapter and stdio MCP both exercised against a live site |
| **Codex** | the same, plus project-scoped MCP for trusted projects only | **NOT_RUN** — no account |
| **Claude web** | a **remote** MCP server reached from Anthropic's cloud. Anthropic states the server "must be reachable over the public internet from Anthropic's IP ranges" and that one "hosted on a private corporate network, behind a VPN, or blocked by a firewall won't connect". OAuth client id and secret are optional under Advanced settings. On Team and Enterprise, only an **owner** can add a connector. | **BLOCKED** — needs a public HTTPS endpoint |
| **ChatGPT web** | remote **Streamable HTTP** MCP surfaced through a plugin. **localhost is not reachable**; only local clients such as Codex can. Workspace administrators control which plugins and tools are available. | **BLOCKED** — same |

So a local watcher or a stdio server satisfies two surfaces and cannot satisfy the other
two. This closes gap 7 of the original matrix (Claude custom connectors / MCP, "not
investigated").

The endpoint the two web surfaces need was decided to belong on the **CRE Cloud SaaS**,
outside this repository. `tools/preview-mcp/server.js` is what that service would run
or proxy; it was tested locally only, and that is not evidence about either web surface.

Consulted **2026-09-18**. Every row below cites the page it came from. Rows marked
**NOT VERIFIED** were not confirmed against official documentation in this session
and must not be treated as fact.

Two assumptions are deliberately **not** made here:

- that a CLI-installable extension is usable in a web chat;
- that MCP support implies any visual interface. MCP exposes tools, resources and
  prompts — not UI.

## Sources

| Ref | URL | Consulted |
| --- | --- | --- |
| S1 | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview | 2026-09-18 |
| S2 | https://code.claude.com/docs/en/skills | 2026-09-18 |
| S3 | https://support.claude.com/en/articles/12512198-creating-custom-skills | 2026-09-18 |
| S4 | https://learn.chatgpt.com/docs/build-skills (redirect from https://developers.openai.com/codex/skills) | 2026-09-18 |
| S5 | https://learn.chatgpt.com/docs/customization/overview (redirect from https://developers.openai.com/codex/concepts/customization) | 2026-09-18 |
| S6 | https://developers.openai.com/codex/config-reference · https://learn.chatgpt.com/docs/agent-configuration/agents-md | 2026-09-18 (config-reference via search result summary only — see gaps) |
| S7 | https://learn.chatgpt.com/docs/extend/mcp | 2026-09-18 |
| S8 | https://learn.chatgpt.com/docs/projects?surface=app | 2026-09-18 |
| S9 | https://developers.openai.com/codex/cloud/environments | 2026-09-18 (via search result summary only — see gaps) |
| S10 | https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt | 2026-09-18 (via search result summary only — see gaps) |
| S11 | https://developers.openai.com/codex/mcp | 2026-09-18 (via search result summary only — see gaps) |

## The good news up front

All four surfaces load a **`SKILL.md` directory** as their packaging unit for
reusable capability. That means delivery 2 can write **one knowledge core** and vary
only installation and packaging.

| Surface | Packaging unit | Required frontmatter |
| --- | --- | --- |
| Claude Code | `<name>/SKILL.md` directory on disk (S2) | all fields optional; `description` recommended (S2) |
| claude.ai | `<name>/SKILL.md` inside a zip whose **root is the skill folder** (S3) | `name`, `description` (S1) |
| ChatGPT | `<name>/SKILL.md` directory (S4) | `name`, `description` (S4) |
| Codex | `<name>/SKILL.md` directory (S4) | `name`, `description` (S4) |

The frontmatter supersets differ, so a portable core should use only `name` and
`description` in the shared file and keep surface-specific keys in per-surface
overlays.

## Matrix

| Capability | ChatGPT (web / desktop / mobile) | Codex (CLI · IDE · cloud) | Claude apps (claude.ai) | Claude Code |
| --- | --- | --- | --- | --- |
| **Skill install path** | Skills load in the **desktop app** via a sidebar Skills section; in **web, desktop and mobile** when bundled inside a plugin (S4) | `$HOME/.agents/skills`, `$CWD/.agents/skills`, `$REPO_ROOT/.agents/skills`, `$CWD/../.agents/skills`, admin `/etc/codex/skills` (S4) | zip upload via Settings → Features (S1) / Customize → Skills (S3) | `~/.claude/skills/<name>/` personal · `.claude/skills/<name>/` project · `<subdir>/.claude/skills/` nested · `<plugin>/skills/<name>/` plugin · enterprise managed dir (S2) |
| **Skills work without a repo?** | yes (chat surface) | skills yes; `AGENTS.md` is repo-oriented (S5) | yes | yes (personal scope) |
| **Project-level instructions file** | Project **instructions** field, not a file (S8) | `~/.codex/AGENTS.md` global; `AGENTS.override.md` then `AGENTS.md` per directory, closer wins; skipped if empty; combined cap `project_doc_max_bytes`, 32 KiB default (S6) | Project instructions in the UI — NOT VERIFIED for exact field limits | `CLAUDE.md` (already in use in this repo) |
| **Bundled reference files** | yes, via the skill directory (S4); Projects also accept uploaded **Sources** that persist across the project's chats (S8) | yes — `scripts/`, `references/`, `assets/` (S4, S5) | yes, inside the zip (S3) | yes; supporting files load only when read (S2) |
| **Runs bundled scripts** | skill `scripts/` are supported as a concept (S4). Whether the **web** app executes them — **NOT VERIFIED** | yes; scripts give "deterministic behavior or external tooling" (S4) | yes, **but requires code execution to be enabled** (S1, S3) | yes, via bash, with the user's own permissions (S2) |
| **Network access at runtime** | NOT VERIFIED | cloud: available during the **setup script** phase; **off by default during the agent phase**, configurable allowlist (S9) | varies by user/admin settings — full, partial or none (S1) | full — same as any program on the machine (S1, S2) |
| **Reads local files / a WordPress install** | no — ChatGPT web does not read local Codex configuration files (S7); Projects give no folder access (S8) | yes (CLI and IDE, local repo); cloud works on a cloned repo | no | yes |
| **Can drive a local dev site (delivery 4 preview)** | no | CLI/IDE yes; cloud no (no access to `kingrealty.local`) | no | **yes** |
| **MCP** | web: install a **plugin** that bundles remote MCP tools; desktop: Settings → MCP servers, STDIO or Streamable HTTP, `/mcp` in the composer (S7). Custom connectors need developer mode under Workspace Settings → Permissions & Roles (S10) | `~/.codex/config.toml`, or project-scoped `.codex/config.toml` for **trusted projects only** (S11) | custom connectors — NOT VERIFIED in this session | yes (project/user scoped MCP config) |
| **Sharing scope** | workspace admins control which plugins and tools are available (S7) | filesystem / repo, so git-shareable | **individual user only**; no org-wide distribution, no central admin management (S1) | personal, project (git-shareable), plugin, or enterprise-managed (S1, S2) |
| **Skills sync across surfaces** | — | — | **no** — claude.ai skills are not available on the API and vice versa (S1) | claude.ai skills sync **into** Claude Code at `~/.claude/skills/synced/`, refreshed ~every 10 min (S2) |

## Constraints that change the design of delivery 2

### 1. Two tiers of capability, not four

| Tier | Surfaces | What the skill can do |
| --- | --- | --- |
| **Full** — reads the repo, runs scripts, reaches the local site | Claude Code; Codex CLI / IDE | Regenerate the catalog, validate a generated template against it, drive the Elementor editor, run the delivery-4 preview |
| **Chat** — instructions plus bundled reference data, no local access | claude.ai; ChatGPT web (and Codex cloud, for anything needing `kingrealty.local`) | Read the catalog **as bundled data**, produce a template JSON, explain it. Cannot verify against the live install. |

So the knowledge core must carry the catalog as **committed data files**, not as
"run the extractor". The extractor is a full-tier convenience; the chat tier needs
the JSON already there. This is already how delivery 1 is laid out.

### 2. Synced claude.ai skills lose shell execution

A skill synced from claude.ai into Claude Code has `!` command execution replaced by
`[shell command execution disabled by policy]`, `@` file attachment disabled, and
`${CLAUDE_PROJECT_DIR}` / `${CLAUDE_SESSION_ID}` passed through as literal text (S2).

A single skill authored for claude.ai and synced down will therefore **not** be able
to run the validator. Ship the Claude Code version as a real `.claude/skills/`
directory in this repository, and treat the claude.ai zip as a separate,
chat-tier package.

### 3. claude.ai cannot be distributed to a team centrally

Custom skills on claude.ai are per-user with no admin distribution (S1). Every person
who needs it uploads the zip themselves. Plan for a versioned zip artefact with a
visible version string, since there is no central update path.

### 4. Code execution must be enabled on claude.ai

Custom skills there require code execution enabled (S1, S3). If a client has it off,
the skill will not be available at all — not merely degraded.

### 5. Codex needs both an `AGENTS.md` pointer and a skill

Codex reads `AGENTS.md` before doing any work (S5, S6) and resolves skills from
`.agents/skills`. The two are complementary: a short `AGENTS.md` note pointing at the
skill makes the skill discoverable in repo-oriented sessions, while the skill itself
carries the knowledge. The 32 KiB `project_doc_max_bytes` cap (S6) means the
knowledge must **not** live in `AGENTS.md`.

Note also that this repository already has a `CLAUDE.md` and **no `AGENTS.md`**.
Delivery 2 will need to add one for Codex, or configure
`project_doc_fallback_filenames` to pick up `CLAUDE.md` (S6).

### 6. Trust boundaries differ

Project-scoped MCP config in Codex applies to **trusted projects only** (S11), and
ChatGPT MCP tooling is gated by workspace admin settings and developer mode
(S7, S10). Any delivery-4 design that depends on an MCP bridge must assume it may be
unavailable per organisation and degrade to the chat tier.

### 7. Anthropic's own guidance: treat skills as software

S1 states plainly that a malicious skill "can direct Claude to invoke tools or
execute code in ways that don't match the Skill's stated purpose", and that skills
should come only from trusted sources and be audited file by file. Given this
plugin's history of a compromised build (a `-withmalware` ZIP sits beside the clean
releases), delivery 2 should ship the skill from this repository, reviewed in the
normal diff, and never as an opaque download.

## Documented gaps

These were **not** resolved and must not be filled in by assumption:

1. **Does ChatGPT web execute a skill's bundled scripts?** S4 describes `scripts/` as
   part of the format and lists ChatGPT web among the surfaces that load skills (when
   plugin-bundled), but does not state that web executes them. Unverified.
2. **Exact ChatGPT Projects limits** — file count, file size, instruction length.
   S8 explicitly does not specify them.
3. **Plan requirement for claude.ai custom skills** — S1 says "Pro, Max, Team, and
   Enterprise"; S3 says "Free, Pro, Max, Team, and Enterprise". The two Anthropic
   pages disagree. Recorded as a conflict, not resolved.
4. **`description` length limit for claude.ai skills** — S1 says max 1024 characters;
   S3 says max 200. Same conflict. Delivery 2 should stay under 200 to satisfy both.
5. **Per-surface support for `AGENTS.md`** — S5 lists the Codex surfaces (ChatGPT
   desktop, remote, ChatGPT web, Codex CLI, Codex IDE extension, Codex cloud) but does
   not say which of them actually load `AGENTS.md` or `.agents/skills`. Unverified per
   surface.
6. **S6, S9, S10, S11** were read through search-result summaries rather than a direct
   page fetch. Their specific numbers (32 KiB cap, cloud network defaults, developer
   mode menu path, `config.toml` locations) should be re-confirmed against the pages
   themselves before delivery 2 depends on them.
7. **Claude apps custom connectors / MCP** — not investigated in this session.
8. Mobile behaviour for any surface — not investigated.

---

# Delivery 2 — what was built per surface, and what was actually run

Consulted again **2026-09-18**. Three new sources close gaps that delivery 1 left
open; two of delivery 1's gaps remain open and are restated below.

| Ref | URL | Consulted | What it settled |
| --- | --- | --- | --- |
| S12 | https://code.claude.com/docs/en/plugins-reference | 2026-09-18 | The Claude Code plugin manifest is `.claude-plugin/plugin.json`; `name` is the only required field; skills under `skills/<name>/SKILL.md` are auto-discovered, so no `skills` field is needed; a `SKILL.md` at the plugin root is loaded as a single skill. |
| S13 | https://learn.chatgpt.com/docs/build-skills | 2026-09-18 | Codex/ChatGPT skills need `SKILL.md` with `name` + `description` and nothing else; optional `scripts/`, `references/`, `assets/` and `agents/openai.yaml` for UI metadata; resolution order `$CWD/.agents/skills`, `$REPO_ROOT/.agents/skills`, `$HOME/.agents/skills`, `/etc/codex/skills`; the ChatGPT desktop app shows them in a sidebar Skills section. |
| S3 | https://support.claude.com/en/articles/12512198-creating-custom-skills | 2026-09-18 | The claude.ai zip's **root must be the skill folder**, and custom skills require code execution enabled. |

## Packages

| Surface | Package | Format used | Source |
| --- | --- | --- | --- |
| Claude Code | `claude-code-skill` | `<name>/` to drop into `.claude/skills/` or `~/.claude/skills/` | S2 |
| Claude Code | `claude-code-plugin` | `.claude-plugin/plugin.json` + `skills/<name>/` | S12 |
| Claude in the browser | `claude-web` | `crecs-property-template.zip`, root = the skill folder | S3 |
| Codex (CLI · IDE · cloud) | `codex-skill` | `<name>/` for `.agents/skills/`, plus `adapters/AGENTS.snippet.md` | S13, S5, S6 |
| ChatGPT desktop | `chatgpt-skill` | `<name>/` + `agents/openai.yaml` | S13 |
| Anywhere a skill cannot be installed | `chatgpt-file-kit` | loose files + `OPENING-INSTRUCTION.md` | — |

No manifest field or path was invented: everything above traces to one of the sources.
The plugin manifest carries only `name` plus optional metadata, and no `skills` field,
because the documented auto-discovery covers it.

## Constraints from delivery 1, and what was done about them

| Constraint | Handled how |
| --- | --- |
| Custom skills do not sync across surfaces (S1) | one canonical skill, six generated packages, each with its own `INSTALL.md`; `packages.json` records which format came from which source |
| A claude.ai skill synced into Claude Code loses `!` shell execution (S2) | the Claude Code packages are real `.claude/skills/` directories built from this repository, not a synced copy; the claude.ai zip is a separate chat-tier artefact |
| claude.ai has no central distribution (S1) | the version string is stamped into `scripts/crecs/__init__.py`, the plugin manifest and `packages.json`, and `INSTALL.md` tells the user to check it |
| claude.ai requires code execution (S1, S3) | `INSTALL.md` states it as a prerequisite and says plainly that without it the skill is reference only and its output is unverified |
| `description` length conflict, 1024 vs 200 (S1 vs S3) | the skill's `description` is **182 characters**, inside both limits |
| Knowledge must not live in `AGENTS.md`, 32 KiB cap (S6) | `adapters/AGENTS.snippet.md` is a ~700-byte pointer; the knowledge stays in the skill |
| Codex cloud has no network during the agent phase (S9) | every script is offline, standard library only |
| No vendor-exclusive hook, variable or tool in the core | `SKILL.md` and the Python package contain no `!`-command injection, no `${CLAUDE_*}` variable, no `allowed-tools`, no MCP dependency. The only surface-specific files are the generated `INSTALL.md` per package, `agents/openai.yaml` (ChatGPT), `.claude-plugin/plugin.json` (Claude Code) and `adapters/AGENTS.snippet.md` (Codex) |
| Existing `AGENTS.md` / `CLAUDE.md` must not be modified | neither was touched. The repository has no `AGENTS.md`; the Codex adapter ships a snippet to paste rather than writing one |

## What was actually executed

Claim levels kept apart, as required:

| Surface | Status | Evidence |
| --- | --- | --- |
| **Claude Code** | **tested in the harness, and driven against a real WordPress** | the 190-test suite and the 12 conversational scenarios ran under Python 3.10.12 against the canonical skill, then again from the distributed `claude-code-skill` package copied outside the repository, then natively on Windows under Python 3.13.15 with a byte-identical export. `selftest` 8/8. In delivery 3 the installed skill drove `init` from a real site export, `inspect`, `set`, `validate` and `export`, and refused two invalid requests correctly. Note the operator had read the package: a **fresh-session conversational run has still never happened on any surface** — that is what `CONVERSATIONAL-ACCEPTANCE-TEST.md` measures. |
| **Codex** | **NOT_RUN** | the package is byte-identical to the Claude Code skill plus an `INSTALL.md` and the `AGENTS.md` snippet, and `verify-package.js` passes 10/10, but **no Codex session was run**. The format follows S13; nothing is claimed about behaviour. |
| **ChatGPT** | **NOT_RUN** | same: package built and verified, no ChatGPT session run. |
| **Claude in the browser** | **NOT_RUN** | zip built and its entry list verified (76 entries, forward slashes, root = skill folder), but **not uploaded to claude.ai** and not exercised there. |

No result is attributed to a vendor whose product was not run. Delivery 3 should run
the suite on each surface and record what it finds.

## Open items

Delivery 1 listed eight; these remain.

1. **Which `description` limit is real** is still unresolved: S1 allows 1024, S3 says
   200. The skill's description was written at 375 characters for trigger quality and
   then cut to **182** so it satisfies both pages. The cost is a shorter trigger
   surface; the benefit is one file that no surface can reject. If the limit is later
   confirmed as 1024, the longer form can come back.
2. **Does ChatGPT web execute a skill's bundled scripts?** Still not stated in the
   documentation. `chatgpt-skill/INSTALL.md` says to assume it may not, and
   `OPENING-INSTRUCTION.md` tells the assistant to declare it when it cannot run files.
3. **The Claude Code plugin marketplace catalog format** was not exercised. S12
   confirms the manifest path and the auto-discovery; the marketplace entry itself is
   configured outside the plugin and is untested here.
4. **Plan requirement for claude.ai custom skills** — the S1/S3 conflict stands.
5. **Per-surface `AGENTS.md` / `.agents/skills` support** — S5 lists the Codex
   surfaces but still does not say which of them load which path.
6. **S6, S9, S10, S11** were read through search-result summaries in delivery 1 and
   were not re-fetched.
7. **Claude apps custom connectors / MCP** — not investigated; no MCP is used.
8. **Mobile behaviour** — not investigated.
