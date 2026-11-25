// Nifty 100 list (REQ-340, WI-041): symbol, name, price and day change, sorted by symbol. Pages load as the reader
// scrolls (infinite scroll); a "Load more" button is the fallback when the browser has no IntersectionObserver.
// Signed-out readers are asked to sign in. Each symbol links to its stock page.
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Alert, AlertIcon, Box, Button, Heading, Link, Stack, Table, Tbody, Td, Th, Thead, Tr, Text } from '@chakra-ui/react';
import { api as defaultApi } from '../../api/client';

export interface StockItem {
  symbol: string;
  name: string;
  sector: string | null;
  price: number | null;
  dayChange: number | null;
  dayChangePct: number | null;
}

export interface StockListPage {
  items: StockItem[];
  nextCursor: string | null;
}

export interface StockClient {
  GET(
    path: '/stocks',
    init?: { params?: { query?: { limit?: number; after?: string } } }
  ): Promise<{ data?: StockListPage; error?: unknown; response: { ok: boolean; status: number } }>;
}

export const PAGE_SIZE = 100;

/** ₹ with two decimals in the Indian grouping, or a dash when no price is stored yet. */
export function formatPrice(value: number | null): string {
  if (value === null) return '—';
  return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/** Day change as an arrow, the amount and the percentage; a dash when there is no previous close. */
export function formatDayChange(change: number | null, pct: number | null): string {
  if (change === null || pct === null) return '—';
  const arrow = change > 0 ? '↗' : change < 0 ? '↘' : '→';
  const sign = change > 0 ? '+' : '';
  return `${arrow} ${sign}${change.toFixed(2)} (${sign}${pct.toFixed(2)}%)`;
}

function changeColour(change: number | null): string | undefined {
  if (change === null || change === 0) return undefined;
  return change > 0 ? 'green.600' : 'red.600';
}

type Status = 'loading' | 'idle' | 'signin' | 'error';

export interface StockListProps {
  client?: StockClient;
  pageSize?: number;
}

export function StockList({ client = defaultApi as unknown as StockClient, pageSize = PAGE_SIZE }: StockListProps) {
  const [items, setItems] = useState<StockItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>('loading');
  const inFlight = useRef(false);
  const sentinel = useRef<HTMLDivElement | null>(null);

  const loadPage = useCallback(
    async (after?: string) => {
      if (inFlight.current) return;
      inFlight.current = true;
      setStatus('loading');
      try {
        const { data, response } = await client.GET('/stocks', {
          params: { query: { limit: pageSize, ...(after ? { after } : {}) } },
        });
        if (response.status === 401) {
          setStatus('signin');
          return;
        }
        if (!response.ok || !data) {
          setStatus('error');
          return;
        }
        setItems((previous) => (after ? [...previous, ...data.items] : data.items));
        setNextCursor(data.nextCursor);
        setStatus('idle');
      } catch {
        setStatus('error');
      } finally {
        inFlight.current = false;
      }
    },
    [client, pageSize]
  );

  useEffect(() => {
    void loadPage();
  }, [loadPage]);

  // Load the next page when the sentinel below the table scrolls into view.
  useEffect(() => {
    const node = sentinel.current;
    if (!node || !nextCursor || typeof IntersectionObserver === 'undefined') return;
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) void loadPage(nextCursor);
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, [nextCursor, loadPage]);

  if (status === 'signin') {
    return (
      <Alert status="info" role="status">
        <AlertIcon />
        <Text>
          Sign in to see the Nifty 100 stocks. <Link as={RouterLink} to="/sign-in" color="blue.600">Sign in</Link>
        </Text>
      </Alert>
    );
  }

  return (
    <Stack spacing={4}>
      <Heading as="h1" size="lg">Nifty 100 stocks</Heading>
      {status === 'error' && (
        <Alert status="error" role="alert">
          <AlertIcon />
          Could not load stocks.{' '}
          <Button size="sm" ml={2} onClick={() => void loadPage(nextCursor ?? undefined)}>Try again</Button>
        </Alert>
      )}
      {status !== 'loading' && items.length === 0 && status !== 'error' && (
        <Text>No stocks to show yet.</Text>
      )}
      {items.length > 0 && (
        <Box overflowX="auto">
          <Table size="sm" aria-label="Nifty 100 stocks">
            <Thead>
              <Tr>
                <Th>Symbol</Th>
                <Th>Name</Th>
                <Th isNumeric>Price</Th>
                <Th>Day change</Th>
              </Tr>
            </Thead>
            <Tbody>
              {items.map((stock) => (
                <Tr key={stock.symbol}>
                  <Td fontWeight="semibold">
                    <Link as={RouterLink} to={`/stocks/${encodeURIComponent(stock.symbol)}`} color="blue.600">
                      {stock.symbol}
                    </Link>
                  </Td>
                  <Td>{stock.name}</Td>
                  <Td isNumeric>{formatPrice(stock.price)}</Td>
                  <Td color={changeColour(stock.dayChange)}>{formatDayChange(stock.dayChange, stock.dayChangePct)}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}
      {nextCursor && (
        <Box ref={sentinel}>
          <Button onClick={() => void loadPage(nextCursor)} isLoading={status === 'loading'} variant="outline">
            Load more
          </Button>
        </Box>
      )}
      {status === 'loading' && items.length === 0 && <Text role="status">Loading stocks…</Text>}
    </Stack>
  );
}
