/**
 * CRECS Template Studio — package verifier (developer tool).
 *
 * Checks a built package is safe to hand out: the manifest matches, nothing is a
 * symlink, no path escapes the package, no reference points outside it, no secret
 * pattern appears, and no client vocabulary leaked into the catalog projection.
 *
 * Prints PASS/FAIL per check and exits non-zero on any failure.
 *
 * Usage:
 *   node verify-package.js <packageDir> [<packageDir> ...]
 *   node verify-package.js dist/crecs-template-studio/*
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const targets = process.argv.slice(2);
if (!targets.length) {
  console.error('Usage: node verify-package.js <packageDir> [...]');
  process.exit(1);
}

const SECRET_PATTERNS = [
  ['google-api-key', /\bAIza[0-9A-Za-z_\-]{30,}/],
  ['bearer-token', /\bBearer\s+[A-Za-z0-9._\-]{20,}/],
  ['jwt', /\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}/],
  ['private-key-block', /-----BEGIN [A-Z ]*PRIVATE KEY-----/],
  ['aws-access-key', /\b(?:AKIA|ASIA)[0-9A-Z]{16}\b/],
  ['slack-token', /\bxox[abprs]-[0-9A-Za-z\-]{10,}/],
  ['github-token', /\bgh[pousr]_[0-9A-Za-z]{20,}/],
];

// Strings that would mean a client's own data shipped inside the package. The city
// and broker names come from the dev tenant's API vocabularies, which the projection
// builder is supposed to strip.
const CLIENT_DATA_MARKERS = [
  'Abilene', 'Abington', 'Alabaster', 'Tom Dodge', 'Max Knake',
];

// Files allowed to mention the example property, because explaining why it must not
// ship is their job.
const EXAMPLE_PROPERTY_MARKERS = ['Farmersville', 'hwy-380-fm-653'];
const EXAMPLE_ALLOWED = [
  'target-profile.example.json', 'SKILL.md', 'README.md',
  'property-template-all-widgets.build-report.json',
  'crecs-property-fields.json', 'validate.py', 'test_validate.py',
  'test_conversational.py', 'frozen-slug.json', 'PATHS.md',
  // Test fixture: it lists the example property as forbidden_literals, which is the
  // same reason target-profile.example.json is allowed to name it.
  'target-profile.test.json', 'test_popup.py',
];

const DEV_ONLY = ['node_modules', '.git', 'crecs-runtime-controls.json',
  'crecs-static-registrations.json', 'notes.manual.json'];

let anyFailed = false;

function walk(root, base = root, out = []) {
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const abs = path.join(root, entry.name);
    const rel = path.relative(base, abs).split(path.sep).join('/');
    if (entry.isSymbolicLink()) {
      out.push({ rel, abs, symlink: true });
      continue;
    }
    if (entry.isDirectory()) walk(abs, base, out);
    else out.push({ rel, abs, symlink: false });
  }
  return out;
}

function isText(rel) {
  return /\.(md|json|py|txt|yaml|yml|cfg|ini)$/i.test(rel);
}

/** List a zip's entries without unpacking it. Returns null if no tool is available. */
function listZip(zipPath) {
  const { execFileSync } = require('child_process');
  try {
    const out = execFileSync('powershell.exe', [
      '-NoProfile', '-Command',
      'Add-Type -AssemblyName System.IO.Compression.FileSystem; '
      + `$z=[System.IO.Compression.ZipFile]::OpenRead('${zipPath}'); `
      + '$z.Entries | ForEach-Object { $_.FullName }; $z.Dispose()',
    ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    return out.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
  } catch (err) {
    try {
      const out = execFileSync('unzip', ['-Z1', zipPath],
        { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
      return out.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
    } catch (err2) {
      return null;
    }
  }
}

const pad = (text, width) => String(text).padEnd(width);

for (const target of targets) {
  if (!fs.existsSync(target) || !fs.statSync(target).isDirectory()) continue;

  const name = path.basename(target);
  const checks = [];
  const check = (label, ok, detail) => {
    checks.push({ label, ok, detail });
    if (!ok) anyFailed = true;
  };

  const files = walk(target);

  // 1. no symlinks
  const symlinks = files.filter((f) => f.symlink).map((f) => f.rel);
  check('no symlinks', symlinks.length === 0, symlinks.join(', '));

  // 2. manifest matches
  const manifestPath = path.join(target, 'MANIFEST.sha256');
  if (fs.existsSync(manifestPath)) {
    const listed = new Map();
    for (const line of fs.readFileSync(manifestPath, 'utf8').split(/\r?\n/)) {
      if (!line.trim()) continue;
      const [digest, rel] = line.split('  ');
      listed.set(rel, digest);
    }
    const bad = [];
    const missing = [];
    for (const [rel, digest] of listed) {
      const abs = path.join(target, rel);
      if (!fs.existsSync(abs)) { missing.push(rel); continue; }
      if (crypto.createHash('sha256').update(fs.readFileSync(abs)).digest('hex') !== digest) {
        bad.push(rel);
      }
    }
    const unlisted = files
      .filter((f) => f.rel !== 'MANIFEST.sha256' && !listed.has(f.rel))
      .map((f) => f.rel);
    check('manifest matches', !bad.length && !missing.length && !unlisted.length,
      `${listed.size} listed, changed=${bad.length}, missing=${missing.length}, `
      + `unlisted=${unlisted.length}`
      + (unlisted.length ? ' -> ' + unlisted.slice(0, 5).join(', ') : ''));
  } else {
    check('manifest matches', false, 'MANIFEST.sha256 missing');
  }

  // 3. nothing developer-only
  const devLeak = files.filter((f) => DEV_ONLY.some((d) => f.rel.includes(d)))
    .map((f) => f.rel);
  check('no developer-only files', devLeak.length === 0, devLeak.join(', '));

  // 4. no secrets
  const secretHits = [];
  for (const file of files) {
    if (!isText(file.rel)) continue;
    const text = fs.readFileSync(file.abs, 'utf8');
    for (const [label, pattern] of SECRET_PATTERNS) {
      // The validator and its tests carry deliberately fake examples of these shapes.
      if (/validate\.py$|test_validate\.py$|verify-package\.js$|secret\.json$/.test(file.rel)) {
        continue;
      }
      if (pattern.test(text)) secretHits.push(`${file.rel} (${label})`);
    }
  }
  check('no secret-shaped strings', secretHits.length === 0, secretHits.join(', '));

  // 5. no client vocabularies
  const clientHits = [];
  for (const file of files) {
    if (!isText(file.rel)) continue;
    const text = fs.readFileSync(file.abs, 'utf8');
    for (const marker of CLIENT_DATA_MARKERS) {
      if (text.includes(marker)) clientHits.push(`${file.rel} ("${marker}")`);
    }
  }
  check('no client vocabulary data', clientHits.length === 0, clientHits.join(', '));

  // 6. the example property only appears where it is being warned about
  const exampleHits = [];
  for (const file of files) {
    if (!isText(file.rel)) continue;
    if (EXAMPLE_ALLOWED.some((allowed) => file.rel.endsWith(allowed))) continue;
    const text = fs.readFileSync(file.abs, 'utf8');
    for (const marker of EXAMPLE_PROPERTY_MARKERS) {
      if (text.includes(marker)) exampleHits.push(`${file.rel} ("${marker}")`);
    }
  }
  check('example property not frozen in', exampleHits.length === 0,
    exampleHits.join(', '));

  // 7. no reference leaves the package
  const outside = [];
  for (const file of files) {
    if (!/\.(md|json|py)$/i.test(file.rel)) continue;
    const text = fs.readFileSync(file.abs, 'utf8');
    for (const match of text.matchAll(/(?:^|["'\s(])((?:\.\.\/){2,}[\w./-]+)/g)) {
      outside.push(`${file.rel} -> ${match[1]}`);
    }
    for (const match of text.matchAll(/["']([A-Za-z]:[\\/][^"']{3,})["']/g)) {
      outside.push(`${file.rel} -> absolute path ${match[1].slice(0, 60)}`);
    }
  }
  check('no path escapes the package', outside.length === 0,
    outside.slice(0, 6).join('; '));

  // 8. the skill's own entry points exist — inside the zip, when the package is one
  const zips = files.filter((f) => f.rel.endsWith('.zip'));
  let names = files.map((f) => f.rel);
  let where = 'package';
  if (zips.length === 1 && files.length <= 3) {
    const entries = listZip(zips[0].abs);
    if (entries === null) {
      check('skill entry points present', false,
        'could not read ' + zips[0].rel + ' (needs PowerShell or unzip)');
      names = [];
    } else {
      names = entries;
      where = 'zip';
    }
  }
  if (names.length) {
    const hasSkill = names.some((n) => n.endsWith('SKILL.md'));
    const hasCli = names.some((n) => n.endsWith('scripts/crecs_template.py'));
    const hasProjection = names.some(
      (n) => n.endsWith('references/catalog/crecs-controls.min.json')
    );
    const rootIsSkillFolder = where !== 'zip'
      || names.every((n) => n.startsWith('crecs-property-template/'));
    check('skill entry points present (' + where + ')',
      hasSkill && hasCli && hasProjection && rootIsSkillFolder,
      `SKILL.md=${hasSkill} cli=${hasCli} projection=${hasProjection}`
      + (where === 'zip' ? ` zipRootIsSkillFolder=${rootIsSkillFolder}` : ''));
  }

  // 9. references resolve inside the package
  const refMisses = [];
  const present = new Set(files.map((f) => f.rel));
  for (const file of files) {
    if (!file.rel.endsWith('.md')) continue;
    const dir = path.posix.dirname(file.rel);
    const text = fs.readFileSync(file.abs, 'utf8');
    for (const match of text.matchAll(/\]\((?!https?:)([^)#]+)\)/g)) {
      const raw = match[1].trim();
      if (!raw || raw.startsWith('/')) continue;
      const resolved = path.posix.normalize(path.posix.join(dir, raw));
      if (resolved.startsWith('..')) { refMisses.push(`${file.rel} -> ${raw}`); continue; }
      if (!present.has(resolved) && !present.has(resolved + '/INDEX.md')) {
        const isDir = [...present].some((p) => p.startsWith(resolved + '/'));
        if (!isDir) refMisses.push(`${file.rel} -> ${raw}`);
      }
    }
  }
  check('markdown links resolve inside the package', refMisses.length === 0,
    refMisses.slice(0, 6).join('; '));

  // 10. an install guide
  check('INSTALL.md present',
    files.some((f) => f.rel === 'INSTALL.md' || f.rel.endsWith('/INSTALL.md')), '');

  console.log('== ' + name + ' (' + files.length + ' files)');
  for (const entry of checks) {
    console.log('  ' + (entry.ok ? 'PASS' : 'FAIL') + '  '
      + pad(entry.label, 46) + (entry.detail || ''));
  }
  console.log('');
}

process.exit(anyFailed ? 1 : 0);
