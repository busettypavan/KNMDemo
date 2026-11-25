// Candlestick price chart with a volume bar chart below it (REQ-341, WI-041), drawn with react-financial-charts.
// Interactive: mouse wheel zooms, drag pans, the OHLC tooltip follows the cursor. The chart opens on the most recent
// VISIBLE_BARS and resizes with its container.
import React, { useLayoutEffect, useMemo, useRef, useState } from 'react';
import {
  BarSeries,
  CandlestickSeries,
  Chart,
  ChartCanvas,
  CrossHairCursor,
  MouseCoordinateX,
  MouseCoordinateY,
  OHLCTooltip,
  XAxis,
  YAxis,
  discontinuousTimeScaleProviderBuilder,
  lastVisibleItemBasedZoomAnchor,
} from 'react-financial-charts';
import { type ChartDatum, initialStart, isUp } from './chartData';

export const VISIBLE_BARS = 90;
const PRICE_HEIGHT = 340;
const VOLUME_HEIGHT = 110;
const MARGIN = { left: 56, right: 56, top: 16, bottom: 28 };
const UP = '#2f855a';
const DOWN = '#c53030';
const FALLBACK_WIDTH = 720;

export interface PriceChartProps {
  symbol: string;
  data: ChartDatum[];
  visibleBars?: number;
}

/** Width of the element, kept current with a ResizeObserver. 0 until measured. */
function useElementWidth(ref: React.RefObject<HTMLElement>): number {
  const [width, setWidth] = useState(0);
  useLayoutEffect(() => {
    const node = ref.current;
    if (!node) return;
    const measure = () => setWidth(Math.floor(node.clientWidth));
    measure();
    if (typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver(measure);
    observer.observe(node);
    return () => observer.disconnect();
  }, [ref]);
  return width;
}

const compact = new Intl.NumberFormat('en-IN', { notation: 'compact', maximumFractionDigits: 1 });

export function PriceChart({ symbol, data, visibleBars = VISIBLE_BARS }: PriceChartProps) {
  const frame = useRef<HTMLDivElement | null>(null);
  const measured = useElementWidth(frame);
  const width = measured || FALLBACK_WIDTH;
  const ratio = typeof window !== 'undefined' && window.devicePixelRatio ? window.devicePixelRatio : 1;

  const scale = useMemo(() => {
    const provider = discontinuousTimeScaleProviderBuilder()
      .inputDateAccessor((d: ChartDatum) => d.date)
      .utc();
    return provider(data);
  }, [data]);

  if (data.length === 0) return null;

  const { data: plotData, xScale, xAccessor, displayXAccessor } = scale;
  const first = xAccessor(plotData[initialStart(plotData.length, visibleBars)]);
  const last = xAccessor(plotData[plotData.length - 1]);
  const xExtents = [first, last + 1];

  return (
    <div ref={frame} style={{ width: '100%' }} data-testid="price-chart">
      <ChartCanvas
        width={width}
        height={PRICE_HEIGHT + VOLUME_HEIGHT}
        ratio={ratio}
        margin={MARGIN}
        data={plotData}
        displayXAccessor={displayXAccessor}
        xAccessor={xAccessor}
        xScale={xScale}
        xExtents={xExtents}
        seriesName={symbol}
        zoomAnchor={lastVisibleItemBasedZoomAnchor}
      >
        <Chart id={1} height={PRICE_HEIGHT} yExtents={(d: ChartDatum) => [d.high, d.low]}>
          <XAxis showGridLines gridLinesStrokeStyle="#e2e8f0" />
          <YAxis showGridLines gridLinesStrokeStyle="#e2e8f0" />
          <MouseCoordinateY at="right" orient="right" displayFormat={(v: number) => v.toFixed(2)} />
          <CandlestickSeries
            fill={(d: ChartDatum) => (isUp(d) ? UP : DOWN)}
            stroke={(d: ChartDatum) => (isUp(d) ? UP : DOWN)}
            wickStroke={(d: ChartDatum) => (isUp(d) ? UP : DOWN)}
          />
          <OHLCTooltip origin={[8, 16]} />
          <CrossHairCursor />
        </Chart>
        <Chart id={2} height={VOLUME_HEIGHT} origin={(_w: number, h: number) => [0, h - VOLUME_HEIGHT]} yExtents={(d: ChartDatum) => d.volume}>
          <XAxis showGridLines gridLinesStrokeStyle="#e2e8f0" />
          <YAxis ticks={3} tickFormat={(v: number) => compact.format(v)} />
          <BarSeries yAccessor={(d: ChartDatum) => d.volume} fillStyle={(d: ChartDatum) => (isUp(d) ? UP : DOWN)} />
          <MouseCoordinateX at="bottom" orient="bottom" displayFormat={(v: Date) => v.toISOString().slice(0, 10)} />
        </Chart>
      </ChartCanvas>
    </div>
  );
}
