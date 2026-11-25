import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { renderApp } from '../../../../src/testing/render';
import { StockList, type StockClient, type StockItem, type StockListPage } from '../../../../src/features/stocks/StockList';

const reliance: StockItem = { symbol: 'RELIANCE.NS', name: 'Reliance Industries Ltd', sector: 'Energy', price: 2945.5, dayChange: 10, dayChangePct: 0.34 };
const tcs: StockItem = { symbol: 'TCS.NS', name: 'Tata Consultancy Services', sector: 'IT', price: 4120, dayChange: null, dayChangePct: null };

type Query = { limit?: number; after?: string };

/** A fake client that answers from a script of replies, in order, and records each query. */
function fakeStockClient(replies: Array<{ status: number; data?: StockListPage }>) {
  const queries: Query[] = [];
  let index = 0;
  const client: StockClient = {
    GET: jest.fn(async (_path, init) => {
      queries.push(init?.params?.query ?? {});
      const reply = replies[Math.min(index, replies.length - 1)];
      index += 1;
      return { data: reply.data, response: { ok: reply.status >= 200 && reply.status < 300, status: reply.status } };
    }) as StockClient['GET'],
  };
  return { client, queries };
}

describe('Nifty 100 stock list', () => {
  it('shows symbol, name, price and day change, with a link to each stock', async () => {
    const { client, queries } = fakeStockClient([{ status: 200, data: { items: [reliance, tcs], nextCursor: null } }]);
    renderApp(<StockList client={client} />);

    expect(await screen.findByText('RELIANCE.NS')).toBeTruthy();
    expect(screen.getByText('Reliance Industries Ltd')).toBeTruthy();
    expect(screen.getByText('₹2,945.50')).toBeTruthy();
    expect(screen.getByText('↗ +10.00 (+0.34%)')).toBeTruthy();
    expect(screen.getByRole('link', { name: 'RELIANCE.NS' }).getAttribute('href')).toBe('/stocks/RELIANCE.NS');
    // a stock with no previous close shows a dash for the change
    expect(screen.getByText('₹4,120.00')).toBeTruthy();
    expect(queries[0]).toEqual({ limit: 100 });
    expect(screen.queryByRole('button', { name: 'Load more' })).toBeNull();
  });

  it('asks signed-out readers to sign in', async () => {
    const { client } = fakeStockClient([{ status: 401 }]);
    renderApp(<StockList client={client} />);
    expect(await screen.findByText(/Sign in to see the Nifty 100 stocks/)).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Sign in' }).getAttribute('href')).toBe('/sign-in');
  });

  it('retries a failed load', async () => {
    const { client } = fakeStockClient([{ status: 500 }, { status: 200, data: { items: [reliance], nextCursor: null } }]);
    renderApp(<StockList client={client} />);
    expect(await screen.findByRole('alert')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
    expect(await screen.findByText('RELIANCE.NS')).toBeTruthy();
  });

  it('loads the next page after the cursor and appends it', async () => {
    const { client, queries } = fakeStockClient([
      { status: 200, data: { items: [reliance], nextCursor: 'RELIANCE.NS' } },
      { status: 200, data: { items: [tcs], nextCursor: null } },
    ]);
    renderApp(<StockList client={client} pageSize={1} />);
    expect(await screen.findByText('RELIANCE.NS')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Load more' }));
    expect(await screen.findByText('TCS.NS')).toBeTruthy();
    expect(screen.getByText('RELIANCE.NS')).toBeTruthy();
    expect(queries[1]).toEqual({ limit: 1, after: 'RELIANCE.NS' });
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Load more' })).toBeNull());
  });

  it('says so when there are no stocks', async () => {
    const { client } = fakeStockClient([{ status: 200, data: { items: [], nextCursor: null } }]);
    renderApp(<StockList client={client} />);
    expect(await screen.findByText('No stocks to show yet.')).toBeTruthy();
  });
});
