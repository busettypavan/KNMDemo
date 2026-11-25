// Daily price bars as the chart needs them. Kept apart from the chart component so the mapping can be tested without
// loading the canvas library.

export interface PriceBar {
  date: string; // YYYY-MM-DD, as the API sends it
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartDatum {
  date: Date; // UTC midnight of the trading day
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/** Parses each YYYY-MM-DD as a UTC date and sorts the bars oldest first. */
export function toChartData(bars: PriceBar[]): ChartDatum[] {
  return bars
    .map((bar) => {
      const [year, month, day] = bar.date.split('-').map(Number);
      return {
        date: new Date(Date.UTC(year, month - 1, day)),
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
        volume: bar.volume,
      };
    })
    .sort((a, b) => a.date.getTime() - b.date.getTime());
}

/** Index of the first bar in view when the chart opens on the last `visible` bars. */
export function initialStart(count: number, visible: number): number {
  return Math.max(0, count - visible);
}

/** Candle direction: up when the close is at or above the open. */
export function isUp(bar: Pick<ChartDatum, 'open' | 'close'>): boolean {
  return bar.close >= bar.open;
}
