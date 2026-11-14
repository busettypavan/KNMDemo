# Browse Nifty 100 Stocks

## Purpose
Allow investors to view and select from a curated list of NSE stocks (Nifty 100) to analyze market opportunities without overwhelming the system.

## Behaviour
- Display list of Nifty 100 stocks with: ticker symbol, company name, current price, day change (amount and percentage)
- Stocks sorted by market cap or symbol for easy navigation
- Click stock to view its detail page with price chart
- Watchlist available in sidebar for quick access
- Price updates reflect latest market data

## Acceptance Criteria
- User sees list of 100 NSE stocks with complete information
- Stock prices and day changes display accurately
- Stocks can be clicked to navigate to price chart
- Watchlist sidebar shows frequently accessed stocks
- Page loads within 2 seconds

## Order: 2 of 8
**Depends on:** 1 (User Registration & Sign In)

## Source Documents
- Detailed Functional Requirements §3 (Data Model - Stock), §4.1 (Browsing)
- ASCII Mock images (Terminal Page - NSE Watchlist)

## Open Questions
- Exact Nifty 100 list composition: which 100 stocks? Proposed but not confirmed
- Sort order preference: market cap, sector, alphabetical?
- Pagination or infinite scroll: not specified
- Search functionality: not mentioned in requirements