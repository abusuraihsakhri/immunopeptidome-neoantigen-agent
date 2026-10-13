'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function setup() {
  const elements = {};
  const context = {
    document: { getElementById(id) {
      return elements[id] ??= {addEventListener() {}, disabled: false, dataset: {}, textContent: '', value: 'local'};
    }},
    location: {hostname: 'example.github.io', protocol: 'https:'},
    URL, Blob, setTimeout, console,
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'web', 'app.js'), 'utf8'), context);
  return {context, elements, evaluate(code) { return vm.runInContext(code, context); }};
}

test('local rules classify routine, elevated and critical', () => {
  const {evaluate} = setup();
  const caseFor = (primary, secondary, flag, descriptor = 'NOMINAL') =>
    evaluate(`evaluate(validate({task_id:'EXAMPLE',target_identifier:'TARGET',primary_metric:${primary},secondary_metric:${secondary},is_critical_flag:'${flag}',status_descriptor:'${descriptor}'}))`);
  assert.equal(caseFor(1, 2, 'False').overall_urgency, 'ROUTINE');
  assert.equal(caseFor(26, 2, 'False').overall_urgency, 'ELEVATED_RISK');
  assert.equal(caseFor(1, 13, 'False').overall_urgency, 'ELEVATED_RISK');
  assert.equal(caseFor(1, 2, 'True').overall_urgency, 'CRITICAL_STAT_PANIC');
  assert.equal(caseFor(1, 2, 'False', 'ANOMALY').total_alerts, 1);
});

test('malformed and sensitive inputs fail safely', () => {
  const {evaluate} = setup();
  assert.throws(() => evaluate("validate({task_id:'T',target_identifier:'TARGET',primary_metric:'NaN',secondary_metric:'1',status_descriptor:'NOMINAL'})"));
  assert.throws(() => evaluate("validate({task_id:'someone@example.com',target_identifier:'TARGET',primary_metric:'1',secondary_metric:'1',status_descriptor:'NOMINAL'})"));
  assert.throws(() => evaluate("validate({task_id:'T',target_identifier:'TARGET',primary_metric:'1',secondary_metric:'1',status_descriptor:'NOMINAL',is_critical_flag:'maybe'})"));
});

test('CSV parser handles quotes and exported CSV resists formula injection', () => {
  const {evaluate} = setup();
  const rows = evaluate(`parseCsv('id,text\\n"x,y","z""w"\\n')`);
  assert.equal(rows[1][0], 'x,y');
  assert.equal(rows[1][1], 'z"w');
  assert.equal(evaluate("csvEscape('=1+2')"), '"\'=1+2"');
});

test('static Pages instance cannot select a nonexistent backend', () => {
  const {elements} = setup();
  assert.equal(elements['api-mode'].disabled, true);
});
