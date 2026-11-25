import { apiErrorMessage, emailProblem, passwordProblem } from '../../../../src/features/auth/validation';

describe('auth form rules (mirror of the API rules)', () => {
  it('accepts a plausible email and rejects an empty or malformed one', () => {
    expect(emailProblem('  Ana@Example.com ')).toBeNull();
    expect(emailProblem('')).toBe('Enter your email address.');
    expect(emailProblem('ana@example')).toBe('Enter a valid email address.');
    expect(emailProblem('ana @example.com')).toBe('Enter a valid email address.');
  });

  it('needs 12 to 256 characters with a letter and a digit', () => {
    expect(passwordProblem('correct-horse-42')).toBeNull();
    expect(passwordProblem('short1')).not.toBeNull();
    expect(passwordProblem('allletterslongenough')).not.toBeNull();
    expect(passwordProblem('1234567890123')).not.toBeNull();
    expect(passwordProblem('a'.repeat(257) + '1')).not.toBeNull();
  });

  it('shows a friendly message for each API error and never the raw code', () => {
    expect(apiErrorMessage('invalid-credentials')).toBe('Email or password is incorrect.');
    expect(apiErrorMessage('email-taken')).toBe('An account with this email already exists.');
    expect(apiErrorMessage('too-many-attempts')).toBe('Too many attempts. Try again later.');
    expect(apiErrorMessage('something-else')).toBe('Something went wrong. Try again.');
    expect(apiErrorMessage(undefined)).toBe('Something went wrong. Try again.');
  });
});
