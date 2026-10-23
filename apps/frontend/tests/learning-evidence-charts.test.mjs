import { test } from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';

const { outputFiles } = await build({
  stdin: { contents: `import React from 'react'; import {renderToStaticMarkup} from 'react-dom/server';
    import {LearningEvidenceCharts, activityWindows} from './src/components/lecturer/LearningEvidenceCharts';
    export {activityWindows};
    export const render = props => renderToStaticMarkup(React.createElement(LearningEvidenceCharts, props));`, resolveDir: process.cwd() },
  bundle: true, write: false, format: 'esm', platform: 'node',
  banner: { js: "import {createRequire} from 'node:module'; const require=createRequire(process.cwd()+'/package.json');" },
});
const api = await import(`data:text/javascript;base64,${Buffer.from(outputFiles[0].text).toString('base64')}`);
const detail = { cutoff_day: 75, assessment_details: [
  { id: 1, type: 'TMA', due_day: 20, submitted_day: 20, score: 0 },
  { id: 2, type: 'CMA', due_day: 35, submitted_day: 38, score: 80 },
  { id: 3, type: 'TMA', due_day: 50, submitted_day: null, score: null },
] };

test('activity comparison normalizes separate 23-day and 7-day windows', () => {
  const windows = api.activityWindows({ clicks_recent_7: 14, clicks_recent_30: 60, total_clicks_to_t: 100 }, 75);
  assert.deepEqual(windows.map(item => [item.clicks, item.days, item.average]), [[46, 23, 2], [14, 7, 2]]);
  for (const [inputs, cutoff] of [
    [{ clicks_recent_7: 14, clicks_recent_30: 10, total_clicks_to_t: 100 }, 75],
    [{ clicks_recent_7: 14, clicks_recent_30: 60, total_clicks_to_t: 50 }, 75],
    [{ clicks_recent_7: 14, clicks_recent_30: 60, total_clicks_to_t: 100 }, 29],
    [{ clicks_recent_7: NaN, clicks_recent_30: 60, total_clicks_to_t: 100 }, 75],
    [null, 75],
  ]) assert.equal(api.activityWindows(inputs, cutoff), null);
});

test('assessment charts distinguish exact-deadline, late and missing submissions and retain zero scores', () => {
  const html = api.render({ detail, group: 'assessment' });
  assert.match(html, /Trong hạn chung: 1/);
  assert.match(html, /Sau hạn chung: 1/);
  assert.match(html, /Chưa ghi nhận nộp: 1/);
  assert.match(html, /Dòng thời gian từng bài/);
  assert.match(html, /Mốc đánh giá: 75/);
  assert.match(html, /2\/3 bài có điểm hợp lệ/);
  assert.match(html, /aria-label="Điểm TMA #1"[^>]*aria-valuenow="0"/);
  assert.ok(!html.includes('aria-label="Điểm TMA #3"'));
});

test('missing or inconsistent assessment data never produces invented counts or scores', () => {
  for (const assessment_details of [[], [{ ...detail.assessment_details[0], due_day: 76 }],
    [{ ...detail.assessment_details[0], submitted_day: 80 }], [detail.assessment_details[0], detail.assessment_details[0]]]) {
    const html = api.render({ detail: { ...detail, assessment_details }, group: 'assessment' });
    assert.match(html, /Chưa có danh sách bài đến hạn hợp lệ/);
    assert.ok(!html.includes('aria-label="Điểm TMA #1"'));
  }
});

test('activity charts preserve true zero and show unavailable data separately', () => {
  const zero = api.render({ detail, group: 'activity', inputs: {
    clicks_recent_7: 0, clicks_recent_30: 0, total_clicks_to_t: 0, active_days_to_t: 0, active_day_ratio: 0,
  } });
  assert.match(zero, /aria-valuenow="0"/);
  assert.match(zero, /0 lượt \/ 7 ngày/);
  assert.ok(!zero.includes('NaN'));
  const missing = api.render({ detail, group: 'activity', inputs: null });
  assert.match(missing, /Chưa đủ cửa sổ 30 ngày/);
  assert.match(missing, /Chưa có số ngày hoạt động/);
});
