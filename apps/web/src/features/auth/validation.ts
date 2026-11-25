// Client-side checks that mirror the API's rules (apps/api/app/auth/passwords.py). They give quick feedback only; the API
// makes the decision and validates again.
const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export function emailProblem(raw: string): string | null {
  const email = raw.trim().toLowerCase();
  if (!email) return 'Enter your email address.';
  return email.length <= 254 && EMAIL.test(email) ? null : 'Enter a valid email address.';
}

export function passwordProblem(password: string): string | null {
  if (password.length < 12 || password.length > 256) return 'Use between 12 and 256 characters.';
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) return 'Use at least one letter and one digit.';
  return null;
}

/** The message for an error code from the API. Never shows the code itself or any input. */
export function apiErrorMessage(code: string | undefined): string {
  switch (code) {
    case 'email-taken': return 'An account with this email already exists.';
    case 'invalid-credentials': return 'Email or password is incorrect.';
    case 'too-many-attempts': return 'Too many attempts. Try again later.';
    case 'weak-password': return 'Use at least 12 characters, with a letter and a digit.';
    case 'invalid-email': return 'Enter a valid email address.';
    default: return 'Something went wrong. Try again.';
  }
}
