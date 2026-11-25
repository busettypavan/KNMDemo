// Who is signed in, asked from the API. The session is an httpOnly cookie, so the page never sees a token: it asks
// GET /auth/me on load. A missing or expired cookie is "signed-out", not an error.
import { useEffect, useState } from 'react';
import { api as defaultApi } from '../../api/client';

export type SessionState = { status: 'loading' } | { status: 'signed-in'; email: string } | { status: 'signed-out' };

export interface SessionClient {
  GET(path: '/auth/me'): Promise<{ data?: { id: string; email: string }; response: Response }>;
}

export function useSession(client: SessionClient = defaultApi as unknown as SessionClient): SessionState {
  const [state, setState] = useState<SessionState>({ status: 'loading' });
  useEffect(() => {
    let active = true;
    client.GET('/auth/me')
      .then(({ data, response }) => {
        if (!active) return;
        setState(response.ok && data ? { status: 'signed-in', email: data.email } : { status: 'signed-out' });
      })
      .catch(() => { if (active) setState({ status: 'signed-out' }); });
    return () => { active = false; };
  }, [client]);
  return state;
}
