// Sign in and Create account (one page, two tabs, as in docs/requirements/REQ-339/mock.md).
// Passwords are sent once, over the request body, and never stored in the page after submit.
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, AlertIcon, Box, Button, FormControl, FormErrorMessage, FormLabel, Input, Stack, Text } from '@chakra-ui/react';
import { api as defaultApi } from '../../api/client';
import { apiErrorMessage, emailProblem, passwordProblem } from './validation';

export type AuthMode = 'signin' | 'signup';

export interface AuthClient {
  POST(path: '/auth/signin' | '/auth/signup', init: { body: { email: string; password: string } }):
    Promise<{ data?: { id: string; email: string }; error?: { error?: string }; response: Response }>;
}

export interface AuthFormProps {
  mode: AuthMode;
  client?: AuthClient;
  onSignedIn?: (email: string) => void;
}

export function AuthForm({ mode, client = defaultApi as unknown as AuthClient, onSignedIn }: AuthFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [signedInAs, setSignedInAs] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const next = {
      email: emailProblem(email) ?? undefined,
      password: mode === 'signup' ? passwordProblem(password) ?? undefined : password ? undefined : 'Enter your password.',
    };
    setErrors(next);
    setFormError(null);
    if (next.email || next.password) return;
    setBusy(true);
    try {
      const path = mode === 'signup' ? '/auth/signup' : '/auth/signin';
      const { data, error } = await client.POST(path, { body: { email: email.trim(), password } });
      if (error || !data) {
        setFormError(apiErrorMessage(error?.error));
        return;
      }
      setPassword('');
      setSignedInAs(data.email);
      onSignedIn?.(data.email);
      navigate('/stocks');  // the stocks list loads with the new session cookie, no page refresh needed
    } catch {
      setFormError('Something went wrong. Try again.');
    } finally {
      setBusy(false);
    }
  };

  if (signedInAs) {
    return <Alert status="success" role="status"><AlertIcon />Signed in as {signedInAs}</Alert>;
  }

  return (
    <form onSubmit={submit} noValidate aria-label={mode === 'signup' ? 'Create account' : 'Sign in'}>
      <Stack spacing={4}>
        {formError && <Alert status="error" role="alert"><AlertIcon />{formError}</Alert>}
        <FormControl isInvalid={!!errors.email}>
          <FormLabel>Email</FormLabel>
          <Input type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <FormErrorMessage>{errors.email}</FormErrorMessage>
        </FormControl>
        <FormControl isInvalid={!!errors.password}>
          <FormLabel>Password</FormLabel>
          <Input
            type="password"
            autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <FormErrorMessage>{errors.password}</FormErrorMessage>
        </FormControl>
        {mode === 'signup' && <Text fontSize="sm">At least 12 characters, with a letter and a digit.</Text>}
        <Button type="submit" colorScheme="blue" isLoading={busy}>
          {mode === 'signup' ? 'Create account' : 'Sign in'}
        </Button>
      </Stack>
    </form>
  );
}

// One form at a time: the submit button names the action, and the link under it switches to the other one (the
// footer of docs/requirements/REQ-339/mock.md). There are no tabs, so the page offers one sign-in control.
export function AuthPage(props: Pick<AuthFormProps, 'client' | 'onSignedIn'>) {
  const [mode, setMode] = useState<AuthMode>('signin');
  const signup = mode === 'signup';
  return (
    <Box maxW="md" mx="auto" mt={8} p={4}>
      <AuthForm key={mode} mode={mode} {...props} />
      <Text mt={4} fontSize="sm">
        {signup ? 'Already have an account? ' : 'New investor? '}
        <Button variant="link" colorScheme="blue" size="sm" onClick={() => setMode(signup ? 'signin' : 'signup')}>
          {signup ? 'Sign in' : 'Create account'}
        </Button>
      </Text>
    </Box>
  );
}
