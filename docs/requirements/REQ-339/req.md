# User Registration & Sign In

## Purpose
Enable investors to create accounts and maintain persistent access to their positions and portfolio across multiple visits.

## Behaviour
- New users can register with email, full name, password, and Terms of Service acceptance
- Existing users can sign in with email and password
- User sessions persist across visits
- Quick demo access available for testing (pre-populated demo accounts)

## Acceptance Criteria
- User can complete registration form with required fields
- Registered user receives account confirmation
- User can sign in with registered credentials
- User session remains active across browser refreshes
- Demo accounts work for quick access without signup

## Order: 1 of 8
**Depends on:** none

## Source Documents
- Detailed Functional Requirements §2 (Users & Auth)
- ASCII Mock images (Login screen)

## Open Questions
- Password reset/recovery flow: not yet specified
- Email verification requirement: confirmation not stated
- Session timeout duration: not specified