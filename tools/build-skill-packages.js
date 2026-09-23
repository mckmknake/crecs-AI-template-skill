/**
 * CRECS Template Studio — per-surface package builder (developer tool).
 *
 * Copies the canonical skill into one self-contained package per surface, in the
 * layout each surface's current documentation specifies. No symlinks, no path that
 * leaves the package, no developer-only file, no secret, no client data.
 *
 * Verified formats (consulted 2026-09-18):
 *   Claude Code plugin  .claude-plugin/plugin.json, only `name` required; skills are
 *                       auto-discovered under skills/<name>/SKILL.md
 *                       https://code.claude.com/docs/en/plugins-reference
 *   Claude Code skill   ~/.claude/skills/<name>/ or .claude/skills/<name>/
 *                       https://code.claude.com/docs/en/skills
 *   claude.ai           zip whose ROOT is the skill folder
 *                       https://support.claude.com/en/articles/12512198-creating-custom-skills
 *   Codex / ChatGPT     $HOME/.agents/skills, $CWD/.agents/skills,
 *                       $REPO_ROOT/.agents/skills, /etc/codex/skills;
 *                       SKILL.md needs name + description; optional
 *                       agents/openai.yaml carries UI metadata
 *                       https://learn.chatgpt.com/docs/build-skills
 *
 * Usage:
 *   node build-skill-packages.js <skillRoot> <distRoot>
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const zlib = require('zlib');

/**
 * Minimal deterministic zip writer.
 *
 * Windows' Compress-Archive writes entry names with backslashes, which the ZIP
 * specification does not allow and which some readers mishandle — and the claude.ai
 * upload needs the skill folder to be the archive root. Writing the archive here gives
 * forward slashes, a fixed timestamp (so two builds are byte-identical) and no
 * external tool dependency.
 */
function writeZip(zipPath, entries) {
  const DOS_TIME = 0x0000; // 00:00:00
  const DOS_DATE = 0x2821; // 2000-01-01, fixed for reproducibility
  const locals = [];
  const centrals = [];
  let offset = 0;

  for (const entry of entries) {
    const nameBuf = Buffer.from(entry.name.split(path.sep).join('/'), 'utf8');
    const raw = entry.data;
    const deflated = zlib.deflateRawSync(raw, { level: 9 });
    const useDeflate = deflated.length < raw.length;
    const body = useDeflate ? deflated : raw;
    const method = useDeflate ? 8 : 0;
    const crc = crc32(raw);

    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50, 0);
    local.writeUInt16LE(20, 4);           // version needed
    local.writeUInt16LE(0x0800, 6);       // UTF-8 names
    local.writeUInt16LE(method, 8);
    local.writeUInt16LE(DOS_TIME, 10);
    local.writeUInt16LE(DOS_DATE, 12);
    local.writeUInt32LE(crc, 14);
    local.writeUInt32LE(body.length, 18);
    local.writeUInt32LE(raw.length, 22);
    local.writeUInt16LE(nameBuf.length, 26);
    local.writeUInt16LE(0, 28);
    locals.push(local, nameBuf, body);

    const central = Buffer.alloc(46);
    central.writeUInt32LE(0x02014b50, 0);
    central.writeUInt16LE(20, 4);         // version made by
    central.writeUInt16LE(20, 6);         // version needed
    central.writeUInt16LE(0x0800, 8);
    central.writeUInt16LE(method, 10);
    central.writeUInt16LE(DOS_TIME, 12);
    central.writeUInt16LE(DOS_DATE, 14);
    central.writeUInt32LE(crc, 16);
    central.writeUInt32LE(body.length, 20);
    central.writeUInt32LE(raw.length, 24);
    central.writeUInt16LE(nameBuf.length, 28);
    central.writeUInt16LE(0, 30);
    central.writeUInt16LE(0, 32);
    central.writeUInt16LE(0, 34);
    central.writeUInt16LE(0, 36);
    central.writeUInt32LE(0, 38);
    central.writeUInt32LE(offset, 42);
    centrals.push(central, nameBuf);

    offset += local.length + nameBuf.length + body.length;
  }

  const centralBuf = Buffer.concat(centrals);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(0, 4);
  end.writeUInt16LE(0, 6);
  end.writeUInt16LE(entries.length, 8);
  end.writeUInt16LE(entries.length, 10);
  end.writeUInt32LE(centralBuf.length, 12);
  end.writeUInt32LE(offset, 16);
  end.writeUInt16LE(0, 20);

  fs.writeFileSync(zipPath, Buffer.concat([...locals, centralBuf, end]));
}

let CRC_TABLE = null;
function crc32(buf) {
  if (!CRC_TABLE) {
    CRC_TABLE = new Int32Array(256);
    for (let i = 0; i < 256; i++) {
      let c = i;
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      CRC_TABLE[i] = c;
    }
  }
  let crc = -1;
  for (let i = 0; i < buf.length; i++) {
    crc = (crc >>> 8) ^ CRC_TABLE[(crc ^ buf[i]) & 0xff];
  }
  return (crc ^ -1) >>> 0;
}

const [, , skillRoot, distRoot] = process.argv;
if (!skillRoot || !distRoot) {
  console.error('Usage: node build-skill-packages.js <skillRoot> <distRoot>');
  process.exit(1);
}

const SKILL_NAME = 'crecs-property-template';
const VERSION = readVersion();

function readVersion() {
  const initPy = fs.readFileSync(
    path.join(skillRoot, 'scripts', 'crecs', '__init__.py'), 'utf8'
  );
  const match = /__version__ = "([^"]+)"/.exec(initPy);
  return match ? match[1] : '0.0.0';
}

/** Files that must never leave the developer environment. */
const EXCLUDE_DIRS = new Set(['__pycache__', '.pytest_cache', '.git']);
const EXCLUDE_NAMES = new Set(['.DS_Store', 'Thumbs.db']);

function copyTree(from, to, opts = {}) {
  const skipTests = !!opts.skipTests;
  fs.mkdirSync(to, { recursive: true });
  for (const entry of fs.readdirSync(from, { withFileTypes: true })) {
    if (entry.isSymbolicLink()) {
      throw new Error('refusing to package a symlink: ' + path.join(from, entry.name));
    }
    if (EXCLUDE_NAMES.has(entry.name)) continue;
    const src = path.join(from, entry.name);
    const dst = path.join(to, entry.name);
    if (entry.isDirectory()) {
      if (EXCLUDE_DIRS.has(entry.name)) continue;
      if (skipTests && entry.name === 'tests') continue;
      copyTree(src, dst, opts);
    } else if (entry.name.endsWith('.pyc')) {
      continue;
    } else {
      fs.copyFileSync(src, dst);
    }
  }
}

const sha256 = (file) => crypto.createHash('sha256')
  .update(fs.readFileSync(file)).digest('hex');

function walkFiles(root, base = root) {
  const out = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const abs = path.join(root, entry.name);
    if (entry.isDirectory()) out.push(...walkFiles(abs, base));
    else out.push(path.relative(base, abs).split(path.sep).join('/'));
  }
  return out;
}

function writeManifest(packageDir) {
  const files = walkFiles(packageDir)
    .filter((f) => f !== 'MANIFEST.sha256')
    .sort();
  const lines = files.map((rel) => `${sha256(path.join(packageDir, rel))}  ${rel}`);
  fs.writeFileSync(path.join(packageDir, 'MANIFEST.sha256'), lines.join('\n') + '\n');
  return files.length;
}

fs.rmSync(distRoot, { recursive: true, force: true });
fs.mkdirSync(distRoot, { recursive: true });

const built = [];

function record(name, dir, extra) {
  const count = writeManifest(dir);
  built.push({ name, dir: path.relative(process.cwd(), dir), files: count, ...extra });
}

// ---------------------------------------------------------------------------
// 1. Claude Code — bare skill directory
// ---------------------------------------------------------------------------

{
  const pkg = path.join(distRoot, 'claude-code-skill');
  copyTree(skillRoot, path.join(pkg, SKILL_NAME));
  fs.writeFileSync(path.join(pkg, 'INSTALL.md'), `# Install — Claude Code (skill)

Copy the \`${SKILL_NAME}/\` folder into one of:

| scope | path |
| --- | --- |
| this repository only | \`.claude/skills/${SKILL_NAME}/\` |
| every project you open | \`~/.claude/skills/${SKILL_NAME}/\` |

\`\`\`bash
mkdir -p .claude/skills
cp -r ${SKILL_NAME} .claude/skills/
\`\`\`

Claude Code watches those directories, so the skill is picked up inside a running
session — no restart. Check it loaded:

\`\`\`bash
python3 .claude/skills/${SKILL_NAME}/scripts/crecs_template.py selftest
\`\`\`

Then say what you want changed, or type \`/${SKILL_NAME}\`.

## Requirements

Python 3.9+ on PATH. Nothing else: no network, no WordPress, no PHP, no CRE Cloud
credentials. The bundled test suite runs offline with
\`python3 scripts/tests/run_tests.py\`.

## Updating

Replace the folder and re-run \`selftest\`. \`MANIFEST.sha256\` in this package lists
every file's hash if you need to confirm an install is intact.
`);
  record('claude-code-skill', pkg, { format: '.claude/skills/<name>/' });
}

// ---------------------------------------------------------------------------
// 2. Claude Code — plugin
// ---------------------------------------------------------------------------

{
  const pkg = path.join(distRoot, 'claude-code-plugin');
  copyTree(skillRoot, path.join(pkg, 'skills', SKILL_NAME));
  fs.mkdirSync(path.join(pkg, '.claude-plugin'), { recursive: true });
  // Only `name` is required; the rest is metadata. Skills under skills/<name>/ are
  // auto-discovered, so no `skills` field is needed.
  fs.writeFileSync(path.join(pkg, '.claude-plugin', 'plugin.json'),
    JSON.stringify({
      name: 'crecs-template-studio',
      displayName: 'CRECS Property Template',
      version: VERSION,
      description: 'Design and edit the shared CRECS Elementor property-page template '
        + 'by conversation, then export importable Elementor JSON.',
      license: 'proprietary',
      keywords: ['crecs', 'elementor', 'wordpress', 'commercial-real-estate'],
    }, null, 2) + '\n');
  fs.writeFileSync(path.join(pkg, 'INSTALL.md'), `# Install — Claude Code (plugin)

This is a Claude Code plugin: \`.claude-plugin/plugin.json\` plus
\`skills/${SKILL_NAME}/\`. Skills under \`skills/<name>/SKILL.md\` are discovered
automatically, so the manifest carries metadata only.

## From a local directory marketplace

Point Claude Code at the directory that contains this package and install it by name:

\`\`\`
/plugin marketplace add <path to the directory containing this package>
/plugin install crecs-template-studio
\`\`\`

Then invoke it as \`/crecs-template-studio:${SKILL_NAME}\`, or just describe the change
you want.

## Or skip the plugin

If you only want the skill, use the \`claude-code-skill\` package instead and copy the
folder into \`.claude/skills/\`. The plugin wrapper exists for teams that distribute
through a marketplace.

## Requirements

Python 3.9+ on PATH.

## Not verified here

The exact marketplace catalog format is configured outside the plugin and was not
exercised in this delivery. What was verified against the current documentation is the
manifest path (\`.claude-plugin/plugin.json\`), that \`name\` is the only required
field, and that \`skills/<name>/SKILL.md\` is auto-discovered.
`);
  record('claude-code-plugin', pkg, { format: '.claude-plugin/plugin.json + skills/' });
}

// ---------------------------------------------------------------------------
// 3. claude.ai — importable zip (root = the skill folder)
// ---------------------------------------------------------------------------

{
  const staging = path.join(distRoot, '.staging-claude-web');
  copyTree(skillRoot, path.join(staging, SKILL_NAME));
  const pkg = path.join(distRoot, 'claude-web');
  fs.mkdirSync(pkg, { recursive: true });
  const zipPath = path.join(pkg, `${SKILL_NAME}.zip`);
  const entries = walkFiles(staging)
    .sort()
    .map((rel) => ({ name: rel, data: fs.readFileSync(path.join(staging, rel)) }));
  writeZip(zipPath, entries);
  fs.rmSync(staging, { recursive: true, force: true });

  fs.writeFileSync(path.join(pkg, 'INSTALL.md'), `# Install — Claude in the browser (claude.ai)

Upload \`${SKILL_NAME}.zip\` under **Settings → Capabilities → Skills** (also reachable
at \`claude.ai/customize/skills\`). The zip's root is the \`${SKILL_NAME}/\` folder,
which is the layout claude.ai expects.

## Prerequisite: code execution

Custom skills on claude.ai **require code execution to be enabled**. Without it the
skill will not be available at all. Turn it on in Settings first.

With code execution on, Claude can run \`scripts/crecs_template.py\` — validate, edit,
export — inside its sandbox, and hand you back the exported JSON file.

If code execution is off or unavailable, the skill can still be read as reference:
Claude will know the real control names and the binding rules, but it **cannot run the
validator**, so treat anything it produces as unverified. Reading the instructions is
not the same as running the checks.

## Scope

Custom skills on claude.ai are per-user. There is no org-wide distribution and no
central admin management, so each person uploads the zip themselves. Version:
**${VERSION}** — check it against the version your team is meant to be on.

## Conflicting documentation

Two Anthropic pages disagree on the plan requirement (one lists Pro, Max, Team and
Enterprise; the other adds Free) and on the \`description\` length limit (1024 vs 200
characters). This skill's description stays under 200 characters to satisfy both.

## Updating

Upload the new zip and remove the old skill entry.
`);
  record('claude-web', pkg, { format: 'zip, root = skill folder' });
}

// ---------------------------------------------------------------------------
// 4. Codex — skill directory under .agents/skills
// ---------------------------------------------------------------------------

{
  const pkg = path.join(distRoot, 'codex-skill');
  copyTree(skillRoot, path.join(pkg, SKILL_NAME));
  fs.writeFileSync(path.join(pkg, 'INSTALL.md'), `# Install — Codex

Copy the \`${SKILL_NAME}/\` folder into one of the locations Codex scans:

| scope | path |
| --- | --- |
| this repository | \`.agents/skills/${SKILL_NAME}/\` |
| the whole machine | \`~/.agents/skills/${SKILL_NAME}/\` |
| admin-managed | \`/etc/codex/skills/${SKILL_NAME}/\` |

\`\`\`bash
mkdir -p .agents/skills
cp -r ${SKILL_NAME} .agents/skills/
\`\`\`

Codex resolves \`$CWD/.agents/skills\`, \`$REPO_ROOT/.agents/skills\` and
\`$HOME/.agents/skills\`, so a repo-scoped copy travels with the repository.

## An AGENTS.md pointer

Codex reads \`AGENTS.md\` before doing any work, and the combined instruction chain is
capped (32 KiB by default). So put the **pointer** there, not the knowledge:

\`\`\`markdown
## CRECS property template

Editing the shared Elementor property template? Use the \`${SKILL_NAME}\` skill in
\`.agents/skills/\`. Read its \`references/widgets/<widget>.md\` before touching a
control, and make changes through \`scripts/crecs_template.py\` rather than editing
the JSON by hand.
\`\`\`

\`adapters/AGENTS.snippet.md\` in this package holds that snippet ready to paste. It is
a separate file on purpose: this package does not modify an existing \`AGENTS.md\`.

## Requirements

Python 3.9+. The scripts are offline, so they work with Codex cloud's default
"no network during the agent phase" setting.

## Codex cloud

The skill works there, but it cannot reach a local WordPress site — nothing in this
package tries to. Everything is file-based.
`);
  fs.mkdirSync(path.join(pkg, 'adapters'), { recursive: true });
  fs.writeFileSync(path.join(pkg, 'adapters', 'AGENTS.snippet.md'),
    `## CRECS property template

Editing the shared Elementor property template? Use the \`${SKILL_NAME}\` skill in
\`.agents/skills/\`. Read its \`references/widgets/<widget>.md\` before touching a
control, and make changes through \`scripts/crecs_template.py\` rather than editing the
JSON by hand — it validates before writing and keeps element ids stable.

Key rules the skill enforces: \`crecs_property_data\` must be the first widget;
\`<control>_tablet\`/\`_mobile\` only exist on controls the reference marks responsive;
control names differ per widget; \`crecs_property_fields_and_data\` does not exist.
`);
  record('codex-skill', pkg, { format: '.agents/skills/<name>/' });
}

// ---------------------------------------------------------------------------
// 5. ChatGPT — skill directory plus UI metadata
// ---------------------------------------------------------------------------

{
  const pkg = path.join(distRoot, 'chatgpt-skill');
  const inner = path.join(pkg, SKILL_NAME);
  copyTree(skillRoot, inner);
  fs.mkdirSync(path.join(inner, 'agents'), { recursive: true });
  fs.writeFileSync(path.join(inner, 'agents', 'openai.yaml'),
    `# Optional UI metadata for the ChatGPT surfaces, per
# https://learn.chatgpt.com/docs/build-skills (consulted 2026-09-18).
# SKILL.md remains the only required file.
interface:
  display_name: "CRECS Property Template"
  short_description: "Design the shared CRECS Elementor property page and export its JSON."

policy:
  allow_implicit_invocation: true
`);
  fs.writeFileSync(path.join(pkg, 'INSTALL.md'), `# Install — ChatGPT

Agent skills use the same \`SKILL.md\` layout as Codex, and the ChatGPT surfaces read
them from the \`.agents/skills\` locations. \`${SKILL_NAME}/agents/openai.yaml\` adds
the display name and description for the skills list; \`SKILL.md\` stays the only
required file.

## Desktop app

Copy \`${SKILL_NAME}/\` into \`~/.agents/skills/\`. It appears in the Skills section of
the sidebar.

\`\`\`bash
mkdir -p ~/.agents/skills
cp -r ${SKILL_NAME} ~/.agents/skills/
\`\`\`

## Web

Skills reach ChatGPT on the web when they are bundled inside a plugin; the web app
does not read local Codex configuration. If you cannot install natively — no plugin,
or an admin-restricted workspace — use the **chatgpt-file-kit** package instead.

## What was NOT verified

Whether the ChatGPT **web** app executes a skill's bundled \`scripts/\` was not
confirmed against the documentation. The docs describe \`scripts/\` as part of the
format and list ChatGPT web among the surfaces that load skills, but do not state that
web executes them. Assume it may not: if the validator cannot run, what you get is
reference knowledge, not verified output. Say so rather than implying it was checked.

## Requirements

Python 3.9+ wherever the scripts actually run.
`);
  record('chatgpt-skill', pkg, { format: '.agents/skills/<name>/ + agents/openai.yaml' });
}

// ---------------------------------------------------------------------------
// 6. ChatGPT — file kit for when native install is unavailable
// ---------------------------------------------------------------------------

{
  const pkg = path.join(distRoot, 'chatgpt-file-kit');
  fs.mkdirSync(pkg, { recursive: true });
  copyTree(path.join(skillRoot, 'references'), path.join(pkg, 'references'));
  copyTree(path.join(skillRoot, 'assets'), path.join(pkg, 'assets'));
  copyTree(path.join(skillRoot, 'scripts'), path.join(pkg, 'scripts'));
  fs.copyFileSync(path.join(skillRoot, 'SKILL.md'), path.join(pkg, 'SKILL.md'));

  fs.writeFileSync(path.join(pkg, 'OPENING-INSTRUCTION.md'), `# Opening instruction

Paste this as your first message, with the files attached, when the skill cannot be
installed natively. It replaces the automatic discovery that a real skill install
gives you.

---

You are helping me design the shared Elementor property-page template for a CRE Cloud
Solutions (CRECS) WordPress site. I have attached a skill bundle. Before doing anything
else:

1. Read \`SKILL.md\` in full. It is the operating manual — follow it, including the
   rules about the loader being first, per-widget control names, and responsiveness.
2. Read \`references/INDEX.md\` so you know which widget reference to open later.
3. Do **not** guess a control name. Open \`references/widgets/<widget>.md\` and use the
   exact keys it lists. If a control is not there, it does not exist in the installed
   plugin version — tell me instead of inventing a key.
4. If you can run files, use \`scripts/crecs_template.py\`. Start with:
   \`python3 scripts/crecs_template.py selftest\`, then
   \`python3 scripts/crecs_template.py init --from assets/property-template-all-widgets.json --workdir ./work --profile ./my-profile.json\`.
   Every change goes through \`set\`/\`move\`/\`add-widget\`/\`remove\`/\`bind\`, then
   \`validate\`, then \`export\`.
5. If you **cannot** run files in this conversation, say so up front. You can still use
   the references to propose changes, but you must label the result as unvalidated:
   reading the rules is not the same as running the validator. Do not claim a template
   is correct, and do not claim it looks right — nothing here renders anything.

Reply in my language. Do not translate the site's own content.

---

## Attach these

Minimum, for reference-only work:

- \`SKILL.md\`
- \`references/INDEX.md\`
- \`references/catalog/crecs-property-fields.json\`
- the \`references/widgets/*.md\` files for the widgets you are changing

Add these when file execution is available:

- \`assets/property-template-all-widgets.json\`
- \`assets/target-profile.example.json\`
- \`references/catalog/crecs-controls.min.json\`
- the whole \`scripts/\` folder

\`references/catalog/crecs-controls.min.json\` is about 1.8 MB. It is what the scripts
read; you do not need to read it yourself, and you should not paste it into the
conversation. Use the per-widget Markdown files for reading — they are 1–30 KB each.
`);

  fs.writeFileSync(path.join(pkg, 'INSTALL.md'), `# Install — file kit

For any surface where a skill cannot be installed: attach the files and paste
\`OPENING-INSTRUCTION.md\` as the first message.

This is the weakest of the packages and it is deliberately explicit about why: without
file execution the validator never runs, so nothing the assistant produces has been
checked. Use it when that is the only option, and read \`OPENING-INSTRUCTION.md\` —
it tells the assistant to say so rather than implying otherwise.

Everything here is a copy of the canonical skill; \`MANIFEST.sha256\` lets you confirm
that.
`);
  record('chatgpt-file-kit', pkg, { format: 'loose files + opening instruction' });
}

// ---------------------------------------------------------------------------
// index
// ---------------------------------------------------------------------------

const index = {
  _about: 'Per-surface packages of the crecs-property-template skill. Generated by '
    + 'tools/crecs-template-studio/build-skill-packages.js — do not edit by hand.',
  version: VERSION,
  generated_at: new Date().toISOString(),
  canonical_skill: 'skills/crecs-property-template',
  packages: built,
  formats_verified_on: '2026-09-18',
  format_sources: {
    claude_code_plugin: 'https://code.claude.com/docs/en/plugins-reference',
    claude_code_skill: 'https://code.claude.com/docs/en/skills',
    claude_web_zip: 'https://support.claude.com/en/articles/12512198-creating-custom-skills',
    codex_and_chatgpt_skill: 'https://learn.chatgpt.com/docs/build-skills',
  },
};
fs.writeFileSync(path.join(distRoot, 'packages.json'),
  JSON.stringify(index, null, 2) + '\n');

fs.writeFileSync(path.join(distRoot, 'README.md'), `# dist/crecs-template-studio

Per-surface packages of the \`crecs-property-template\` skill, version **${VERSION}**.
Generated from \`skills/crecs-property-template\` by
\`tools/crecs-template-studio/build-skill-packages.js\`. Do not edit these — regenerate.

| package | surface | layout |
| --- | --- | --- |
${built.map((b) => `| \`${path.basename(b.dir)}\` | ${b.name} | ${b.format} |`).join('\n')}

Each package carries its own \`INSTALL.md\` and \`MANIFEST.sha256\`. Verify one with:

\`\`\`bash
node tools/crecs-template-studio/verify-package.js dist/crecs-template-studio/<package>
\`\`\`

## Which one do I want?

- **Claude Code** — \`claude-code-skill\` for a drop-in folder, or
  \`claude-code-plugin\` if your team distributes through a marketplace.
- **Claude in the browser** — \`claude-web\`. Needs code execution enabled.
- **Codex** (CLI, IDE extension, cloud) — \`codex-skill\`, plus the \`AGENTS.md\`
  snippet it ships in \`adapters/\`.
- **ChatGPT desktop** — \`chatgpt-skill\`.
- **Anywhere a skill cannot be installed** — \`chatgpt-file-kit\`.

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
`);

console.log('built %d packages in %s', built.length,
  path.relative(process.cwd(), distRoot));
for (const entry of built) {
  console.log('  ' + path.basename(entry.dir).padEnd(22) + String(entry.files).padStart(3)
    + ' files  ' + entry.format);
}
