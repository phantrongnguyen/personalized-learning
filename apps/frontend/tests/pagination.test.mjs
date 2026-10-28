import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';

const { outputFiles } = await build({
  stdin: { contents: `export { getAdvisorStudentsApi, getCourseRiskBoardApi } from './src/services/api';
    export { setStoredTokens, clearStoredTokens } from './src/services/session';`, resolveDir: process.cwd() },
  bundle: true, write: false, format: 'esm', platform: 'node',
});
const api = await import(`data:text/javascript;base64,${Buffer.from(outputFiles[0].text).toString('base64')}`);
globalThis.window = new EventTarget();
const values = new Map();
globalThis.localStorage = { getItem: k => values.get(k) ?? null, setItem: (k,v) => values.set(k,v), removeItem: k => values.delete(k) };
beforeEach(() => { api.clearStoredTokens(); api.setStoredTokens('account-a', 'refresh-a'); });

test('advisor and lecturer lists read every page and preserve filters', async () => {
  for (const load of [() => api.getAdvisorStudentsApi('http://api', 'A B'),
                      () => api.getCourseRiskBoardApi('http://api', 'course')]) {
    const offsets = [];
    globalThis.fetch = async url => {
      const parsed = new URL(url);
      const offset = Number(parsed.searchParams.get('offset'));
      offsets.push(offset);
      assert.equal(parsed.searchParams.get('limit'), '100');
      if (parsed.pathname.includes('/advisor/')) assert.equal(parsed.searchParams.get('class_name'), 'A B');
      return new Response(JSON.stringify(Array.from({ length: Math.min(100, 201-offset) }, (_,i) => ({ id: offset+i }))));
    };
    const result = await load();
    assert.equal(result.length, 201);
    assert.deepEqual(offsets, [0, 100, 200]);
    assert.equal(result[200].id, 200);
  }
});

test('a failed later page rejects the whole list', async () => {
  globalThis.fetch = async url => new URL(url).searchParams.get('offset') === '0'
    ? new Response(JSON.stringify(Array(100).fill({ id: 1 }))) : new Response('', { status: 500 });
  await assert.rejects(api.getAdvisorStudentsApi('http://api'), /Không thể tải/);
});

test('account change during page decoding cannot return or combine old rows', async () => {
  globalThis.fetch = async () => ({ status: 200, ok: true, json: async () => {
    api.setStoredTokens('account-b', 'refresh-b');
    return Array(100).fill({ owner: 'account-a' });
  }});
  await assert.rejects(api.getAdvisorStudentsApi('http://api'), { name: 'AbortError' });
});
