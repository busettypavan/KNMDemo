# View Stock Price Chart

## Purpose
Display daily OHLCV (Open, High, Low, Close, Volume) price data in an interactive chart to enable technical analysis of NSE stocks.

## Behaviour
- Load stock data from Yahoo Finance (yfinance) with .NS suffix for NSE tickers
- Fetch/refresh price history daily (once per day maximum)
- Display candlestick chart with date, OHLCV values
- Chart is responsive and interactive (zoom, pan)
- Volume bar chart displayed below main price chart
- Loading spinner shown while data fetches

## Acceptance Criteria
- Price chart displays correct OHLCV data for selected stock
- Chart updates with latest market data (end-of-day)
- Chart renders within 3 seconds for cached data
- Chart allows zoom and pan interactions
- Volume bars visible below price chart
- Error message shown if data fetch fails

## Order: 3 of 8
**Depends on:** 2 (Browse Nifty 100 Stocks)

## Source Documents
- Detailed Functional Requirements §3 (Data Model - PriceHistory), §4.1 (Browsing), §6 (Data source)
- ASCII Mock images (Terminal Page - Nifty 500 chart)

## Open Questions
- Minimum historical candles to display: not specified (30, 60, 90 days default?)
- Chart library/vendor: not specified
- Intraday vs. daily candles: requirements specify daily
- Data caching strategy beyond "once per day": not detailed