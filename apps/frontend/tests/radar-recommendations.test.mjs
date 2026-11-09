import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { build } from 'esbuild';

const { outputFiles } = await build({
  stdin: { contents: `export * from '../../packages/shared/radar';
    export { DEFAULT_FEATURES } from '../../packages/shared/constants';
    export { generateInterventions } from './src/utils/recommendations';`, resolveDir: process.cwd() },
  bundle: true, write: false, format: 'esm', platform: 'node',
});
const { calculateRadar, RADAR_REFERENCE, DEFAULT_FEATURES, generateInterventions, radarAppearance } =
  await import(`data:text/javascript;base64,${Buffer.from(outputFiles[0].text).toString('base64')}`);
const cases = JSON.parse(await readFile('../../packages/shared/constants/radar-cases.json', 'utf8'));

for (const fixture of cases) test(`shared radar contract: ${fixture.name}`, () => {
  const dimensions = calculateRadar(fixture.features);
  assert.deepEqual(dimensions.map(d => d.reference_score), fixture.scores);
  assert.ok(dimensions.every(d => !('percentile' in d)));
  assert.equal(RADAR_REFERENCE.status, 'illustrative_unvalidated');
});

test('nonfinite and boolean observations stay unknown', () => {
  for (const value of [Infinity, NaN, true]) {
    assert.equal(calculateRadar({ total_clicks_to_t: value })[0].reference_score, null);
  }
});

const ids = features => generateInterventions({ ...DEFAULT_FEATURES, ...features }, true, 0.7).map(s => s.id);
test('heuristic activity and submission thresholds retain strict boundaries', () => {
  assert.ok(!ids({ days_since_last_activity: 13 }).includes('high-inactivity'));
  assert.ok(ids({ days_since_last_activity: 14 }).includes('high-inactivity'));
  assert.ok(!ids({ active_day_ratio: 0.35 }).includes('low-active-ratio'));
  assert.ok(ids({ active_day_ratio: 0.349 }).includes('low-active-ratio'));
  assert.ok(!ids({ submission_rate: 0.6, late_submissions_to_t: 1 }).includes('late-submission'));
  assert.ok(ids({ submission_rate: 0.599 }).includes('late-submission'));
  assert.ok(ids({ submission_rate: 0.6, late_submissions_to_t: 2 }).includes('late-submission'));
  assert.ok(!ids({ clicks_recent_7: 30, clicks_recent_30: 300 }).includes('drop-recent'));
  assert.ok(ids({ clicks_recent_7: 29, clicks_recent_30: 300 }).includes('drop-recent'));
});

test('no submissions triggers verification and inconsistent data yields no suggestions', () => {
  assert.ok(ids({ assessments_submitted_to_t: 0, late_submissions_to_t: 0 }).includes('no-submission'));
  assert.deepEqual(ids({ assessments_submitted_to_t: 0, late_submissions_to_t: 1 }), []);
  assert.deepEqual(ids({ active_day_ratio: NaN }), []);
});

test('OULAD credit values never trigger an HUIT overload claim', () => {
  for (const credits of [3, 60, 90, 120]) {
    assert.ok(!ids({ studied_credits: credits }).includes('credit-overload'));
  }
});

test('below-threshold branch describes model status without claiming good engagement', () => {
  const low = generateInterventions(DEFAULT_FEATURES, false, 0.299);
  const watch = generateInterventions(DEFAULT_FEATURES, false, 0.3);
  assert.equal(low[0].id, 'maintain-performance');
  assert.equal(watch[0].id, 'watch-moderate');
  assert.ok(!watch[0].description.includes('50%'));
  assert.ok(!low[0].description.includes('chuyên cần rất tốt'));
});

test('radar color uses normalized low scores without treating unknown data as zero', () => {
  assert.equal(radarAppearance([0, 100]).stroke, '#f87171');
  assert.equal(radarAppearance([24.9, 100]).low, true);
  assert.equal(radarAppearance([25, 100]).low, false);
  assert.equal(radarAppearance([null, NaN, 100]).low, false);
  assert.equal(radarAppearance([]).low, false);
  // Zero late submissions is healthy when submissions exist.
  const punctual = calculateRadar({ late_submissions_to_t: 0, assessments_submitted_to_t: 3 });
  assert.equal(radarAppearance(punctual.map(d => d.reference_score)).low, false);
});
