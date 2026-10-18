/** One refresh per concurrent group; stale responses cannot resurrect a logged-out session. */
export const TOKEN_KEY = 'edurisk_jwt_access_token';
export const REFRESH_TOKEN_KEY = 'edurisk_jwt_refresh_token';
export const SESSION_ENDED = 'edurisk-session-ended';
let generation = 0;
let identityEpoch = 0;
export function getSessionEpoch(): number { return identityEpoch; }
let refreshing: { token: string; promise: Promise<boolean> } | null = null;

export function getStoredToken(): string | null { return localStorage.getItem(TOKEN_KEY); }
export function setStoredTokens(access: string, refresh: string) {
  identityEpoch++;
  storeTokens(access, refresh);
}
function storeTokens(access: string, refresh: string) {
  generation++;
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}
export function clearStoredTokens() {
  identityEpoch++;
  generation++;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.dispatchEvent(new Event(SESSION_ENDED));
}

async function refreshSession(base: string): Promise<boolean> {
  const token = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!token) { clearStoredTokens(); return false; }
  if (refreshing?.token === token) return refreshing.promise;
  const started = generation;
  const promise = (async () => {
    const response = await fetch(`${base.replace(/\/+$/, '')}/api/v1/auth/refresh`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: token }), signal: AbortSignal.timeout(15000),
    });
    if (generation !== started) return false;
    if (response.status === 401 || response.status === 403) { clearStoredTokens(); return false; }
    if (!response.ok) throw new Error('Không thể làm mới phiên đăng nhập. Vui lòng thử lại.');
    const data = await response.json();
    if (generation !== started) return false;
    if (typeof data.access_token !== 'string' || typeof data.refresh_token !== 'string') {
      throw new Error('Phản hồi làm mới phiên không hợp lệ.');
    }
    storeTokens(data.access_token, data.refresh_token);
    return true;
  })();
  refreshing = { token, promise };
  try { return await promise; }
  finally { if (refreshing?.promise === promise) refreshing = null; }
}

export async function authenticatedFetch(base: string, url: string, options: RequestInit = {}): Promise<Response> {
  const epoch = identityEpoch;
  const initialToken = getStoredToken();
  const send = () => {
    const headers = new Headers(options.headers);
    const token = getStoredToken();
    if (token) headers.set('Authorization', `Bearer ${token}`);
    else headers.delete('Authorization');
    return fetch(url, { ...options, headers });
  };
  let response = await send();
  if (identityEpoch !== epoch) throw new DOMException('Session changed', 'AbortError');
  if (response.status !== 401) return response;
  // Another request may already have refreshed the token while this one was in flight.
  if (initialToken === getStoredToken() && !(await refreshSession(base))) return response;
  if (identityEpoch !== epoch) throw new DOMException('Session changed', 'AbortError');
  options.signal?.throwIfAborted();
  if (!getStoredToken()) return response;
  const retriedToken = getStoredToken();
  response = await send();
  if (identityEpoch !== epoch) throw new DOMException('Session changed', 'AbortError');
  if (response.status === 401 && getStoredToken() === retriedToken) clearStoredTokens();
  return response;
}

export function historyStorageKey(base: string, userId?: string): string | null {
  return userId ? `edurisk_history_v3:${encodeURIComponent(base.replace(/\/+$/, ''))}:${userId}` : null;
}
