# WI-030: Account sign-up and sign-in with hashed passwords and JWT

Applications: api (primary), web (other)

- Requirement: REQ-339 (User Registration & Sign In), status approved
- Feature: FEAT-1120, decision: DEC-374 (Basic Auth for MVP)

## Answers that shape this plan

- Token issuance: issued in the Python API (apps/api), in this work item (Q&A q1).
- Password reset: part of this work item (Q&A q2).
- Token storage in the browser: httpOnly cookie (answered in chat, not recorded as a KNM answer). This departs from REQ-339's wording that the client stores the token and sends it in the Authorization header. The API sets the cookie, and the browser sends it back on later requests, so sign-in persists across visits.
- Out of scope: the positions and preferences tables. No such tables exist in the repo. This work item adds the account and its ownership key (`user_id`), and the sign-in flow. Saving positions and preferences per account is a follow-up.

## Approach

### API (apps/api, primary)

1. **User model.** Add `User` to `app/db/models.py`: `id`, `email` (unique, normalised to lower case), `password_hash`, `created_at`. Add a migration file. `Database.create_all` is for development and tests only.
2. **Password hashing.** Add `app/auth/passwords.py` using `argon2-cffi` (Argon2id). Store only the hash. Add `argon2-cffi` to `requirements.in` and regenerate `requirements.txt`.
3. **Token issuance.** Add `app/auth/tokens.py`: sign an HS256 JWT with `sub` (user id), `iat`, `exp`, and `iss`/`aud` when configured. Reuse `AuthSettings` from `app/auth/jwt.py`, and update that file's header comment, since tokens are now issued here.
4. **Cookie.** The sign-in and sign-up responses set `session` as an `HttpOnly`, `Secure`, `SameSite=Strict` cookie with `Max-Age` equal to the token lifetime. Sign-out clears it. `app/auth/middleware.py` reads the cookie when no `Authorization` header is present; a bad token from either source returns 401 as today.
5. **Routes.** Add `app/auth/routes.py` and register it in `app/glue/routes.py` at the `knm:entries` marker:
   - `POST /auth/signup`: validates the email format and a strong password, then creates the user. Duplicate email returns 409 with the same response shape as other errors, so account existence is not revealed beyond the required message.
   - `POST /auth/signin`: verifies the password, sets the cookie.
   - `POST /auth/signout`: clears the cookie.
   - `POST /auth/password-reset/request` and `POST /auth/password-reset/confirm`: a single-use reset token, valid for a short time, signed with a `purpose` claim so it cannot be used as a session token. Delivery is through a sender interface. Production email delivery is not part of this work item.
6. **Lockout and rate limiting.** Add `app/auth/lockout.py`: count failed sign-ins per email and per client IP, lock the account for a period after N failures, and return 429 while locked. Store counts in memory, consistent with the existing `memory-cache` module. A multi-instance deployment would need a shared store; this is recorded as a risk.
7. **Ownership checks.** Add an ownership helper that compares the token's `user_id` with a resource's owner before reads and writes. `Note` has no owner column; add `user_id` to it in the migration, or flag `Note` as not user-scoped and tell the product owner. Protected routes use `require_auth`, and mutations (POST/PUT/DELETE) check the role or permission on the server.
8. **Config.** Add `TOKEN_TTL_SECONDS`, `LOGIN_MAX_FAILURES`, and `LOGIN_LOCK_SECONDS` to `app/glue/config.py`. `JWT_SECRET` stays required and at least 32 characters.
9. **Security baselines.** HTTPS is enforced at the deployment layer. The API also sends `Strict-Transport-Security`. Cookie-based requests need CSRF protection: `SameSite=Strict` plus a check that the `Origin` header matches the configured web origin on state-changing requests.
10. **Tests.** Add `tests/modules/auth-accounts/` covering: signup, duplicate email, weak or malformed input, signin success and failure, lockout, cookie flags, sign-out, password-reset tokens (single use, expiry, purpose), and ownership (a user cannot read another user's resource).

### Web (apps/web, other)

1. **Auth screens.** Add `src/features/auth/` with the Sign in and Create account tabs from the mock (email, password, submit). Client-side validation runs first; the server still validates.
2. **Routes.** Add the sign-in and create-account routes to `src/app/router.tsx` at the `knm:entries` marker, with a route guard for protected pages.
3. **API client.** `src/api/client.ts` sends requests with `credentials: 'include'` so the cookie is sent. The in-memory `setAuthToken` path is removed, because the token now lives only in the cookie. Keep `createApiClient` for other callers.
4. **Session state.** On load, the app calls a `GET /auth/me` route to learn whether a valid cookie exists. This restores the signed-in state across visits without storing a token in JavaScript.
5. **Schema.** Regenerate `src/api/schema.d.ts` with `scripts/generate-client.cjs` after the API's OpenAPI export.
6. **Tests.** Add `tests/modules/auth-screens/` for validation messages, the sign-in flow, and the signed-in state after reload.

## Files likely affected

- api: `app/db/models.py`, new migration, `app/auth/passwords.py` (new), `app/auth/tokens.py` (new), `app/auth/lockout.py` (new), `app/auth/routes.py` (new), `app/auth/middleware.py`, `app/auth/jwt.py`, `app/glue/routes.py`, `app/glue/config.py`, `requirements.in`, `requirements.txt`, `tests/modules/auth-accounts/`
- web: `src/features/auth/` (new), `src/app/router.tsx`, `src/api/client.ts`, `src/api/schema.d.ts`, `tests/modules/auth-screens/`

## Risks

- The cookie-based design departs from REQ-339's wording on storage. The product owner should confirm this in the requirement.
- Lockout counts are in memory. With more than one API instance, a lock on one instance does not apply to the others.
- `Note` has no owner column, so existing notes are not user-scoped until the migration adds one.
- Password reset needs an email delivery provider, which is outside this work item.

## Assumptions

- The web app and the API are served from the same site, so the cookie is sent without cross-site rules.
- `argon2-cffi` is an acceptable dependency.
- Positions and preferences are not stored in this work item (see above).
