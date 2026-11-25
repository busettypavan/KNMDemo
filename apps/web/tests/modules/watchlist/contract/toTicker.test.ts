import { toTicker } from '../../../../src/features/watchlist/WatchlistSidebar';

describe('watchlist symbol input', () => {
  it('adds the .NS suffix and upper-cases what the reader typed', () => {
    expect(toTicker('reliance')).toBe('RELIANCE.NS');
    expect(toTicker(' tcs ')).toBe('TCS.NS');
  });

  it('keeps a symbol that already has a suffix', () => {
    expect(toTicker('tcs.ns')).toBe('TCS.NS');
  });

  it('gives nothing for an empty entry', () => {
    expect(toTicker('   ')).toBe('');
  });
});
