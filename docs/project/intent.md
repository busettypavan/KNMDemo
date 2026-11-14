# Intent

## Purpose
A web dashboard for analyzing NSE-listed stocks with price charts, technical indicators, position tracking, and trading strategy signals to help investors make informed trading decisions.

## Goals
- G1: Enable users to browse and analyze NSE stocks with price charts and 10+ technical indicators
- G2: Allow users to track investment positions manually and see real profit/loss against current prices
- G3: Provide technical trading signals (Moving Average Crossover strategy) to support trading decisions

## Not goals
- Full goal planning (multi-goal investment plans with targets and timelines)
- Multiple trading strategies (MVP ships only Moving Average Crossover)
- Real-time streaming data (end-of-day prices only)
- Broker statement or CSV import
- AI features (sentiment analysis, strategy recommendations, goal-gap analysis)
- Full NSE universe (only curated Nifty 100 subset for MVP)
- Aggregate P&L views across multiple positions in the same stock

## Success
- Users can register, sign in, and persist positions across visits
- Users can browse Nifty 100 stocks and view daily price charts with selectable technical indicators (SMA, EMA, RSI, Bollinger Bands, MACD, Stochastic, ATR, VWAP, OBV, Parabolic SAR)
- Users can manually enter positions (quantity, buy price, date) and see real current profit/loss calculated from live market data
- Moving Average Crossover signals are generated and displayed as markers on the chart for user-selected MA periods
