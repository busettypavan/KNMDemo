# Manually Enter Positions

## Purpose
Allow investors to record their stock purchases manually so they can track holdings and calculate profits/losses against current prices.

## Behaviour
- User opens "Add Position" form with fields: ticker, quantity, buy price, buy date
- Each entry is stored as a separate lot (no auto-averaging with existing positions)
- Positions persist in user account across visits
- Position list updates immediately after entry
- User can edit or delete positions
- Form validation ensures valid ticker, positive quantity, and past date

## Acceptance Criteria
- User can add position with all required fields
- Position displays in portfolio after entry
- Multiple lots of same stock stored separately
- Position data persists across sign-in/out
- Form validates input (ticker exists, quantity > 0, date is valid)
- User can edit quantity and buy price
- User can delete position with confirmation

## Order: 5 of 8
**Depends on:** 1 (User Registration & Sign In)

## Source Documents
- Detailed Functional Requirements §3 (Data Model - Position), §4.3 (Entering a position)
- ASCII Mock images (Terminal Page - Portfolio Holdings table)

## Open Questions
- Decimal quantities (e.g., fractional shares): not specified
- Currency handling for buy price (₹ assumed but not explicit)
- Position entry via CSV/broker import: confirmed out of scope for MVP
- Position editing history/audit trail: not mentioned