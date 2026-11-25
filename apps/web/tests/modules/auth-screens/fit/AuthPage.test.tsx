import React from 'react';
import { fireEvent, renderHook, screen, waitFor } from '@testing-library/react';
import { renderApp } from '../../../../src/testing/render';
import { AuthPage, type AuthClient } from '../../../../src/features/auth/AuthPage';
import { useSession, type SessionClient } from '../../../../src/features/auth/useSession';

type Reply = { data?: unknown; error?: unknown; response: { ok: boolean; status: number } };

function fakeAuthClient(reply: (path: string) => Reply) {
  const calls: { path: string; body: unknown }[] = [];
  const client: AuthClient = {
    POST: (async (path: string, init: { body: unknown }) => {
      calls.push({ path, body: init.body });
      return reply(path) as any;
    }) as AuthClient['POST']
  };
  return { client, calls };
}

const ok = (data: unknown): Reply => ({ data, response: { ok: true, status: 200 } });
const fail = (status: number, error: unknown): Reply => ({ error, response: { ok: false, status } });

function fill(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } });
}

describe('sign in and create account', () => {
  it('blocks an empty form before calling the API', async () => {
    const { client, calls } = fakeAuthClient(() => ok({}));
    renderApp(<AuthPage client={client} />);
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));
    expect(await screen.findByText('Enter your email address.')).toBeTruthy();
    expect(calls).toHaveLength(0);
  });

  it('signs in and confirms the account', async () => {
    const { client, calls } = fakeAuthClient(() => ok({ id: 'u1', email: 'ana@example.com' }));
    const onSignedIn = jest.fn();
    renderApp(<AuthPage client={client} onSignedIn={onSignedIn} />);
    fill('Email', 'ana@example.com');
    fill('Password', 'correct-horse-42');
    fireEvent.click(screen.getAllByRole('button', { name: 'Sign in' })[0]);
    expect(await screen.findByText('Signed in as ana@example.com')).toBeTruthy();
    expect(calls).toEqual([{ path: '/auth/signin', body: { email: 'ana@example.com', password: 'correct-horse-42' } }]);
    expect(onSignedIn).toHaveBeenCalledWith('ana@example.com');
  });

  it('shows the wrong-credentials message without saying which part was wrong', async () => {
    const { client } = fakeAuthClient(() => fail(401, { error: 'invalid-credentials' }));
    renderApp(<AuthPage client={client} />);
    fill('Email', 'ana@example.com');
    fill('Password', 'wrong-password-99');
    fireEvent.click(screen.getAllByRole('button', { name: 'Sign in' })[0]);
    expect(await screen.findByText('Email or password is incorrect.')).toBeTruthy();
  });

  it('checks the password rules on create account before calling the API', async () => {
    const { client, calls } = fakeAuthClient(() => ok({}));
    renderApp(<AuthPage client={client} />);
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }));
    fill('Email', 'new@example.com');
    fill('Password', 'short');
    fireEvent.click(screen.getAllByRole('button', { name: 'Create account' })[0]);
    expect(await screen.findByText('Use between 12 and 256 characters.')).toBeTruthy();
    expect(calls).toHaveLength(0);
  });

  it('reports a taken email on create account', async () => {
    const { client, calls } = fakeAuthClient(() => fail(409, { error: 'email-taken' }));
    renderApp(<AuthPage client={client} />);
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }));
    fill('Email', 'ana@example.com');
    fill('Password', 'correct-horse-42');
    fireEvent.click(screen.getAllByRole('button', { name: 'Create account' })[0]);
    expect(await screen.findByText('An account with this email already exists.')).toBeTruthy();
    expect(calls[0].path).toBe('/auth/signup');
  });
});

describe('useSession', () => {
  it('is signed in when the API knows the cookie', async () => {
    const client: SessionClient = {
      GET: async () => ({ data: { id: 'u1', email: 'ana@example.com' }, response: { ok: true, status: 200 } as Response })
    };
    const { result } = renderHook(() => useSession(client));
    await waitFor(() => expect(result.current).toEqual({ status: 'signed-in', email: 'ana@example.com' }));
  });

  it('is signed out, not an error, when there is no valid cookie', async () => {
    const client: SessionClient = {
      GET: async () => ({ error: { error: 'unauthorized' }, response: { ok: false, status: 401 } as Response })
    };
    const { result } = renderHook(() => useSession(client));
    await waitFor(() => expect(result.current).toEqual({ status: 'signed-out' }));
  });
});
