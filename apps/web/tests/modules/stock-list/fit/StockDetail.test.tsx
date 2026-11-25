import React from 'react';
import { fireEvent, screen } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { renderApp } from '../../../../src/testing/render';
import { StockDetail, type PriceClient, type PriceSeries } from '../../../../src/features/stocks/StockDetail';

// The chart draws on a canvas, which jsdom does not provide. The stub renders the bar count so the page can be tested.
jest.mock('react-financial-charts', () => {
  const Stub = () => null;
  const ChartCanvas = ({ data, children }: { data: unknown[]; children?: unknown }) =>
    require('react').createElement('div', { 'data-testid': 'chart-canvas', 'data-count': String(data.length) }, children as never);
  const builder = () => {
    const provider: any = (data: any[]) => ({
      data,
      xScale: null,
      xAccessor: (d: any) => data.indexOf(d),
      displayXAccessor: (d: any) => d.date,
    });
    provider.inputDateAccessor = () => provider;
    provider.utc = () => provider;
    return provider;
  };
  return {
    ChartCanvas,
    Chart: Stub,
    XAxis: Stub,
    YAxis: Stub,
    MouseCoordinateX: Stub,
    MouseCoordinateY: Stub,
    CandlestickSeries: Stub,
    BarSeries: Stub,
    OHLCTooltip: Stub,
    CrossHairCursor: Stub,
    discontinuousTimeScaleProviderBuilder: builder,
    lastVisibleItemBasedZoomAnchor: () => 0,
  };
});

const series: PriceSeries = {
  symbol: 'RELIANCE.NS',
  name: 'Reliance Industries Ltd',
  stale: false,
  bars: [
    { date: '2026-06-01', open: 99, high: 101, low: 98, close: 100, volume: 1000 },
    { date: '2026-06-02', open: 105, high: 111, low: 104, close: 110, volume: 2000 },
  ],
};

type Reply = { status: number; data?: PriceSeries };

function fakePriceClient(replies: Reply[]) {
  const paths: string[] = [];
  let index = 0;
  const client: PriceClient = {
    GET: jest.fn(async (path: string) => {
      paths.push(path);
      const reply = replies[Math.min(index, replies.length - 1)];
      index += 1;
      return { data: reply.data, response: { ok: reply.status >= 200 && reply.status < 300, status: reply.status } };
    }) as PriceClient['GET'],
  };
  return { client, paths };
}

function renderDetail(client: PriceClient) {
  return renderApp(
    <Routes>
      <Route path="/stocks/:symbol" element={<StockDetail client={client} />} />
    </Routes>,
    { route: '/stocks/RELIANCE.NS' }
  );
}

describe('stock price page', () => {
  it('shows the name, last close and the candlestick chart for the bars', async () => {
    const { client, paths } = fakePriceClient([{ status: 200, data: series }]);
    renderDetail(client);

    expect(await screen.findByRole('heading', { name: /Reliance Industries Ltd/ })).toBeTruthy();
    expect(screen.getByText('₹110.00')).toBeTruthy();
    expect(screen.getByTestId('chart-canvas').getAttribute('data-count')).toBe('2');
    expect(paths).toEqual(['/stocks/{symbol}/prices']);
    expect(screen.getByRole('link', { name: '← All stocks' }).getAttribute('href')).toBe('/stocks');
  });

  it('says so when the stock has no bars yet', async () => {
    const { client } = fakePriceClient([{ status: 200, data: { ...series, bars: [] } }]);
    renderDetail(client);
    expect(await screen.findByText('No price data yet.')).toBeTruthy();
    expect(screen.queryByTestId('chart-canvas')).toBeNull();
  });

  it('reports an unknown stock', async () => {
    const { client } = fakePriceClient([{ status: 404 }]);
    renderDetail(client);
    expect(await screen.findByText('This stock is not on the list.')).toBeTruthy();
  });

  it('asks signed-out readers to sign in', async () => {
    const { client } = fakePriceClient([{ status: 401 }]);
    renderDetail(client);
    expect(await screen.findByText(/Sign in to see price charts/)).toBeTruthy();
  });

  it('retries after an error', async () => {
    const { client } = fakePriceClient([{ status: 500 }, { status: 200, data: series }]);
    renderDetail(client);
    expect(await screen.findByRole('alert')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
    expect(await screen.findByTestId('chart-canvas')).toBeTruthy();
  });

  it('says the bars are saved ones when today\'s refresh failed', async () => {
    const { client } = fakePriceClient([{ status: 200, data: { ...series, stale: true } }]);
    renderDetail(client);
    expect(await screen.findByText('Showing saved prices. The latest refresh failed.')).toBeTruthy();
    expect(screen.getByTestId('chart-canvas')).toBeTruthy();
  });

  it('says prices are unavailable when the source failed and nothing is stored', async () => {
    const { client } = fakePriceClient([{ status: 503 }]);
    renderDetail(client);
    expect(await screen.findByText('Price data is not available right now. Try again later.')).toBeTruthy();
    expect(screen.queryByTestId('chart-canvas')).toBeNull();
  });
});
