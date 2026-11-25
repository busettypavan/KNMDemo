// Stand-in for react-financial-charts in jest. The real package is ESM and draws on a canvas, which jsdom does not
// provide. The app-level tests load the router, so every name the chart uses gets an empty component here. Tests that
// check the chart's own props replace this with jest.mock.

const empty = () => null;

export const ChartCanvas = empty;
export const Chart = empty;
export const XAxis = empty;
export const YAxis = empty;
export const MouseCoordinateX = empty;
export const MouseCoordinateY = empty;
export const CandlestickSeries = empty;
export const BarSeries = empty;
export const OHLCTooltip = empty;
export const CrossHairCursor = empty;
export const lastVisibleItemBasedZoomAnchor = () => 0;

export function discontinuousTimeScaleProviderBuilder() {
  const provider: any = (data: any[]) => ({
    data,
    xScale: null,
    xAccessor: (d: any) => data.indexOf(d),
    displayXAccessor: (d: any) => d.date,
  });
  provider.inputDateAccessor = () => provider;
  provider.utc = () => provider;
  return provider;
}
