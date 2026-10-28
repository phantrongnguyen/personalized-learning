import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';

const { outputFiles } = await build({
  stdin: { contents: `export { inspectSnapshotApi, reviewSnapshotApi } from './src/services/api';
    export { setStoredTokens, clearStoredTokens } from './src/services/session';
    import React from 'react'; import {renderToStaticMarkup} from 'react-dom/server';
    import {SuggestionReview} from './src/components/lecturer/SuggestionReview';
    import {SnapshotEvidenceReview} from './src/components/lecturer/SnapshotEvidenceReview';
    export const renderReview = props => renderToStaticMarkup(React.createElement(SuggestionReview, props));
    export const renderSnapshot = props => renderToStaticMarkup(React.createElement(SnapshotEvidenceReview, props));`, resolveDir: process.cwd() },
  bundle: true, write: false, format: 'esm', platform: 'node',
  banner: { js: "import {createRequire} from 'node:module'; const require=createRequire(process.cwd()+'/package.json');" },
});
const api = await import(`data:text/javascript;base64,${Buffer.from(outputFiles[0].text).toString('base64')}`);
globalThis.window = new EventTarget();
const storage = new Map();
globalThis.localStorage = { getItem: k => storage.get(k) ?? null, setItem: (k,v) => storage.set(k,v), removeItem: k => storage.delete(k) };
beforeEach(() => { api.clearStoredTokens(); api.setStoredTokens('fixture-access', 'fixture-refresh'); });

test('review reads the selected database snapshot without submitting confirmation', async () => {
  const requests = [];
  globalThis.fetch = async (url, options) => { requests.push({ url, options }); return new Response(JSON.stringify({ snapshot_id: 'snapshot' })); };
  const response = await api.inspectSnapshotApi('http://api', 'course', 'student', 'snapshot');
  assert.equal(response.snapshot_id, 'snapshot');
  assert.equal(requests.length, 1);
  assert.equal(requests[0].url, 'http://api/api/v1/lecturer/courses/course/students/student/snapshots/snapshot/review');
  assert.ok(!requests[0].options.method || requests[0].options.method === 'GET');
});

test('confirmation sends the content digest and explicit separate completeness choices', async () => {
  const payload = { snapshot_sha256: 'a'.repeat(64), review_scope: 'aggregate_only',
    source_reference: 'database snapshot', review_note: 'Only compared aggregate database fields.',
    activity_complete: false, assessments_complete: false, acknowledged_limitations: true };
  globalThis.fetch = async (url, options) => {
    assert.equal(options.method, 'POST');
    assert.deepEqual(JSON.parse(options.body), payload);
    assert.equal(new Headers(options.headers).get('Authorization'), 'Bearer fixture-access');
    return new Response(JSON.stringify({ snapshot_id: 'new' }));
  };
  assert.equal((await api.reviewSnapshotApi('http://api', 'course', 'student', 'old', payload)).snapshot_id, 'new');
});

test('a stale snapshot requires reload instead of retrying with a forged digest', async () => {
  let requests = 0;
  globalThis.fetch = async () => { requests++; return new Response(JSON.stringify({ detail: 'Snapshot đã thay đổi; tải lại' }), { status: 409 }); };
  await assert.rejects(api.inspectSnapshotApi('http://api', 'course', 'student', 'old'), /tải lại/);
  assert.equal(requests, 1);
});

test('review keeps missing data explicit without demonstration banners', () => {
  for (const data_source of [null, 'synthetic_demo']) {
    const html = api.renderReview({ detail: { status: 'insufficient_data', data_source, prediction: null,
      cutoff_date: null, suggestions: [], warnings: ['Chưa có xác nhận gắn với đúng nội dung snapshot và người phụ trách.'],
      assignment: { can_assign: false } }, student: { total_clicks: null, late_submissions: null, submission_rate: null }, selectedRuleId: null, onChoose() {} });
    assert.match(html, /Chưa đủ căn cứ/);
    assert.match(html, /Chưa xác minh đủ nguồn dữ liệu/);
    assert.match(html, /Gợi ý &amp; giao bài/);
    assert.ok(!html.includes("Dữ liệu minh họa"));
  }
  const html = api.renderSnapshot({ apiBase: 'http://api', presentationId: 'course', studentId: 'student', snapshotId: 'snapshot', onReviewed() {} });
  assert.match(html, /Đọc snapshot từ database/);
  assert.match(html, /không chứng minh log LMS đầy đủ/);
  assert.ok(!html.includes('checked=""'));
});
