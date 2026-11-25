# REQ-339: User Registration & Sign In

- Feature: FEAT-1120 (User Registration & Sign In)
- Decision: DEC-374 (Basic Auth for MVP)
- Status: finalized

## Purpose

Investors need an account so that their positions and preferences persist across visits. Basic authentication is required for the MVP (DEC-374).

## Behaviour

1. **Create account.** A new investor can create an account by providing an email address and a password.
2. **Sign in.** A registered investor can sign in with the same email address and password.
3. **Persistence.** Once signed in, the investor's positions and preferences are associated with their account and are available again on later visits.

## Acceptance criteria

- [X] A new investor can create an account with an email address and a password.
- [X] A registered investor can sign in with that email address and password.
- [X] Positions saved by a signed-in investor are still present after the investor signs out and signs in again.
- [X] Preferences saved by a signed-in investor are still present after the investor signs out and signs in again.
- [X] Positions and preferences are available on a later visit, after sign-in.

## Questions and answers

None. No questions were raised for this requirement.

## Scope

In scope: account creation, sign-in, and persistence of positions and preferences per account.

Out of scope for this requirement: anything not named in REQ-339 or DEC-374.
