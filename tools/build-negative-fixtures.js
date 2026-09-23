/**
 * CRECS Template Studio — negative fixture builder (developer tool).
 *
 * Derives assets/fixtures/negative/*.json from one valid document, each file breaking
 * exactly one rule. Generated rather than hand-written so they stay consistent with
 * the valid fixture they come from.
 *
 * Usage:
 *   node build-negative-fixtures.js <skillRoot>
 */
const fs = require('fs');
const path = require('path');

const skillRoot = process.argv[2];
if (!skillRoot) {
  console.error('Usage: node build-negative-fixtures.js <skillRoot>');
  process.exit(1);
}

const fixtures = path.join(skillRoot, 'assets', 'fixtures');
const outDir = path.join(fixtures, 'negative');
fs.mkdirSync(outDir, { recursive: true });

const VALID = JSON.parse(
  fs.readFileSync(path.join(fixtures, 'dynamic-field-data.json'), 'utf8')
);

const clone = () => JSON.parse(JSON.stringify(VALID));

function column(doc) {
  return doc.content[0].elements[0];
}
function widget(doc, type) {
  return column(doc).elements.find((e) => e.widgetType === type);
}
function addWidget(doc, id, type, settings) {
  column(doc).elements.push({
    id, elType: 'widget', widgetType: type, isInner: false,
    settings: settings || {}, elements: [],
  });
}

const cases = {};

// E-ID-DUPLICATE
cases['duplicate-ids.json'] = () => {
  const doc = clone();
  column(doc).elements[1].id = column(doc).elements[0].id;
  return doc;
};

// E-CONTROL-UNKNOWN
cases['invented-key.json'] = () => {
  const doc = clone();
  addWidget(doc, 'f1b0001', 'crecs_property_fields', {
    layout_type: 'two_column',
    card_neon_glow_intensity: 7,
  });
  return doc;
};

// E-BINDING-CORRUPT
cases['corrupt-binding.json'] = () => {
  const doc = clone();
  addWidget(doc, 'f1b0002', 'heading', {
    title: 'Add Your Heading Text Here',
    __dynamic__: { title: '[elementor-tag name=crecs-property settings=%7Bnope' },
  });
  return doc;
};

// E-BINDING-PARAM (the documented lower-case spelling that does not exist)
cases['wrong-param-case.json'] = () => {
  const doc = clone();
  addWidget(doc, 'f1b0003', 'heading', {
    title: 'Add Your Heading Text Here',
    __dynamic__: {
      title: '[elementor-tag id="c9ca4f5" name="crecs-property" '
        + 'settings="%7B%22param_name%22%3A%22size-available_sf%22%7D"]',
    },
  });
  return doc;
};

// E-FROZEN-SLUG (needs a profile listing the example slug)
cases['frozen-slug.json'] = () => {
  const doc = clone();
  widget(doc, 'crecs_property_data').settings.slug =
    'hwy-380-fm-653-farmersville-tx-75442';
  return doc;
};

// E-NESTING: a widget hanging directly off a section
cases['invalid-nesting.json'] = () => {
  const doc = clone();
  doc.content[0].elements.push({
    id: 'f1b0004', elType: 'widget', widgetType: 'crecs_property_rates',
    isInner: false, settings: {}, elements: [],
  });
  return doc;
};

// E-ELEMENT-MODEL
cases['container-model.json'] = () => {
  const doc = clone();
  doc.content.push({
    id: 'f1b0005', elType: 'container', settings: { flex_direction: 'row' },
    elements: [],
  });
  return doc;
};

// E-SECRET
cases['secret.json'] = () => {
  const doc = clone();
  addWidget(doc, 'f1b0006', 'crecs_property_fields', {
    layout_type: 'list',
    card_color: 'AIzaSyD0000000000000000000000000000000000',
  });
  return doc;
};

// E-RESPONSIVE-UNSUPPORTED
cases['dead-device-variant.json'] = () => {
  const doc = clone();
  addWidget(doc, 'f1b0007', 'crecs_property_fields', {
    layout_type: 'list',
    card_color_mobile: '#ffffff',
  });
  return doc;
};

// E-CARDINALITY
cases['two-maps.json'] = () => {
  const doc = clone();
  addWidget(doc, 'f1b0008', 'crecs_property_map', { map_type: 'roadmap' });
  addWidget(doc, 'f1b0009', 'crecs_property_map', { map_type: 'satellite' });
  return doc;
};

// E-LOADER-ORDER
cases['loader-not-first.json'] = () => {
  const doc = clone();
  const elements = column(doc).elements;
  const loader = elements.shift();
  elements.push(loader);
  return doc;
};

// E-CONTROL-OPTION
cases['bad-option-value.json'] = () => {
  const doc = clone();
  addWidget(doc, 'f1b0010', 'crecs_property_fields', { layout_type: 'three_column' });
  return doc;
};

// E-REPEATER-SHAPE
cases['repeater-without-id.json'] = () => {
  const doc = clone();
  addWidget(doc, 'f1b0011', 'crecs_property_fields', {
    layout_type: 'list',
    pa_condition_repeater: [{ pa_condition_key: 'post' }],
  });
  return doc;
};

const written = [];
for (const [name, build] of Object.entries(cases)) {
  const payload = build();
  payload.title = 'Negative fixture — ' + name.replace(/\.json$/, '');
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(payload, null, 2) + '\n');
  written.push(name);
}

// Not JSON at all.
fs.writeFileSync(
  path.join(outDir, 'malformed.json'),
  '{ "content": [ { "elType": "section", "elements": [ ] }, \n'
  + '  // Elementor exports carry no comments, and a trailing comma is not JSON\n'
  + '] ,\n'
);
written.push('malformed.json');

fs.writeFileSync(
  path.join(outDir, 'README.md'),
  '# Negative fixtures\n\nGenerated by `tools/crecs-template-studio/'
  + 'build-negative-fixtures.js` from `../dynamic-field-data.json`. Each file breaks '
  + 'exactly one rule; see `../README.md` for the table of expected findings.\n\n'
  + 'Do not edit by hand — regenerate.\n'
);

console.log('wrote %d negative fixtures to %s',
  written.length, path.relative(process.cwd(), outDir));
console.log('  ' + written.sort().join('\n  '));
