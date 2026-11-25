import { formatDayChange, formatPrice } from '../../../../src/features/stocks/StockList';

describe('stock list formatting', () => {
  it('shows the price in rupees with Indian grouping', () => {
    expect(formatPrice(2945.5)).toBe('₹2,945.50');
    expect(formatPrice(1140.1)).toBe('₹1,140.10');
  });

  it('shows a dash when no price is stored', () => {
    expect(formatPrice(null)).toBe('—');
    expect(formatDayChange(null, null)).toBe('—');
  });

  it('shows the day change as arrow, amount and percentage', () => {
    expect(formatDayChange(10, 10)).toBe('↗ +10.00 (+10.00%)');
    expect(formatDayChange(-12.5, -1.81)).toBe('↘ -12.50 (-1.81%)');
    expect(formatDayChange(0, 0)).toBe('→ 0.00 (0.00%)');
  });
});
