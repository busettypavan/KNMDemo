import { initialStart, isUp, toChartData } from '../../../../src/features/stocks/chartData';

describe('price chart data', () => {
  it('parses dates as UTC and sorts the bars oldest first', () => {
    const data = toChartData([
      { date: '2026-06-02', open: 105, high: 111, low: 104, close: 110, volume: 2000 },
      { date: '2026-06-01', open: 99, high: 101, low: 98, close: 100, volume: 1000 },
    ]);
    expect(data.map((d) => d.date.toISOString().slice(0, 10))).toEqual(['2026-06-01', '2026-06-02']);
    expect(data[1].close).toBe(110);
    expect(data[1].volume).toBe(2000);
  });

  it('opens on the most recent bars', () => {
    expect(initialStart(250, 90)).toBe(160);
    expect(initialStart(30, 90)).toBe(0);
    expect(initialStart(0, 90)).toBe(0);
  });

  it('colours a candle up when the close is at or above the open', () => {
    expect(isUp({ open: 100, close: 101 })).toBe(true);
    expect(isUp({ open: 100, close: 100 })).toBe(true);
    expect(isUp({ open: 100, close: 99 })).toBe(false);
  });
});
