import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { renderApp } from '../../../../src/testing/render';
import { WatchlistSidebar, type WatchlistClient, type WatchlistEntry } from '../../../../src/features/watchlist/WatchlistSidebar';

const reliance: WatchlistEntry = { symbol: 'RELIANCE.NS', name: 'Reliance Industries Ltd', price: 2945.5, dayChange: 10, dayChangePct: 0.34 };

/** A fake that behaves like the API: adds unless the symbol is unknown, removes, and lists in the order added. */
function fakeWatchlist(initial: WatchlistEntry[] = [], signedOut = false) {
  let items = [...initial];
  const page = () => ({ items: [...items] });
  const client: WatchlistClient = {
    GET: jest.fn(async () =>
      signedOut ? { response: { ok: false, status: 401 } } : { data: page(), response: { ok: true, status: 200 } }
    ) as WatchlistClient['GET'],
    POST: jest.fn(async (_path: string, init: { body: { symbol: string } }) => {
      const { symbol } = init.body;
      if (symbol === 'NOPE.NS') return { response: { ok: false, status: 404 } };
      if (!items.some((i) => i.symbol === symbol)) {
        items.push({ ...reliance, symbol, name: symbol === 'TCS.NS' ? 'Tata Consultancy Services' : reliance.name });
      }
      return { data: page(), response: { ok: true, status: 200 } };
    }) as WatchlistClient['POST'],
    DELETE: jest.fn(async (_path: string, init: { params: { path: { symbol: string } } }) => {
      items = items.filter((i) => i.symbol !== init.params.path.symbol);
      return { data: page(), response: { ok: true, status: 200 } };
    }) as WatchlistClient['DELETE'],
  };
  return client;
}

describe('watchlist sidebar', () => {
  it('lists the saved stocks with their price, change and a link to each', async () => {
    renderApp(<WatchlistSidebar client={fakeWatchlist([reliance])} />);
    expect(await screen.findByRole('link', { name: 'RELIANCE.NS' })).toBeTruthy();
    expect(screen.getByRole('link', { name: 'RELIANCE.NS' }).getAttribute('href')).toBe('/stocks/RELIANCE.NS');
    expect(screen.getByText('₹2,945.50')).toBeTruthy();
    expect(screen.getByText('↗ +10.00 (+0.34%)')).toBeTruthy();
  });

  it('says so when the watchlist is empty', async () => {
    renderApp(<WatchlistSidebar client={fakeWatchlist()} />);
    expect(await screen.findByText('No stocks in your watchlist yet.')).toBeTruthy();
  });

  it('adds a stock typed without the .NS suffix', async () => {
    const client = fakeWatchlist();
    renderApp(<WatchlistSidebar client={client} />);
    await screen.findByText('No stocks in your watchlist yet.');

    fireEvent.change(screen.getByRole('textbox', { name: 'Stock symbol' }), { target: { value: ' reliance ' } });
    fireEvent.click(screen.getByRole('button', { name: '+ Add' }));

    expect(await screen.findByRole('link', { name: 'RELIANCE.NS' })).toBeTruthy();
    expect(client.POST).toHaveBeenCalledWith('/watchlist', { body: { symbol: 'RELIANCE.NS' } });
    expect((screen.getByRole('textbox', { name: 'Stock symbol' }) as HTMLInputElement).value).toBe('');
  });

  it('explains when the symbol is not on the list', async () => {
    renderApp(<WatchlistSidebar client={fakeWatchlist()} />);
    await screen.findByText('No stocks in your watchlist yet.');
    fireEvent.change(screen.getByRole('textbox', { name: 'Stock symbol' }), { target: { value: 'nope' } });
    fireEvent.click(screen.getByRole('button', { name: '+ Add' }));
    expect(await screen.findByText('NOPE.NS is not on the Nifty 100 list.')).toBeTruthy();
  });

  it('removes a stock', async () => {
    renderApp(<WatchlistSidebar client={fakeWatchlist([reliance])} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Remove RELIANCE.NS' }));
    await waitFor(() => expect(screen.queryByRole('link', { name: 'RELIANCE.NS' })).toBeNull());
    expect(await screen.findByText('No stocks in your watchlist yet.')).toBeTruthy();
  });

  it('asks signed-out readers to sign in', async () => {
    renderApp(<WatchlistSidebar client={fakeWatchlist([], true)} />);
    expect(await screen.findByText('to keep a watchlist.')).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Sign in' }).getAttribute('href')).toBe('/sign-in');
  });
});
