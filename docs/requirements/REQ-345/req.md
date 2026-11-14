# Apply Moving Average Crossover Strategy

## Purpose
Provide a single trading strategy (MA Crossover) that generates buy/sell signals based on moving average crossovers for MVP.

## Behaviour
- User selects Moving Average Crossover strategy from strategy selector
- User specifies MA period (e.g., 20-day, 50-day, 200-day)
- Strategy computes crossover points where price crosses the MA line
- Buy signal: price crosses from below to above the MA
- Sell signal: price crosses from above to below the MA
- Signals computed on-demand from PriceHistory (not pre-computed/persisted)
- Signals recomputed each time chart loads with strategy active

## Acceptance Criteria
- User can select MA Crossover strategy
- User can configure MA period (10 to 200 days)
- Buy signals detected when price crosses above MA
- Sell signals detected when price crosses below MA
- Signals compute within 2 seconds for standard stock history
- Strategy applies to currently viewed stock
- Signals displayed/marked on chart

## Order: 7 of 8
**Depends on:** 3 (View Stock Price Chart)

## Source Documents
- Detailed Functional Requirements §3 (Data Model - Strategy, Signal), §4.4 (Applying the MVP strategy)
- ASCII Mock images (Terminal Page - chart area)

## Open Questions
- Other strategies planned for future: yes, confirmed out of scope
- Signal persistence/caching: confirmed not required for MVP
- Strategy parameter presets (e.g., "Conservative", "Aggressive"): not specified
- Multiple strategy comparison: out of scope for MVP