import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';

const { outputFiles } = await build({ entryPoints: ['src/services/session.ts'], bundle: true, write: false, format: 'esm', platform: 'node' });
const session = await import(`data:text/javascript;base64,${Buffer.from(outputFiles[0].text).toString('base64')}`);
globalThis.window = new EventTarget();
const values = new Map();
globalThis.localStorage = { getItem: k => values.get(k) ?? null, setItem: (k, v) => values.set(k, v), removeItem: k => values.delete(k) };
const ok = data => new Response(JSON.stringify(data), { status: 200 });
beforeEach(() => { session.clearStoredTokens(); values.clear(); session.setStoredTokens('expired', 'refresh-a'); });

test('concurrent 401s refresh once and retry with the new access token', async () => {
  let refreshes = 0;
  globalThis.fetch = async (url, options) => {
    if (url.endsWith('/refresh')) { refreshes++; await new Promise(r => setTimeout(r, 10)); return ok({ access_token: 'new', refresh_token: 'refresh-b' }); }
    return options.headers.get('Authorization') === 'Bearer new' ? ok({}) : new Response('', { status: 401 });
  };
  const responses = await Promise.all(Array.from({ length: 5 }, () => session.authenticatedFetch('http://api', 'http://api/protected')));
  assert(responses.every(r => r.status === 200));
  assert.equal(refreshes, 1);
});

test('invalid refresh clears tokens and dispatches session ended', async () => {
  let ended = 0;
  window.addEventListener(session.SESSION_ENDED, () => ended++, { once: true });
  globalThis.fetch = async () => new Response('', { status: 401 });
  assert.equal((await session.authenticatedFetch('http://api', 'http://api/protected')).status, 401);
  assert.equal(session.getStoredToken(), null);
  assert.equal(ended, 1);
});

test('403 on a protected record does not refresh or end the session', async () => {
  let calls = 0;
  globalThis.fetch = async () => { calls++; return new Response('', { status: 403 }); };
  assert.equal((await session.authenticatedFetch('http://api', 'http://api/foreign-record')).status, 403);
  assert.equal(calls, 1); assert.equal(session.getStoredToken(), 'expired');
});

test('refresh network errors and 5xx preserve the session', async () => {
  for (const failure of ['network', 'server']) {
    globalThis.fetch = async url => {
      if (!url.endsWith('/refresh')) return new Response('', { status: 401 });
      if (failure === 'network') throw new TypeError('offline');
      return new Response('', { status: 503 });
    };
    await assert.rejects(session.authenticatedFetch('http://api', 'http://api/protected'));
    assert.equal(session.getStoredToken(), 'expired');
  }
});

test('logout while refresh is pending cannot resurrect the session', async () => {
  let release;
  const gate = new Promise(r => release = r);
  globalThis.fetch = async url => {
    if (!url.endsWith('/refresh')) return new Response('', { status: 401 });
    await gate; return ok({ access_token: 'stale', refresh_token: 'stale-refresh' });
  };
  const pending = session.authenticatedFetch('http://api', 'http://api/protected');
  await new Promise(r => setTimeout(r, 0));
  session.clearStoredTokens(); release();
  await pending;
  assert.equal(session.getStoredToken(), null);
});

test('account switch aborts the old request instead of replaying it as the new account', async () => {
  let release;
  globalThis.fetch = () => new Promise(r => release = () => r(new Response('', { status: 401 })));
  const pending = session.authenticatedFetch('http://api', 'http://api/write', { method: 'POST' });
  session.setStoredTokens('account-b', 'refresh-b'); release();
  await assert.rejects(pending, { name: 'AbortError' });
  assert.equal(session.getStoredToken(), 'account-b');
});

test('history keys isolate accounts and API servers; guests cannot write shared history', () => {
  const a = session.historyStorageKey('http://api/', 'a');
  const b = session.historyStorageKey('http://api', 'b');
  localStorage.setItem(a, '["account-a"]');
  assert.equal(localStorage.getItem(b), null);
  assert.notEqual(a, session.historyStorageKey('http://other-api', 'a'));
  assert.equal(session.historyStorageKey('http://api'), null);
  session.clearStoredTokens(); session.setStoredTokens('b', 'rb');
  assert.equal(localStorage.getItem(b), null);
  assert.equal(localStorage.getItem(a), '["account-a"]');
});
