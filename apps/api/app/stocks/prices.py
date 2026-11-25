"""Daily price data from Yahoo Finance (yfinance), fetched lazily (REQ-341, WI-041).

A stock's history is fetched the first time someone views it and refreshed at most once per UTC day. The refresh runs
inside the request that views the stock. If the source fails, the stored bars are served and marked stale. A failed
refresh is not retried for RETRY_AFTER_FAILURE, so a broken source is not hit on every view.

Only the lazy fetch writes prices; the list endpoint reads what is stored.
"""

import asyncio
import logging
import math
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PriceHistory, Stock

log = logging.getLogger("app.stocks")

HISTORY_PERIOD = "1y"
RETRY_AFTER_FAILURE = timedelta(hours=1)


class PriceSourceError(Exception):
    """The price source could not give usable data. The message is for the log, never for the page."""


@dataclass(frozen=True)
class FetchedBar:
    date: str  # YYYY-MM-DD
    open: float
    high: float
    low: float
    close: float
    volume: int


Fetcher = Callable[[str], Awaitable[list[FetchedBar]]]


def _download(symbol: str) -> list[FetchedBar]:
    import yfinance  # imported here: the rest of the app does not need the package to be loaded

    try:
        frame = yfinance.Ticker(symbol).history(period=HISTORY_PERIOD, interval="1d", auto_adjust=False)
    except Exception as exc:  # the library raises many types; all of them mean "no data"
        raise PriceSourceError(f"download failed for {symbol}: {type(exc).__name__}") from exc
    bars: list[FetchedBar] = []
    for index, row in frame.iterrows():
        close = float(row["Close"])
        if math.isnan(close):
            continue
        # The source gives float32 numbers; INR prices have two decimals, so round to those.
        bars.append(
            FetchedBar(
                date=index.strftime("%Y-%m-%d"),
                open=round(float(row["Open"]), 2),
                high=round(float(row["High"]), 2),
                low=round(float(row["Low"]), 2),
                close=round(close, 2),
                volume=int(row["Volume"]),
            )
        )
    if not bars:
        raise PriceSourceError(f"no rows returned for {symbol}")
    return bars


async def yfinance_fetcher(symbol: str) -> list[FetchedBar]:
    return await asyncio.to_thread(_download, symbol)


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


class PriceService:
    """One per app (app.state.prices). `fetcher`, `clock` and the retry memory are replaceable in tests."""

    def __init__(self, fetcher: Fetcher = yfinance_fetcher, clock: Callable[[], datetime] | None = None) -> None:
        self.fetcher = fetcher
        self.clock = clock or (lambda: datetime.now(UTC))
        self._failed_at: dict[str, datetime] = {}

    async def ensure_fresh(self, session: AsyncSession, stock: Stock) -> bool:
        """Refreshes the stock's bars when they are not from today. Returns True when the data is stale because the
        refresh failed (or was skipped after a recent failure)."""
        now = self.clock()
        last = await session.scalar(
            select(func.max(PriceHistory.last_refreshed_at)).where(PriceHistory.stock_id == stock.id)
        )
        if last is not None and _as_utc(last).date() == now.date():
            return False
        failed = self._failed_at.get(stock.symbol)
        if failed is not None and now - failed < RETRY_AFTER_FAILURE:
            return True
        try:
            bars = await self.fetcher(stock.symbol)
        except PriceSourceError as exc:
            self._failed_at[stock.symbol] = now
            log.warning("price refresh failed: %s", exc)
            return True
        self._failed_at.pop(stock.symbol, None)
        await _store(session, stock.id, bars, now)
        return False


async def _store(session: AsyncSession, stock_id: str, bars: list[FetchedBar], now: datetime) -> None:
    """Inserts new trading dates and updates dates already stored (a corrected close replaces the old one)."""
    existing = {
        row.date: row
        for row in (await session.scalars(select(PriceHistory).where(PriceHistory.stock_id == stock_id))).all()
    }
    for bar in bars:
        row = existing.get(bar.date)
        if row is None:
            session.add(
                PriceHistory(
                    id=str(uuid.uuid4()),
                    stock_id=stock_id,
                    date=bar.date,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    last_refreshed_at=now,
                )
            )
        else:
            row.open, row.high, row.low = bar.open, bar.high, bar.low
            row.close, row.volume, row.last_refreshed_at = bar.close, bar.volume, now
