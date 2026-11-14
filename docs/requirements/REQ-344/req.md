# View Portfolio with Profit/Loss

## Purpose
Display all user positions with real current profit/loss calculations to enable tracking of portfolio performance.

## Behaviour
- Portfolio table shows each position lot separately
- Columns: ticker, company name, buy price, buy quantity, current price, absolute P&L (₹), percentage P&L (%)
- Color coding: green for gains, red for losses
- Current price fetched from latest PriceHistory
- P&L calculated as: (current - buy) * quantity for absolute; ((current - buy) / buy) * 100 for %
- Portfolio updates when prices refresh
- Total portfolio value and aggregate gains/losses available

## Acceptance Criteria
- All positions display with correct P&L calculations
- Current prices reflect latest market data
- Green/red color coding shows gains/losses visually
- Percentages calculated accurately
- Portfolio updates when user refreshes or new price data loads
- Multiple lots of same stock shown separately with individual P&Ls
- Portfolio persists across sessions

## Order: 6 of 8
**Depends on:** 5 (Manually Enter Positions), 3 (View Stock Price Chart)

## Source Documents
- Detailed Functional Requirements §3 (Data Model - Position, PriceHistory), §4.3 (Seeing P&L)
- ASCII Mock images (Terminal Page - NSE Portfolio Holdings table)

## Open Questions
- Aggregate P&L across same-stock lots: explicitly out of scope for MVP
- Portfolio performance over time (chart): not specified
- Position average cost basis display: not required
- Dividend/corporate action handling: not addressed