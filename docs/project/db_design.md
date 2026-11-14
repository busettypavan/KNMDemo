# DB design

Target DB: SQLite 3.40+

Constraints:
- Primary keys: UUID (text in SQLite)
- Normalization: 3NF
- Timestamps: created_at for record creation; updated_at not included for MVP simplicity
- Soft delete: Not used; records are physically deleted or marked via active status if needed later
- Foreign keys: Enforced; ON DELETE CASCADE for dependent records where applicable

Sources: 
- docs/project/intent.md (project goals and scope)
- docs/project/source/01-detailed-functional-requirements.md (data model §3, flows §4)
- docs/requirements/REQ-339 to REQ-346 (user stories and acceptance criteria)

Tables: db_design_tables.csv (Status: New = proposed by Claude; Feedback = awaiting review; Final = accepted)

## Columns

### users

| Column | Type | Null | Default | Key / FK | Index | Constraints | Description |
|--------|------|------|---------|----------|-------|-------------|-------------|
| id | TEXT | No | — | PK | — | UUID, length 36 | Unique user identifier |
| email | TEXT | No | — | UQ | Yes | NOT NULL, unique | Email address used for sign-in; case-sensitive |
| password_hash | TEXT | No | — | — | — | NOT NULL | Hashed password (bcrypt or similar) |
| full_name | TEXT | No | — | — | — | NOT NULL | User's full name from registration |
| created_at | TEXT | No | CURRENT_TIMESTAMP | — | — | ISO 8601 datetime | Account creation timestamp |

### stocks

| Column | Type | Null | Default | Key / FK | Index | Constraints | Description |
|--------|------|------|---------|----------|-------|-------------|-------------|
| id | TEXT | No | — | PK | — | UUID, length 36 | Unique stock identifier |
| symbol | TEXT | No | — | UQ | Yes | NOT NULL, unique | NSE ticker with .NS suffix (e.g., RELIANCE.NS) |
| name | TEXT | No | — | — | Yes | NOT NULL | Company name (e.g., Reliance Industries Ltd) |
| sector | TEXT | Yes | — | — | Yes | — | Industry sector (e.g., Energy, IT, Banking) |
| created_at | TEXT | No | CURRENT_TIMESTAMP | — | — | ISO 8601 datetime | When stock was added to the reference list |

### price_history

| Column | Type | Null | Default | Key / FK | Index | Constraints | Description |
|--------|------|------|---------|----------|-------|-------------|-------------|
| id | TEXT | No | — | PK | — | UUID, length 36 | Unique record identifier |
| stock_id | TEXT | No | — | FK -> stocks.id | Yes | NOT NULL | Reference to stock; ON DELETE CASCADE |
| date | TEXT | No | — | — | Yes | NOT NULL, YYYY-MM-DD | Trading date in ISO format |
| open | REAL | No | — | — | — | NOT NULL, ≥ 0 | Opening price in INR |
| high | REAL | No | — | — | — | NOT NULL, ≥ 0 | Day's high price in INR |
| low | REAL | No | — | — | — | NOT NULL, ≥ 0 | Day's low price in INR |
| close | REAL | No | — | — | — | NOT NULL, ≥ 0 | Closing price in INR |
| volume | INTEGER | No | — | — | — | NOT NULL, ≥ 0 | Trading volume in shares |
| last_refreshed_at | TEXT | No | CURRENT_TIMESTAMP | — | — | ISO 8601 datetime | When this day's data was last fetched from Yahoo Finance |
| — | — | — | — | Constraint: (stock_id, date) unique | — | — | Only one record per stock per date |

### positions

| Column | Type | Null | Default | Key / FK | Index | Constraints | Description |
|--------|------|------|---------|----------|-------|-------------|-------------|
| id | TEXT | No | — | PK | — | UUID, length 36 | Unique position identifier |
| user_id | TEXT | No | — | FK -> users.id | Yes | NOT NULL | Reference to user account; ON DELETE CASCADE |
| stock_id | TEXT | No | — | FK -> stocks.id | Yes | NOT NULL | Reference to stock; ON DELETE RESTRICT (prevent accidental deletion of a stock with held positions) |
| quantity | REAL | No | — | — | — | NOT NULL, > 0 | Number of shares held (supports fractional shares) |
| buy_price | REAL | No | — | — | — | NOT NULL, > 0 | Purchase price per share in INR |
| buy_date | TEXT | No | — | — | Yes | NOT NULL, YYYY-MM-DD | Date of purchase in ISO format |
| created_at | TEXT | No | CURRENT_TIMESTAMP | — | — | ISO 8601 datetime | When position was recorded |

### strategies

| Column | Type | Null | Default | Key / FK | Index | Constraints | Description |
|--------|------|------|---------|----------|-------|-------------|-------------|
| id | TEXT | No | — | PK | — | UUID, length 36 | Unique strategy identifier |
| name | TEXT | No | — | UQ | Yes | NOT NULL, unique | Strategy name (MVP includes "Moving Average Crossover") |
| description | TEXT | Yes | — | — | — | — | User-facing description of the strategy |
| created_at | TEXT | No | CURRENT_TIMESTAMP | — | — | ISO 8601 datetime | When strategy was added to the system |

## Design Notes

- **Signals (not persisted)**: Per requirements §4.4 and §6, buy/sell signals from Moving Average Crossover are computed on-demand from price_history and not stored. A Signal table may be added in a future extension for caching/performance.

- **Indicators (not persisted)**: Per requirements §4.2 §3, technical indicator overlays (SMA, EMA, RSI, etc.) are computed server-side on demand from price_history and toggled client-side. No IndicatorRequest table for MVP.

- **UUID choice in SQLite**: Text columns (36 chars each for standard UUID format) are used rather than SQLite's native INTEGER ROWID. Trades one byte per row for portability if the schema migrates to PostgreSQL/MySQL later.

- **Price data types**: REAL for prices to avoid integer rounding; high precision (6+ decimal places) is preserved. Volume is INTEGER. If higher precision is needed, migrate to DECIMAL/NUMERIC on future DB engines.

- **Datetime format**: TEXT (ISO 8601, e.g., "2026-11-14T09:30:00") rather than SQLite's unix timestamps, for human readability in queries and exports. Application code handles conversion.

- **Nifty 100 scope**: Stocks table is seeded with exactly 100 NSE stocks at app start or via admin import. Exact composition is a backlog item (open point in requirements §8, item 5).

- **Stock reference vs. frequency**: Stock records are static reference data; users do not add stocks. Stocks are pre-loaded or imported from an external Nifty 100 list (out of scope for DB schema, but in-scope for data pipeline).

- **User deletion**: Positions cascade-delete when a user is deleted (ON DELETE CASCADE on users.id → positions.user_id), maintaining referential integrity. Price history persists independently.

- **Symbol format**: Symbols are stored with the `.NS` suffix for direct use with the yfinance library; no separate market-code column is needed for MVP.
