"""Fit: /stocks and /stocks/{symbol}/prices through create_app with the real glue, against a SQLite file: auth required,
sort order, latest close and day change, cursor paging, and the lazy daily price refresh (fetch, once-a-day, stale
fallback, retry memory, 503). No test reaches the network: the price source is replaced in every test."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine as sync_engine
from sqlalchemy.orm import Session

from app.db import models  # noqa: F401  (registers the tables)
from app.db.base import Base
from app.db.models import PriceHistory, Stock
from app.http.app import create_app
from app.http.settings import Settings
from app.stocks.prices import FetchedBar, PriceSourceError

SECRET = "s" * 40
PASSWORD = "correct-horse-42"
CSRF = {"X-Requested-With": "knm"}
STORED_ON = datetime(2026, 6, 2, 9, 0, tzinfo=UTC)  # when the seeded rows were "refreshed"
TODAY = datetime(2026, 6, 3, 12, 0, tzinfo=UTC)


class Clock:
    def __init__(self, value: datetime) -> None:
        self.now = value

    def __call__(self) -> datetime:
        return self.now


class FakeSource:
    """Stands in for Yahoo Finance: counts the calls and returns the bars it was given, or fails."""

    def __init__(self, bars: list[FetchedBar] | None = None, error: bool = False) -> None:
        self.bars = bars or []
        self.error = error
        self.calls: list[str] = []

    async def __call__(self, symbol: str) -> list[FetchedBar]:
        self.calls.append(symbol)
        if self.error:
            raise PriceSourceError("offline in tests")
        return self.bars


def yahoo_bars(last_close: float = 120.0) -> list[FetchedBar]:
    return [
        FetchedBar(date="2026-06-01", open=99.0, high=101.0, low=98.0, close=100.0, volume=1000),
        FetchedBar(date="2026-06-02", open=105.0, high=111.0, low=104.0, close=110.0, volume=2000),
        FetchedBar(date="2026-06-03", open=111.0, high=122.0, low=110.0, close=last_close, volume=3000),
    ]


def _row(row_id: str, stock_id: str, date: str, close: float) -> PriceHistory:
    return PriceHistory(
        id=row_id,
        stock_id=stock_id,
        date=date,
        open=1,
        high=1,
        low=1,
        close=close,
        volume=1,
        last_refreshed_at=STORED_ON,
    )


def _seed(db_file) -> None:
    engine = sync_engine(f"sqlite:///{db_file.as_posix()}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            [
                Stock(id="s-infy", symbol="INFY.NS", name="Infosys Ltd", sector="IT"),
                Stock(id="s-rel", symbol="RELIANCE.NS", name="Reliance Industries Ltd", sector="Energy"),
                Stock(id="s-tcs", symbol="TCS.NS", name="Tata Consultancy Services", sector="IT"),
            ]
        )
        session.add_all(
            [
                _row("p1", "s-rel", "2026-06-01", 100.0),
                _row("p2", "s-rel", "2026-06-02", 110.0),
                _row("p3", "s-tcs", "2026-06-02", 4000.0),
            ]
        )
        session.commit()
    engine.dispose()


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "stocks.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file.as_posix()}")
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("COOKIE_SECURE", "false")  # the test client talks plain http
    # GET responses are cached for CACHE_TTL_SECONDS (30 by default). Zero makes every request reach the price logic,
    # so tests that move the clock see the refresh happen.
    monkeypatch.setenv("CACHE_TTL_SECONDS", "0")
    _seed(db_file)
    app = create_app(settings=Settings(env="production"))
    app.state.prices.fetcher = FakeSource(error=True)  # offline unless a test says otherwise
    app.state.prices.clock = Clock(TODAY)
    with TestClient(app) as test_client:
        yield test_client


def _signed_in(client: TestClient) -> TestClient:
    response = client.post("/auth/signup", json={"email": "ana@example.com", "password": PASSWORD}, headers=CSRF)
    assert response.status_code in (200, 201), response.text
    return client


def _source(client: TestClient, source: FakeSource) -> FakeSource:
    client.app.state.prices.fetcher = source
    return source


# --- the list -----------------------------------------------------------------------------------------------------


def test_requires_sign_in(client):
    assert client.get("/stocks").status_code == 401


def test_lists_sorted_by_symbol_with_latest_close_and_day_change(client):
    _signed_in(client)
    body = client.get("/stocks").json()
    assert [item["symbol"] for item in body["items"]] == ["INFY.NS", "RELIANCE.NS", "TCS.NS"]
    by_symbol = {item["symbol"]: item for item in body["items"]}

    reliance = by_symbol["RELIANCE.NS"]
    assert reliance["price"] == 110.0
    assert reliance["dayChange"] == pytest.approx(10.0)
    assert reliance["dayChangePct"] == pytest.approx(10.0)
    assert reliance["name"] == "Reliance Industries Ltd"
    assert reliance["sector"] == "Energy"

    # one stored row: a price but no day change
    assert by_symbol["TCS.NS"]["price"] == 4000.0
    assert by_symbol["TCS.NS"]["dayChange"] is None

    # no stored rows: empty price fields, not an error
    assert by_symbol["INFY.NS"]["price"] is None
    assert by_symbol["INFY.NS"]["dayChangePct"] is None
    assert body["nextCursor"] is None


def test_pages_by_cursor(client):
    _signed_in(client)
    first = client.get("/stocks", params={"limit": 2}).json()
    assert [item["symbol"] for item in first["items"]] == ["INFY.NS", "RELIANCE.NS"]
    assert first["nextCursor"] == "RELIANCE.NS"

    second = client.get("/stocks", params={"limit": 2, "after": first["nextCursor"]}).json()
    assert [item["symbol"] for item in second["items"]] == ["TCS.NS"]
    assert second["nextCursor"] is None


def test_rejects_bad_limit(client):
    _signed_in(client)
    assert client.get("/stocks", params={"limit": 0}).status_code == 422
    assert client.get("/stocks", params={"limit": 201}).status_code == 422


def test_the_list_never_fetches_prices(client):
    _signed_in(client)
    source = _source(client, FakeSource(yahoo_bars()))
    client.get("/stocks")
    assert source.calls == []


# --- the price bars -----------------------------------------------------------------------------------------------


def test_price_bars_need_sign_in(client):
    assert client.get("/stocks/RELIANCE.NS/prices").status_code == 401


def test_price_bars_are_oldest_first_with_the_stored_values(client):
    _signed_in(client)
    body = client.get("/stocks/RELIANCE.NS/prices").json()
    assert body["symbol"] == "RELIANCE.NS"
    assert body["name"] == "Reliance Industries Ltd"
    assert body["stale"] is True  # the offline source failed, so the stored bars are served as stale
    assert [bar["date"] for bar in body["bars"]] == ["2026-06-01", "2026-06-02"]
    assert body["bars"][1] == {"date": "2026-06-02", "open": 1.0, "high": 1.0, "low": 1.0, "close": 110.0, "volume": 1}


def test_price_bars_limit_keeps_most_recent(client):
    _signed_in(client)
    body = client.get("/stocks/RELIANCE.NS/prices", params={"limit": 1}).json()
    assert [bar["date"] for bar in body["bars"]] == ["2026-06-02"]


def test_price_bars_for_unknown_symbol_is_not_found(client):
    _signed_in(client)
    response = client.get("/stocks/NOPE.NS/prices")
    assert response.status_code == 404
    assert response.json() == {"error": "not-found"}


def test_first_view_fetches_and_stores_and_the_same_day_does_not_refetch(client):
    _signed_in(client)
    source = _source(client, FakeSource(yahoo_bars()))
    body = client.get("/stocks/INFY.NS/prices").json()
    assert source.calls == ["INFY.NS"]
    assert body["stale"] is False
    assert [bar["date"] for bar in body["bars"]] == ["2026-06-01", "2026-06-02", "2026-06-03"]

    client.get("/stocks/INFY.NS/prices")
    assert source.calls == ["INFY.NS"]  # refreshed at most once a day


def test_next_day_refreshes_and_corrects_stored_closes(client):
    _signed_in(client)
    _source(client, FakeSource(yahoo_bars(last_close=120.0)))
    client.get("/stocks/INFY.NS/prices")

    client.app.state.prices.clock = Clock(TODAY + timedelta(days=1))
    source = _source(client, FakeSource(yahoo_bars(last_close=125.0)))
    body = client.get("/stocks/INFY.NS/prices").json()
    assert source.calls == ["INFY.NS"]
    assert body["bars"][-1]["close"] == 125.0
    assert len(body["bars"]) == 3  # corrected in place, not duplicated


def test_failed_refresh_is_not_retried_for_an_hour(client):
    _signed_in(client)
    source = _source(client, FakeSource(error=True))
    first = client.get("/stocks/RELIANCE.NS/prices").json()
    again = client.get("/stocks/RELIANCE.NS/prices").json()
    assert first["stale"] is True and again["stale"] is True
    assert source.calls == ["RELIANCE.NS"]

    client.app.state.prices.clock = Clock(TODAY + timedelta(hours=2))
    client.get("/stocks/RELIANCE.NS/prices")
    assert source.calls == ["RELIANCE.NS", "RELIANCE.NS"]


def test_failed_refresh_with_nothing_stored_is_unavailable(client):
    _signed_in(client)
    _source(client, FakeSource(error=True))
    response = client.get("/stocks/INFY.NS/prices")
    assert response.status_code == 503
    assert response.json() == {"error": "price-source-unavailable"}


def test_first_fetch_for_a_stock_without_rows_stores_them(client):
    _signed_in(client)
    _source(client, FakeSource(yahoo_bars()))
    body = client.get("/stocks/INFY.NS/prices").json()
    assert len(body["bars"]) == 3
    listed = {item["symbol"]: item for item in client.get("/stocks").json()["items"]}
    assert listed["INFY.NS"]["price"] == 120.0
    assert listed["INFY.NS"]["dayChange"] == pytest.approx(120.0 - 110.0)


# --- the watchlist ------------------------------------------------------------------------------------------------


def _signed_in_as(client: TestClient, email: str) -> TestClient:
    response = client.post("/auth/signup", json={"email": email, "password": PASSWORD}, headers=CSRF)
    assert response.status_code in (200, 201), response.text
    return client


def test_watchlist_needs_sign_in(client):
    assert client.get("/watchlist").status_code == 401
    assert client.post("/watchlist", json={"symbol": "RELIANCE.NS"}, headers=CSRF).status_code == 401


def test_watchlist_starts_empty_and_is_never_cached(client):
    _signed_in(client)
    response = client.get("/watchlist")
    assert response.json() == {"items": []}
    assert response.headers["cache-control"] == "no-store"


def test_add_shows_the_stock_with_its_price_and_change(client):
    _signed_in(client)
    response = client.post("/watchlist", json={"symbol": "RELIANCE.NS"}, headers=CSRF)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    item = response.json()["items"][0]
    assert item["symbol"] == "RELIANCE.NS"
    assert item["name"] == "Reliance Industries Ltd"
    assert item["price"] == 110.0
    assert item["dayChange"] == pytest.approx(10.0)


def test_adding_twice_keeps_one_entry(client):
    _signed_in(client)
    client.post("/watchlist", json={"symbol": "RELIANCE.NS"}, headers=CSRF)
    body = client.post("/watchlist", json={"symbol": "RELIANCE.NS"}, headers=CSRF).json()
    assert [item["symbol"] for item in body["items"]] == ["RELIANCE.NS"]


def test_watchlist_keeps_the_order_stocks_were_added(client):
    _signed_in(client)
    client.post("/watchlist", json={"symbol": "TCS.NS"}, headers=CSRF)
    client.post("/watchlist", json={"symbol": "RELIANCE.NS"}, headers=CSRF)
    assert [item["symbol"] for item in client.get("/watchlist").json()["items"]] == ["TCS.NS", "RELIANCE.NS"]


def test_adding_an_unknown_symbol_is_not_found(client):
    _signed_in(client)
    response = client.post("/watchlist", json={"symbol": "NOPE.NS"}, headers=CSRF)
    assert response.status_code == 404
    assert response.json() == {"error": "not-found"}


def test_remove_takes_the_stock_off_the_watchlist(client):
    _signed_in(client)
    client.post("/watchlist", json={"symbol": "RELIANCE.NS"}, headers=CSRF)
    client.post("/watchlist", json={"symbol": "TCS.NS"}, headers=CSRF)
    body = client.delete("/watchlist/RELIANCE.NS", headers=CSRF).json()
    assert [item["symbol"] for item in body["items"]] == ["TCS.NS"]
    assert client.delete("/watchlist/NOPE.NS", headers=CSRF).status_code == 404


def test_each_user_has_their_own_watchlist(client):
    _signed_in(client)
    client.post("/watchlist", json={"symbol": "RELIANCE.NS"}, headers=CSRF)
    client.cookies.clear()
    _signed_in_as(client, "ben@example.com")
    assert client.get("/watchlist").json() == {"items": []}


def test_watchlist_changes_need_the_csrf_header(client):
    _signed_in(client)
    assert client.post("/watchlist", json={"symbol": "RELIANCE.NS"}).status_code == 403
    assert client.delete("/watchlist/RELIANCE.NS").status_code == 403
