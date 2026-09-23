#!/usr/bin/env node
/**
 * Contract for the client-delivery ZIP builder.
 *
 * The skill lives in a private repository, which is a place to develop and not a place
 * to distribute from: a private repo gates its own releases, so a client would need a
 * GitHub account and collaborator access, and would then be reading proprietary source.
 * What goes to a client is a built package.
 *
 * The risk this guards is staleness. `dist/` is generated, and a ZIP built from a
 * `dist/` that no longer matches the skill ships a client something that was never
 * tested — silently, because the archive is perfectly valid. So the builder's job is to
 * check before it packs.
 *
 * Run: node tools/tests/build-release-zips.test.js
 */

'use strict';

const assert = require('assert');
const child = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const SCRIPT = path.join(ROOT, 'tools', 'build-release-zips.js');

let passed = 0;
const failures = [];

function test(name, fn) {
  try {
    fn();
    passed += 1;
    console.log('  PASS  ' + name);
  } catch (err) {
    failures.push({ name, err });
    console.log('  FAIL  ' + name + '\n          ' + (err && err.message));
  }
}

function run(args) {
  const r = child.spawnSync(process.execPath, [SCRIPT].concat(args), {
    cwd: ROOT, encoding: 'utf8',
  });
  return { code: r.status, stdout: r.stdout || '', stderr: r.stderr || '' };
}

function entries(zipPath) {
  const buf = fs.readFileSync(zipPath);
  let eocd = buf.length - 22;
  while (eocd >= 0 && buf.readUInt32LE(eocd) !== 0x06054b50) eocd -= 1;
  assert.ok(eocd >= 0, 'not a ZIP: ' + zipPath);
  const count = buf.readUInt16LE(eocd + 10);
  let at = buf.readUInt32LE(eocd + 16);
  const names = [];
  for (let i = 0; i < count; i += 1) {
    const nameLen = buf.readUInt16LE(at + 28);
    const extraLen = buf.readUInt16LE(at + 30);
    const commentLen = buf.readUInt16LE(at + 32);
    names.push(buf.toString('utf8', at + 46, at + 46 + nameLen));
    at += 46 + nameLen + extraLen + commentLen;
  }
  return names;
}

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'crecs-zips-'));
const rmrf = (p) => fs.rmSync(p, { recursive: true, force: true });

// ---------------------------------------------------------------------------

console.log('\nclient delivery ZIPs\n');

test('the script exists and explains itself', () => {
  assert.ok(fs.existsSync(SCRIPT), 'tools/build-release-zips.js is missing');
  const r = run(['--help']);
  assert.strictEqual(r.code, 0, r.stderr);
  assert.ok(/--only/.test(r.stdout), '--help does not mention --only');
});

test('it builds one archive per surface', () => {
  const out = tmp();
  const r = run(['--out', out]);
  assert.strictEqual(r.code, 0, r.stdout + r.stderr);
  const zips = fs.readdirSync(out).filter((f) => f.endsWith('.zip')).sort();
  assert.strictEqual(zips.length, 6, 'expected six archives, got ' + zips.join(', '));
  for (const surface of ['claude-code-skill', 'claude-code-plugin', 'claude-web',
    'codex-skill', 'chatgpt-skill', 'chatgpt-file-kit']) {
    assert.ok(zips.some((z) => z.includes(surface)), 'no archive for ' + surface);
  }
  rmrf(out);
});

test('every archive carries the version in its name', () => {
  const out = tmp();
  run(['--out', out]);
  const version = fs.readFileSync(
    path.join(ROOT, 'crecs-property-template', 'scripts', 'crecs', '__init__.py'), 'utf8'
  ).match(/__version__\s*=\s*"([^"]+)"/)[1];
  for (const z of fs.readdirSync(out).filter((f) => f.endsWith('.zip'))) {
    assert.ok(z.includes(version), z + ' does not carry the version ' + version);
  }
  rmrf(out);
});

test('an archive holds its package and nothing above it', () => {
  // A client unzips and finds the package; they should not find a stray parent folder
  // or a sibling surface's files.
  const out = tmp();
  run(['--out', out, '--only', 'claude-code-skill']);
  const zip = path.join(out, fs.readdirSync(out).find((f) => f.endsWith('.zip')));
  const names = entries(zip);
  assert.ok(names.includes('INSTALL.md'), 'the install instructions are missing');
  assert.ok(names.some((n) => n.startsWith('crecs-property-template/')), 'no skill folder');
  assert.ok(!names.some((n) => n.startsWith('dist/') || n.startsWith('tools/')),
    'the archive carries repository paths');
  rmrf(out);
});

test('--only builds just that surface', () => {
  const out = tmp();
  const r = run(['--out', out, '--only', 'claude-web']);
  assert.strictEqual(r.code, 0, r.stderr);
  const zips = fs.readdirSync(out).filter((f) => f.endsWith('.zip'));
  assert.strictEqual(zips.length, 1, 'expected one archive');
  assert.ok(zips[0].includes('claude-web'));
  rmrf(out);
});

test('an unknown surface is refused, and names the real ones', () => {
  const out = tmp();
  const r = run(['--out', out, '--only', 'gemini']);
  assert.notStrictEqual(r.code, 0);
  assert.ok(/claude-code-skill/.test(r.stdout + r.stderr), 'the refusal does not list the surfaces');
  rmrf(out);
});

test('a package that fails its own manifest stops the build', () => {
  // Each package ships a MANIFEST.sha256. If a file inside it has drifted, the package
  // is not what it claims and must not reach a client.
  const out = tmp();
  const victim = path.join(ROOT, 'dist', 'claude-code-skill', 'INSTALL.md');
  const original = fs.readFileSync(victim);
  fs.writeFileSync(victim, Buffer.concat([original, Buffer.from('\ntampered\n')]));
  try {
    const r = run(['--out', out, '--only', 'claude-code-skill']);
    assert.notStrictEqual(r.code, 0, 'a tampered package should have been refused');
    assert.ok(/manifest|INSTALL\.md/i.test(r.stdout + r.stderr), 'the refusal is not specific');
    assert.strictEqual(fs.readdirSync(out).filter((f) => f.endsWith('.zip')).length, 0,
      'an archive was written despite the refusal');
  } finally {
    fs.writeFileSync(victim, original);
    rmrf(out);
  }
});

test('packages stale against the skill source stop the build', () => {
  // The real hazard: dist/ is generated, and shipping a ZIP built from a stale dist/
  // delivers something that was never tested, with no outward sign.
  const out = tmp();
  const victim = path.join(ROOT, 'crecs-property-template', 'SKILL.md');
  const original = fs.readFileSync(victim);
  fs.writeFileSync(victim, Buffer.concat([original, Buffer.from('\n<!-- edited -->\n')]));
  try {
    const r = run(['--out', out]);
    assert.notStrictEqual(r.code, 0, 'a stale dist/ should have been refused');
    assert.ok(/stale|rebuild|build-skill-packages/i.test(r.stdout + r.stderr),
      'the refusal does not say to rebuild: ' + (r.stdout + r.stderr).slice(0, 200));
  } finally {
    fs.writeFileSync(victim, original);
    rmrf(out);
  }
});

test('the claude.ai archive is the upload itself, not a wrapper around it', () => {
  // A client uploading to claude.ai gets this back when the shape is wrong:
  //   "All files must be inside the top-level folder"
  //   ".zip or .skill file must include a SKILL.md file"
  // The uploader takes the archive as-is: one top-level folder, SKILL.md inside it. The
  // first version of this script zipped every package directory, which for claude-web
  // produced a zip containing a zip, and INSTALL.md and MANIFEST.sha256 beside it as
  // extra roots. Neither of those can be uploaded.
  const out = tmp();
  run(['--out', out, '--only', 'claude-web']);
  const zip = path.join(out, fs.readdirSync(out).find((f) => f.endsWith('.zip')));
  const names = entries(zip);

  const roots = new Set(names.map((n) => n.split('/')[0]));
  assert.strictEqual(roots.size, 1, 'claude.ai needs exactly one top-level folder, got: '
    + [...roots].join(', '));
  assert.ok(names.includes('crecs-property-template/SKILL.md'),
    'SKILL.md is not directly inside the top-level folder');
  assert.ok(!names.some((n) => n.endsWith('.zip')), 'the archive contains another archive');
  assert.ok(!names.includes('INSTALL.md'), 'INSTALL.md is a second root and breaks the upload');
  rmrf(out);
});

test('the install instructions still reach the client for claude.ai', () => {
  // They cannot travel inside that archive, so they travel beside it.
  const out = tmp();
  run(['--out', out, '--only', 'claude-web']);
  const files = fs.readdirSync(out);
  assert.ok(files.some((f) => /claude-web.*INSTALL\.md$/.test(f)),
    'no INSTALL.md alongside the claude.ai archive: ' + files.join(', '));
  rmrf(out);
});

test('it writes checksums a client can verify against', () => {
  const out = tmp();
  run(['--out', out]);
  const sums = path.join(out, 'SHA256SUMS.txt');
  assert.ok(fs.existsSync(sums), 'no SHA256SUMS.txt');
  const lines = fs.readFileSync(sums, 'utf8').trim().split('\n');
  assert.strictEqual(lines.length, 6, 'expected six checksums');
  for (const line of lines) {
    const [hash, name] = line.split(/\s+/);
    assert.ok(/^[0-9a-f]{64}$/.test(hash), 'not a sha256: ' + line);
    assert.ok(fs.existsSync(path.join(out, name)), 'checksum names a missing file: ' + name);
    const actual = require('crypto').createHash('sha256')
      .update(fs.readFileSync(path.join(out, name))).digest('hex');
    assert.strictEqual(actual, hash, 'the checksum does not match ' + name);
  }
  rmrf(out);
});

test('the same tree twice gives byte-identical archives', () => {
  const a = tmp();
  const b = tmp();
  run(['--out', a, '--only', 'codex-skill']);
  run(['--out', b, '--only', 'codex-skill']);
  const fa = fs.readFileSync(path.join(a, fs.readdirSync(a).find((f) => f.endsWith('.zip'))));
  const fb = fs.readFileSync(path.join(b, fs.readdirSync(b).find((f) => f.endsWith('.zip'))));
  assert.ok(fa.equals(fb), 'two builds of the same package differ');
  rmrf(a); rmrf(b);
});

test('no bytecode reaches a client', () => {
  const out = tmp();
  run(['--out', out]);
  for (const z of fs.readdirSync(out).filter((f) => f.endsWith('.zip'))) {
    const names = entries(path.join(out, z));
    assert.ok(!names.some((n) => n.includes('__pycache__') || n.endsWith('.pyc')),
      z + ' carries compiled bytecode');
  }
  rmrf(out);
});

test('it says what it built and what to hand over', () => {
  const out = tmp();
  const r = run(['--out', out]);
  assert.ok(/sha256/i.test(r.stdout), 'no checksums in the output');
  assert.ok(/claude-web/.test(r.stdout), 'the surfaces are not listed');
  rmrf(out);
});

console.log('\n' + passed + ' passed, ' + failures.length + ' failed\n');
process.exit(failures.length === 0 ? 0 : 1);
