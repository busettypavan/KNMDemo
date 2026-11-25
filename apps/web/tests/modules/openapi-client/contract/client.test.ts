/** @jest-environment node */
import fs from 'fs';
import path from 'path';
import { createApiClient } from '../../../../src/api/client';

type Call = { url: string; auth: string | null; csrf: string | null; credentials: string | undefined };
const fakeFetch = (reply: () => Response) => {
  const calls: Call[] = [];
  const impl = (async (input: Request) => {
    calls.push({
      url: input.url,
      auth: input.headers.get('Authorization'),
      csrf: input.headers.get('X-Requested-With'),
      credentials: input.credentials
    });
    return reply();
  }) as unknown as typeof fetch;
  return { calls, impl };
};
const json = (body: unknown, status = 200) => () => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
// the generated paths are empty until the first generation: call through any
const get = (client: ReturnType<typeof createApiClient>, p: string) => (client as any).GET(p);

describe('api client contract', () => {
  it('sends the session cookie with every request and never an Authorization header', async () => {
    const f = fakeFetch(json({ ok: true }));
    const client = createApiClient('http://api.test', f.impl);
    await get(client, '/ping');
    await get(client, '/ping');
    expect(f.calls.map((c) => c.credentials)).toEqual(['include', 'include']);
    expect(f.calls.map((c) => c.auth)).toEqual([null, null]);
  });

  it('marks every request with the X-Requested-With header the API checks for cookie-authenticated changes', async () => {
    const f = fakeFetch(json({ ok: true }));
    const client = createApiClient('http://api.test', f.impl);
    await get(client, '/ping');
    expect(f.calls[0].csrf).toBe('knm');
  });

  it('calls the base URL and returns data on success and error on failure', async () => {
    const ok = fakeFetch(json({ id: 1 }));
    const r = await get(createApiClient('http://api.test/base', ok.impl), '/items');
    expect(ok.calls[0].url).toBe('http://api.test/base/items');
    expect(r.data).toEqual({ id: 1 });
    const bad = fakeFetch(json({ error: 'not-found' }, 404));
    const e = await get(createApiClient('http://api.test', bad.impl), '/missing');
    expect(e.error).toEqual({ error: 'not-found' });
    expect(e.response.status).toBe(404);
  });

  it('never stores anything script can read: no token in storage or in the page', () => {
    const source = fs.readFileSync(path.join(__dirname, '../../../../src/api/client.ts'), 'utf8');
    expect(source).not.toMatch(/localStorage|sessionStorage|document\.cookie|indexedDB|setAuthToken|Bearer/);
  });

  it('defaults to /api', () => {
    const source = fs.readFileSync(path.join(__dirname, '../../../../src/api/client.ts'), 'utf8');
    expect(source).toMatch(/baseUrl = '\/api'/);
  });
});
