# WI-041 — Nifty 100 stock list page

Requirement: REQ-340 (Browse Nifty 100 Stocks)
Applications: web (primary), api

## Approach
- **web (primary):** a stock list page showing ticker symbol, company name, current price and day change (amount and %), sorted by symbol (alphabetical), loaded with infinite scroll. Each row links to the stock detail page with its price chart. A watchlist sidebar sits beside the list. Target: page loads within 2 seconds.
- **api (other):** serves the Nifty 100 reference list (stocks table: symbol, name, sector) and the latest daily price data per stock (price_history). Sorting by symbol and paging for infinite scroll are done server-side so the client receives ordered pages.
- Price data is daily end-of-day from Yahoo Finance (`yfinance`), fetched lazily on first view and refreshed at most once a day (functional requirements §4.1, §6). The list shows the latest stored close and the day change against the previous close.

## Areas and files likely affected
- web: `apps/web/src/app/router.tsx` (new route for the list), `apps/web/src/api/client.ts` and `apps/web/src/api/schema.d.ts` (regenerate from the API schema), `apps/web/src/features/` (stock list component, infinite-scroll hook, watchlist sidebar), `apps/web/tests/` (list rendering, sort order, infinite scroll, link to detail).
- api: `apps/api/app/db/models.py` (stocks and price_history models if not yet present), `apps/api/app/glue/routes.py` (stock list endpoint with symbol sort and cursor/page params), a price-fetch service wrapping `yfinance`, `apps/api/tests/` (sort order, paging, price and day-change calculation).
- Exact files are confirmed in `/knm:finalize-workitem` plan review and the preview step; this list is an estimate.

## Risks
- `yfinance` has no SLA or official rate limit; fetching 100 stocks on first load can throttle. Mitigation: lazy fetch and daily refresh, per the functional requirements.
- The 2-second load target depends on the list endpoint reading stored data, not calling Yahoo Finance on every request.
- Day change needs the previous close; a stock with no prior-day row must show a clear empty state rather than a wrong value.

## Assumptions
- The Nifty 100 composition is the proposed list in the functional requirements (REQ-340 still lists the exact list as unconfirmed; this work item does not change it).
- Sort is by symbol ascending. No market-cap field is added to the Stock table.
- Infinite scroll, not pagination controls. Search is out of scope (not in the requirement).
- Watchlist is shown in a sidebar for quick access; adding or removing items is not part of this work item unless REQ-340 says so.
