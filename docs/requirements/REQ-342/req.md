# Apply Technical Indicators

## Purpose
Enable investors to overlay 10+ technical indicators on price charts for visual analysis of stock trends and momentum.

## Behaviour
- Provide checkbox/toggle interface to show/hide each indicator
- Indicators computed server-side from cached PriceHistory
- Indicator overlays rendered on same chart with distinct colors
- Support: SMA, EMA, RSI, Bollinger Bands, MACD, Stochastic, ATR, VWAP, OBV, Parabolic SAR
- Configurable periods for applicable indicators (e.g., 20/50-day MA)
- Performance remains responsive with all 10 indicators toggled

## Acceptance Criteria
- All 10 indicators can be toggled independently
- Each indicator displays with distinct color and label
- Indicators compute and render within 2 seconds
- Configurable parameters (e.g., MA period) take effect immediately
- Interface remains responsive with multiple indicators active
- Indicators update when stock or data refreshes

## Order: 4 of 8
**Depends on:** 3 (View Stock Price Chart)

## Source Documents
- Detailed Functional Requirements §3 (Data Model - IndicatorRequest), §4.2 (Applying Indicators)
- ASCII Mock images (Terminal Page - chart area)

## Open Questions
- Default parameter values for each indicator: not specified
- Default indicators shown on load: none, or a selection?
- Mobile/responsive display of many overlays: challenges not addressed
- Legend placement/layout: not specified