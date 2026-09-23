#!/usr/bin/env node
/**
 * Build the ZIPs that go to a client, one per assistant surface.
 *
 * This repository is private, which makes it a place to develop and not a place to
 * distribute from: a private repository gates its own releases, so a client would need
 * a GitHub account and collaborator access, and would then be reading proprietary
 * source. What a client receives is a built package.
 *
 * The hazard this guards against is staleness. `dist/` is generated from
 * `crecs-property-template/`, and a ZIP built from a `dist/` that no longer matches the
 * skill delivers something nobody tested — silently, because the archive is perfectly
 * valid. So this checks two things before packing anything:
 *
 *   1. every package still matches its own MANIFEST.sha256
 *   2. the packaged skill still matches the skill in this repository
 *
 * and refuses on either, naming what to do.
 *
 * Deterministic: entries sorted, a fixed timestamp, fixed compression. The same tree
 * gives byte-identical archives, so the checksums it writes to SHA256SUMS.txt can be
 * published beside the download and checked by whoever receives it.
 *
 * Usage:
 *   node tools/build-release-zips.js [--out <dir>] [--only <surface>]
 *
 * No dependencies. The archives are written directly, deflate through zlib.
 */

'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const ROOT = path.resolve(__dirname, '..');
const DIST = path.join(ROOT, 'dist');
const SKILL = path.join(ROOT, 'crecs-property-template');

/** The surfaces, and where the skill sits inside each package. */
const SURFACES = {
  'claude-code-skill': 'crecs-property-template',
  'claude-code-plugin': 'skills/crecs-property-template',
  'claude-web': null,                       // a zip of the skill; nothing to compare
  'codex-skill': 'crecs-property-template',
  'chatgpt-skill': 'crecs-property-template',
  'chatgpt-file-kit': '.',                  // loose files, the skill at the package root
};

/**
 * Surfaces whose deliverable is an archive the package already carries, handed over
 * untouched. claude.ai validates the upload's own shape, so anything wrapped around it
 * is rejected; INSTALL.md is written beside the archive instead.
 */
const UPLOADED_AS_IS = {
  'claude-web': 'crecs-property-template.zip',
};

const SKIP_NAMES = new Set(['__pycache__', '.DS_Store', 'Thumbs.db', 'desktop.ini']);

function fail(message) {
  console.error('\nrefused: ' + message + '\n');
  process.exit(1);
}

function usage() {
  console.log([
    '',
    'Build the client delivery ZIPs, one per assistant surface.',
    '',
    '  node tools/build-release-zips.js [--out <dir>] [--only <surface>]',
    '',
    '  --out <dir>      where to write (default: ./release)',
    '  --only <surface> build one: ' + Object.keys(SURFACES).join(', '),
    '',
    'It refuses if a package no longer matches its own MANIFEST.sha256, or if the',
    'packaged skill has drifted from crecs-property-template/ — a stale package ships',
    'a client something nobody tested, and looks perfectly fine doing it.',
    '',
  ].join('\n'));
}

function parseArgs(argv) {
  const out = { out: path.join(ROOT, 'release'), only: null, help: false };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--help' || argv[i] === '-h') out.help = true;
    else if (argv[i] === '--out') out.out = argv[++i];
    else if (argv[i] === '--only') out.only = argv[++i];
    else fail('unknown argument ' + argv[i]);
  }
  return out;
}

function version() {
  const init = path.join(SKILL, 'scripts', 'crecs', '__init__.py');
  if (!fs.existsSync(init)) fail('the skill is missing: ' + init);
  const m = fs.readFileSync(init, 'utf8').match(/__version__\s*=\s*"([^"]+)"/);
  if (!m) fail('no __version__ in scripts/crecs/__init__.py');
  return m[1];
}

/** Every file under `dir`, relative and forward-slashed, skipping the droppings. */
function walk(dir, base, acc) {
  base = base || dir;
  acc = acc || [];
  for (const name of fs.readdirSync(dir).sort()) {
    if (SKIP_NAMES.has(name)) continue;
    const abs = path.join(dir, name);
    if (fs.statSync(abs).isDirectory()) walk(abs, base, acc);
    else acc.push(path.relative(base, abs).split(path.sep).join('/'));
  }
  return acc;
}

const sha256 = (buf) => crypto.createHash('sha256').update(buf).digest('hex');

/** Check a package against the MANIFEST.sha256 it carries. */
function checkManifest(pkgDir, surface) {
  const manifestPath = path.join(pkgDir, 'MANIFEST.sha256');
  if (!fs.existsSync(manifestPath)) fail(surface + ' has no MANIFEST.sha256');
  for (const line of fs.readFileSync(manifestPath, 'utf8').split('\n')) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const at = trimmed.indexOf('  ');
    const expected = trimmed.slice(0, at);
    const rel = trimmed.slice(at + 2);
    const abs = path.join(pkgDir, rel.split('/').join(path.sep));
    if (!fs.existsSync(abs)) {
      fail(surface + ': ' + rel + ' is listed in MANIFEST.sha256 and is not there.');
    }
    if (sha256(fs.readFileSync(abs)) !== expected) {
      fail(surface + ': ' + rel + ' does not match MANIFEST.sha256. The package has been '
        + 'edited by hand or is half rebuilt; run '
        + '`node tools/build-skill-packages.js crecs-property-template dist` and try again.');
    }
  }
}

/** Check the packaged skill still matches the skill in this repository. */
function checkFresh(pkgDir, surface, inner) {
  if (inner === null) return; // claude-web ships a zip; its manifest already covers it
  const packagedRoot = inner === '.' ? pkgDir : path.join(pkgDir, inner.split('/').join(path.sep));
  if (!fs.existsSync(packagedRoot)) fail(surface + ': expected the skill at ' + inner);

  for (const rel of walk(SKILL)) {
    // The file kit carries a subset on purpose, so only compare what it has.
    const packaged = path.join(packagedRoot, rel.split('/').join(path.sep));
    if (inner === '.' && !fs.existsSync(packaged)) continue;
    if (!fs.existsSync(packaged)) {
      fail(surface + ' is stale: it is missing ' + rel + '. Rebuild with '
        + '`node tools/build-skill-packages.js crecs-property-template dist`.');
    }
    if (sha256(fs.readFileSync(packaged)) !== sha256(fs.readFileSync(path.join(SKILL, rel)))) {
      fail(surface + ' is stale: ' + rel + ' differs from crecs-property-template/. '
        + 'Rebuild with `node tools/build-skill-packages.js crecs-property-template dist`.');
    }
  }
}

// ---------------------------------------------------------------------------
// a small deterministic ZIP writer
// ---------------------------------------------------------------------------

const CRC_TABLE = (() => {
  const t = new Int32Array(256);
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c;
  }
  return t;
})();

function crc32(buf) {
  let c = -1;
  for (let i = 0; i < buf.length; i += 1) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ -1) >>> 0;
}

// Fixed 1980-01-01: real mtimes would make two builds of the same tree differ, and then
// a published checksum proves nothing.
const DOS_TIME = 0;
const DOS_DATE = 33;

function zipOf(files) {
  const locals = [];
  const central = [];
  let offset = 0;

  for (const f of files) {
    const name = Buffer.from(f.name, 'utf8');
    const deflated = zlib.deflateRawSync(f.body, { level: 9 });
    const store = deflated.length >= f.body.length;
    const data = store ? f.body : deflated;
    const method = store ? 0 : 8;
    const sum = crc32(f.body);

    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50, 0);
    local.writeUInt16LE(20, 4);
    local.writeUInt16LE(0, 6);
    local.writeUInt16LE(method, 8);
    local.writeUInt16LE(DOS_TIME, 10);
    local.writeUInt16LE(DOS_DATE, 12);
    local.writeUInt32LE(sum, 14);
    local.writeUInt32LE(data.length, 18);
    local.writeUInt32LE(f.body.length, 22);
    local.writeUInt16LE(name.length, 26);
    local.writeUInt16LE(0, 28);
    locals.push(local, name, data);

    const head = Buffer.alloc(46);
    head.writeUInt32LE(0x02014b50, 0);
    head.writeUInt16LE(20, 4);
    head.writeUInt16LE(20, 6);
    head.writeUInt16LE(0, 8);
    head.writeUInt16LE(method, 10);
    head.writeUInt16LE(DOS_TIME, 12);
    head.writeUInt16LE(DOS_DATE, 14);
    head.writeUInt32LE(sum, 16);
    head.writeUInt32LE(data.length, 20);
    head.writeUInt32LE(f.body.length, 24);
    head.writeUInt16LE(name.length, 28);
    head.writeUInt16LE(0, 30);
    head.writeUInt16LE(0, 32);
    head.writeUInt16LE(0, 34);
    head.writeUInt16LE(0, 36);
    head.writeUInt32LE(0o644 << 16, 38);
    head.writeUInt32LE(offset, 42);
    central.push(head, name);

    offset += 30 + name.length + data.length;
  }

  const localBuf = Buffer.concat(locals);
  const centralBuf = Buffer.concat(central);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(0, 4);
  end.writeUInt16LE(0, 6);
  end.writeUInt16LE(files.length, 8);
  end.writeUInt16LE(files.length, 10);
  end.writeUInt32LE(centralBuf.length, 12);
  end.writeUInt32LE(localBuf.length, 16);
  end.writeUInt16LE(0, 20);

  return Buffer.concat([localBuf, centralBuf, end]);
}

// ---------------------------------------------------------------------------

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) { usage(); process.exit(0); }

  if (!fs.existsSync(DIST)) fail('dist/ is missing; nothing has been packaged yet');
  if (args.only && !Object.prototype.hasOwnProperty.call(SURFACES, args.only)) {
    fail('unknown surface ' + args.only + '. The surfaces are: '
      + Object.keys(SURFACES).join(', '));
  }

  const v = version();
  const surfaces = args.only ? [args.only] : Object.keys(SURFACES);
  const outDir = path.resolve(args.out);

  // Check everything before writing anything: a half-built release directory is worse
  // than none, because the good archives look shippable.
  const built = [];
  for (const surface of surfaces) {
    const pkgDir = path.join(DIST, surface);
    if (!fs.existsSync(pkgDir)) fail('dist/' + surface + ' is missing');
    checkManifest(pkgDir, surface);
    checkFresh(pkgDir, surface, SURFACES[surface]);
  }

  fs.mkdirSync(outDir, { recursive: true });
  for (const surface of surfaces) {
    const pkgDir = path.join(DIST, surface);
    const outName = 'crecs-property-template-' + v + '-' + surface + '.zip';
    let archive;
    let count;

    if (UPLOADED_AS_IS[surface]) {
      // claude.ai takes the archive exactly as given: one top-level folder with
      // SKILL.md directly inside it. Zipping the package directory would wrap that
      // archive in another one and add INSTALL.md and MANIFEST.sha256 as extra roots,
      // and the uploader answers "All files must be inside the top-level folder". So
      // the deliverable IS the inner archive, copied through untouched, and the
      // instructions travel beside it instead of inside.
      const inner = path.join(pkgDir, UPLOADED_AS_IS[surface]);
      if (!fs.existsSync(inner)) fail(surface + ': expected ' + UPLOADED_AS_IS[surface]);
      archive = fs.readFileSync(inner);
      count = null;
      const notes = path.join(pkgDir, 'INSTALL.md');
      if (fs.existsSync(notes)) {
        fs.copyFileSync(notes, path.join(outDir,
          'crecs-property-template-' + v + '-' + surface + '-INSTALL.md'));
      }
    } else {
      const names = walk(pkgDir).sort();
      if (!names.length) fail('dist/' + surface + ' is empty');
      const files = names.map((n) => ({
        name: n,
        body: fs.readFileSync(path.join(pkgDir, n.split('/').join(path.sep))),
      }));
      archive = zipOf(files);
      count = files.length;
    }

    fs.writeFileSync(path.join(outDir, outName), archive);
    built.push({ surface, name: outName, files: count, bytes: archive.length, sha: sha256(archive) });
  }

  fs.writeFileSync(
    path.join(outDir, 'SHA256SUMS.txt'),
    built.map((b) => b.sha + '  ' + b.name).join('\n') + '\n'
  );

  console.log('');
  console.log('  version  ' + v);
  console.log('  out      ' + outDir);
  console.log('');
  for (const b of built) {
    const what = b.files === null ? ' upload  ' : String(b.files).padStart(4) + ' files  ';
    console.log('  ' + b.surface.padEnd(20) + what
      + (b.bytes / 1024).toFixed(0).padStart(5) + ' KB  sha256 ' + b.sha.slice(0, 16) + '…');
  }
  console.log('');
  console.log('  checksums written to SHA256SUMS.txt — publish it beside the downloads.');
  console.log('  each archive carries its own INSTALL.md.');
  console.log('');
}

main();
