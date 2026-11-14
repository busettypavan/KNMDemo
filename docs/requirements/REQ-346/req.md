# Display Trading Signals on Chart

## Purpose
Show buy and sell signal markers on the price chart to visualize strategy signals in the context of price action.

## Behaviour
- Signals display as markers/icons on the chart at the date they occurred
- Buy signals marked with upward arrow or green marker
- Sell signals marked with downward arrow or red marker
- Signal marker includes date and price at signal point
- Markers positioned on the price candle corresponding to signal date
- User can toggle signals on/off on the chart
- Legend shows signal marker meanings
- Hover over marker shows signal details (date, price, signal type)

## Acceptance Criteria
- Buy signal markers display in green/up-arrow style
- Sell signal markers display in red/down-arrow style
- Markers positioned at correct dates on chart
- Markers include hover tooltip with signal details
- Signals visible when strategy is active
- User can hide/show signals via toggle
- Chart remains responsive with signals displayed

## Order: 8 of 8
**Depends on:** 7 (Apply Moving Average Crossover Strategy), 3 (View Stock Price Chart)

## Source Documents
- Detailed Functional Requirements §4.4 (Applying the MVP strategy, markers on chart)
- ASCII Mock images (Terminal Page - chart area)

## Open Questions
- Signal list table view: explicitly out of scope; markers only for MVP
- Historical signal performance statistics: not specified
- Signal modification/override by user: not mentioned
- Conflicting signals (multiple strategies in future): not addressed