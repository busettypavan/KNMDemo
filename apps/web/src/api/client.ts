// Typed API client over the generated schema (openapi-fetch). Sign-in is an httpOnly cookie that the browser keeps and
// sends by itself (credentials: 'include'), so no script can read the session. Every request carries X-Requested-With,
// which the API requires before it acts on a cookie-authenticated change (CSRF protection).
import createClient, { type Middleware } from 'openapi-fetch';
import type { paths } from './schema';

export const CSRF_HEADER = 'X-Requested-With';
export const CSRF_VALUE = 'knm';

const csrf: Middleware = {
  onRequest({ request }) {
    request.headers.set(CSRF_HEADER, CSRF_VALUE);
    return request;
  }
};

/** In development `/api` is proxied to the API (see API_PROXY_TARGET); in production serve the API under /api or pass its URL. */
export function createApiClient(baseUrl = '/api', fetchImpl?: typeof fetch) {
  const client = createClient<paths>({ baseUrl, credentials: 'include', ...(fetchImpl ? { fetch: fetchImpl } : {}) });
  client.use(csrf);
  return client;
}

export const api = createApiClient();
