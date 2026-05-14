// Base URL. Empty by default so requests like "/api/auth/login" hit the same
// origin and use the Vite proxy in dev. Set VITE_API_BASE_URL for prod builds
// where the API lives on a different host.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const TOKEN_KEY = 'ai-tutor-token';

function buildUrl(path) {
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${BASE_URL.replace(/\/$/, '')}${p}`;
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(message, { status, payload } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

async function request(path, { method = 'GET', body, headers = {}, auth = true } = {}) {
  const token = auth ? getToken() : null;

  const res = await fetch(buildUrl(path), {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const contentType = res.headers.get('content-type') || '';
  const payload = res.status === 204
    ? null
    : contentType.includes('application/json')
      ? await res.json().catch(() => null)
      : await res.text().catch(() => '');

  if (!res.ok) {
    const message = extractErrorMessage(payload) || `Request failed with ${res.status}`;
    throw new ApiError(message, { status: res.status, payload });
  }
  return payload;
}

function extractErrorMessage(payload) {
  if (!payload) return null;
  if (typeof payload === 'string') return payload;
  if (typeof payload.detail === 'string') return payload.detail;
  if (Array.isArray(payload.detail)) {
    // FastAPI validation error: take the first message.
    const first = payload.detail[0];
    if (first && typeof first.msg === 'string') return first.msg;
  }
  return null;
}

export const api = {
  get:    (path, opts) => request(path, { ...opts, method: 'GET' }),
  post:   (path, body, opts) => request(path, { ...opts, method: 'POST', body }),
  put:    (path, body, opts) => request(path, { ...opts, method: 'PUT', body }),
  patch:  (path, body, opts) => request(path, { ...opts, method: 'PATCH', body }),
  delete: (path, opts) => request(path, { ...opts, method: 'DELETE' }),
};


/**
 * Open a Server-Sent Events stream and forward each `data: <json>` chunk to
 * `onChunk(parsedJson)`. Closes when the server sends `[DONE]` or the body ends.
 *
 *   await streamSSE('/api/foo/stream', { method: 'POST' }, ({text}) => append(text))
 *
 * Auth header is included automatically. AbortSignal can be passed to cancel.
 */
export async function streamSSE(path, { method = 'POST', body, signal } = {}, onChunk) {
  const token = getToken();
  const res = await fetch(buildUrl(path), {
    method,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
  });

  if (!res.ok) {
    let detail = `Stream failed with ${res.status}`;
    try {
      const payload = await res.json();
      if (payload?.detail) detail = payload.detail;
    } catch { /* ignore */ }
    throw new ApiError(detail, { status: res.status });
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    // SSE events are separated by blank lines (\n\n)
    let idx;
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const eventText = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      for (const line of eventText.split('\n')) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6);
        if (payload === '[DONE]') return;
        try {
          onChunk(JSON.parse(payload));
        } catch {
          // Non-JSON data line — pass as text fallback
          onChunk({ text: payload });
        }
      }
    }
  }
}
