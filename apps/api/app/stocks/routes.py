"""Stocks: the Nifty 100 list with the latest close and day change (REQ-340, WI-041).

Signed-in users only. Sorted by symbol. Pages by cursor: pass the last symbol of the previous page as `after` for
infinite scroll. Price fields are null when no price row is stored yet. Prices are read from the database only; this
endpoint never calls Yahoo Finance.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import AuthClaims
from app.auth.middleware import require_auth
from app.db.models import PriceHistory, Stock, WatchlistItem
from app.db.session import get_session
from app.stocks.prices import PriceService


class StockItem(BaseModel):
    symbol: str
    name: str
    sector: str | None
    price: float | None
    dayChange: float | None
    dayChangePct: float | None


class StockPage(BaseModel):
    items: list[StockItem]
    nextCursor: str | None


class PriceBar(BaseModel):
    date: str  # YYYY-MM-DD
    open: float
    high: float
    low: float
    close: float
    volume: int


class PriceSeries(BaseModel):
    symbol: str
    name: str
    bars: list[PriceBar]
    stale: bool  # true when the refresh failed and these are the bars stored before it


router = APIRouter()


async def _latest_closes(session: AsyncSession, stock_ids: list[str]) -> dict[str, dict[int, float]]:
    """stock id -> {1: latest close, 2: close before that}, from the stored daily rows."""
    if not stock_ids:
        return {}
    ranked = (
        select(
            PriceHistory.stock_id.label("stock_id"),
            PriceHistory.close.label("close"),
            func.row_number()
            .over(partition_by=PriceHistory.stock_id, order_by=PriceHistory.date.desc())
            .label("rn"),
        )
        .where(PriceHistory.stock_id.in_(stock_ids))
        .subquery()
    )
    rows = await session.execute(select(ranked.c.stock_id, ranked.c.close, ranked.c.rn).where(ranked.c.rn <= 2))
    closes: dict[str, dict[int, float]] = {}
    for row in rows.all():
        closes.setdefault(str(row.stock_id), {})[int(row.rn)] = float(row.close)
    return closes


def _item(stock: Stock, closes: dict[int, float]) -> StockItem:
    latest = closes.get(1)
    previous = closes.get(2)
    change: float | None = None
    change_pct: float | None = None
    if latest is not None and previous:
        change = latest - previous
        change_pct = change / previous * 100
    return StockItem(
        symbol=stock.symbol,
        name=stock.name,
        sector=stock.sector,
        price=latest,
        dayChange=change,
        dayChangePct=change_pct,
    )


@router.get("/stocks", response_model=StockPage, dependencies=[Depends(require_auth)])
async def list_stocks(
    limit: int = Query(100, ge=1, le=200),
    after: str | None = Query(None, max_length=32),
    session: AsyncSession = Depends(get_session),
) -> Any:
    stmt = select(Stock).order_by(Stock.symbol).limit(limit + 1)
    if after:
        stmt = stmt.where(Stock.symbol > after)
    stocks = list((await session.scalars(stmt)).all())
    page = stocks[:limit]
    closes = await _latest_closes(session, [s.id for s in page])
    items = [_item(s, closes.get(s.id, {})) for s in page]
    next_cursor = page[-1].symbol if len(stocks) > limit and page else None
    return StockPage(items=items, nextCursor=next_cursor)


@router.get("/stocks/{symbol}/prices", response_model=PriceSeries, dependencies=[Depends(require_auth)])
async def price_history(
    request: Request,
    symbol: str = Path(max_length=32),
    limit: int = Query(250, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """The most recent `limit` daily bars for one stock, oldest first. Refreshes them first when they are not from
    today. 404 when the symbol is not on the list; 503 when the refresh failed and nothing is stored yet."""
    stock = (await session.scalars(select(Stock).where(Stock.symbol == symbol))).first()
    if stock is None:
        raise HTTPException(status_code=404, detail="not-found")
    prices: PriceService = request.app.state.prices
    stale = await prices.ensure_fresh(session, stock)
    rows = (
        await session.scalars(
            select(PriceHistory)
            .where(PriceHistory.stock_id == stock.id)
            .order_by(PriceHistory.date.desc())
            .limit(limit)
        )
    ).all()
    if stale and not rows:
        raise HTTPException(status_code=503, detail="price-source-unavailable")
    bars = [
        PriceBar(date=r.date, open=r.open, high=r.high, low=r.low, close=r.close, volume=r.volume)
        for r in reversed(rows)
    ]
    return PriceSeries(symbol=stock.symbol, name=stock.name, bars=bars, stale=stale)


class WatchlistEntry(BaseModel):
    symbol: str
    name: str
    price: float | None
    dayChange: float | None
    dayChangePct: float | None


class WatchlistPage(BaseModel):
    items: list[WatchlistEntry]


class WatchAdd(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)


# The watchlist changes on every add and remove, so its responses are never cached (see app/cache/middleware.py).
NO_STORE = {"Cache-Control": "no-store"}


async def _watchlist(session: AsyncSession, user_id: str) -> WatchlistPage:
    """The user's stocks in the order they were added, each with its latest stored close and day change."""
    rows = (
        await session.execute(
            select(Stock)
            .join(WatchlistItem, WatchlistItem.stock_id == Stock.id)
            .where(WatchlistItem.user_id == user_id)
            .order_by(WatchlistItem.added_at, Stock.symbol)
        )
    ).scalars().all()
    closes = await _latest_closes(session, [s.id for s in rows])
    items = []
    for stock in rows:
        item = _item(stock, closes.get(stock.id, {}))
        items.append(
            WatchlistEntry(
                symbol=item.symbol,
                name=item.name,
                price=item.price,
                dayChange=item.dayChange,
                dayChangePct=item.dayChangePct,
            )
        )
    return WatchlistPage(items=items)


async def _stock_by_symbol(session: AsyncSession, symbol: str) -> Stock:
    stock = (await session.scalars(select(Stock).where(Stock.symbol == symbol))).first()
    if stock is None:
        raise HTTPException(status_code=404, detail="not-found")
    return stock


@router.get("/watchlist", response_model=WatchlistPage)
async def get_watchlist(auth: AuthClaims = Depends(require_auth), session: AsyncSession = Depends(get_session)) -> Any:
    page = await _watchlist(session, auth.user_id)
    return JSONResponse(page.model_dump(), headers=NO_STORE)


@router.post("/watchlist", response_model=WatchlistPage)
async def add_to_watchlist(
    body: WatchAdd,
    auth: AuthClaims = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Adds a stock to the user's watchlist. Adding one already there changes nothing. 404 if not listed."""
    stock = await _stock_by_symbol(session, body.symbol)
    already = await session.scalar(
        select(WatchlistItem.id).where(WatchlistItem.user_id == auth.user_id, WatchlistItem.stock_id == stock.id)
    )
    if already is None:
        session.add(WatchlistItem(id=str(uuid.uuid4()), user_id=auth.user_id, stock_id=stock.id))
        await session.flush()
    page = await _watchlist(session, auth.user_id)
    return JSONResponse(page.model_dump(), headers=NO_STORE)


@router.delete("/watchlist/{symbol}", response_model=WatchlistPage)
async def remove_from_watchlist(
    symbol: str = Path(max_length=32),
    auth: AuthClaims = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> Any:
    stock = await _stock_by_symbol(session, symbol)
    await session.execute(
        delete(WatchlistItem).where(WatchlistItem.user_id == auth.user_id, WatchlistItem.stock_id == stock.id)
    )
    page = await _watchlist(session, auth.user_id)
    return JSONResponse(page.model_dump(), headers=NO_STORE)


def mount(app: FastAPI) -> None:
    """Glue entry point: the list reads stored prices; the price endpoint refreshes them through app.state.prices."""
    app.state.prices = PriceService()
    app.include_router(router)
