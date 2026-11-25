import React from 'react';
import { render } from '@testing-library/react';
import * as chartLib from 'react-financial-charts';
import { PriceChart } from '../../../../src/features/stocks/PriceChart';
import { type ChartDatum } from '../../../../src/features/stocks/chartData';

// Records the props each chart component receives, so the tests can check what the chart is asked to draw.
jest.mock('react-financial-charts', () => {
  const captured: Array<{ name: string; props: any }> = [];
  const make = (name: string) => (props: any) => {
    captured.push({ name, props });
    return require('react').createElement('div', { 'data-testid': name }, props.children);
  };
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
    __captured: captured,
    ChartCanvas: make('ChartCanvas'),
    Chart: make('Chart'),
    XAxis: make('XAxis'),
    YAxis: make('YAxis'),
    MouseCoordinateX: make('MouseCoordinateX'),
    MouseCoordinateY: make('MouseCoordinateY'),
    CandlestickSeries: make('CandlestickSeries'),
    BarSeries: make('BarSeries'),
    OHLCTooltip: make('OHLCTooltip'),
    CrossHairCursor: make('CrossHairCursor'),
    discontinuousTimeScaleProviderBuilder: builder,
    lastVisibleItemBasedZoomAnchor: () => 0,
  };
});

const captured = (chartLib as unknown as { __captured: Array<{ name: string; props: any }> }).__captured;
const UP = '#2f855a';
const DOWN = '#c53030';

function bars(count: number): ChartDatum[] {
  return Array.from({ length: count }, (_, i) => ({
    date: new Date(Date.UTC(2026, 0, 1 + i)),
    open: 100,
    high: 105,
    low: 95,
    close: i % 2 === 0 ? 101 : 99,
    volume: 1000 + i,
  }));
}

function prop(name: string, id?: number): any {
  const entry = captured.find((c) => c.name === name && (id === undefined || c.props.id === id));
  if (!entry) throw new Error(`${name} not rendered`);
  return entry.props;
}

beforeEach(() => {
  captured.length = 0;
});

describe('price chart', () => {
  it('renders nothing when there are no bars', () => {
    const { container } = render(<PriceChart symbol="RELIANCE.NS" data={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('opens on the most recent 90 bars and passes all bars to the canvas', () => {
    render(<PriceChart symbol="RELIANCE.NS" data={bars(120)} />);
    const canvas = prop('ChartCanvas');
    expect(canvas.data).toHaveLength(120);
    expect(canvas.xExtents).toEqual([30, 120]);
    expect(canvas.seriesName).toBe('RELIANCE.NS');
    expect(canvas.width).toBe(720); // not measured in jsdom: falls back to the default width
  });

  it('shows all bars when there are fewer than the visible count', () => {
    render(<PriceChart symbol="TCS.NS" data={bars(10)} />);
    expect(prop('ChartCanvas').xExtents).toEqual([0, 10]);
  });

  it('colours candles and volume bars by direction', () => {
    render(<PriceChart symbol="RELIANCE.NS" data={bars(3)} />);
    const up = { open: 1, close: 2 };
    const down = { open: 2, close: 1 };
    const candles = prop('CandlestickSeries');
    expect(candles.fill(up)).toBe(UP);
    expect(candles.fill(down)).toBe(DOWN);
    expect(candles.stroke(down)).toBe(DOWN);
    expect(candles.wickStroke(up)).toBe(UP);
    const volume = prop('BarSeries');
    expect(volume.yAccessor({ volume: 7 })).toBe(7);
    expect(volume.fillStyle(down)).toBe(DOWN);
  });

  it('draws the price chart above the volume chart and reads the ranges from the bars', () => {
    render(<PriceChart symbol="RELIANCE.NS" data={bars(3)} />);
    const price = prop('Chart', 1);
    expect(price.yExtents({ high: 5, low: 3 })).toEqual([5, 3]);
    const volume = prop('Chart', 2);
    expect(volume.origin(800, 450)).toEqual([0, 340]);
    expect(volume.yExtents({ volume: 9 })).toBe(9);
  });

  it('formats the axis labels and the cursor readouts', () => {
    render(<PriceChart symbol="RELIANCE.NS" data={bars(3)} />);
    expect(prop('MouseCoordinateY').displayFormat(110)).toBe('110.00');
    expect(prop('MouseCoordinateX').displayFormat(new Date(Date.UTC(2026, 5, 2)))).toBe('2026-06-02');
    // the volume chart's y-axis is the second one rendered
    const volumeAxis = captured.filter((c) => c.name === 'YAxis').pop()!.props;
    expect(typeof volumeAxis.tickFormat(1500000)).toBe('string');
  });
});
