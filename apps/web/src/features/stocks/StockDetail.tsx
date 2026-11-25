// One stock's page at /stocks/:symbol: name, the latest close, and the candlestick and volume chart (REQ-341).
// Shows a spinner while the bars load and a message for each failure (not found, sign-in, other errors).
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import { Alert, AlertIcon, Box, Button, Heading, Link, Spinner, Stack, Text } from '@chakra-ui/react';
import { api as defaultApi } from '../../api/client';
import { type PriceBar, toChartData } from './chartData';
import { PriceChart } from './PriceChart';

export interface PriceSeries {
  symbol: string;
  name: string;
  bars: PriceBar[];
  stale: boolean; // true when today's refresh failed and these are the bars stored before it
}

export interface PriceClient {
  GET(
    path: '/stocks/{symbol}/prices',
    init: { params: { path: { symbol: string }; query?: { limit?: number } } }
  ): Promise<{ data?: PriceSeries; response: { ok: boolean; status: number } }>;
}

type Status = 'loading' | 'ready' | 'not-found' | 'signin' | 'unavailable' | 'error';

export interface StockDetailProps {
  client?: PriceClient;
}

export function StockDetail({ client = defaultApi as unknown as PriceClient }: StockDetailProps) {
  const { symbol = '' } = useParams();
  const [series, setSeries] = useState<PriceSeries | null>(null);
  const [status, setStatus] = useState<Status>('loading');
  const inFlight = useRef(false);

  const load = useCallback(async () => {
    if (inFlight.current) return;
    inFlight.current = true;
    setStatus('loading');
    try {
      const { data, response } = await client.GET('/stocks/{symbol}/prices', {
        params: { path: { symbol }, query: { limit: 250 } },
      });
      if (response.status === 401) return setStatus('signin');
      if (response.status === 404) return setStatus('not-found');
      if (response.status === 503) return setStatus('unavailable');
      if (!response.ok || !data) return setStatus('error');
      setSeries(data);
      setStatus('ready');
    } catch {
      setStatus('error');
    } finally {
      inFlight.current = false;
    }
  }, [client, symbol]);

  useEffect(() => {
    setSeries(null);
    void load();
  }, [load]);

  const chartData = useMemo(() => (series ? toChartData(series.bars) : []), [series]);
  const latest = chartData[chartData.length - 1];

  if (status === 'signin') {
    return (
      <Alert status="info" role="status">
        <AlertIcon />
        <Text>
          Sign in to see price charts. <Link as={RouterLink} to="/sign-in" color="blue.600">Sign in</Link>
        </Text>
      </Alert>
    );
  }

  return (
    <Stack spacing={4}>
      <Link as={RouterLink} to="/stocks" color="blue.600" fontSize="sm">← All stocks</Link>
      {status === 'not-found' && <Alert status="warning" role="alert"><AlertIcon />This stock is not on the list.</Alert>}
      {status === 'unavailable' && (
        <Alert status="warning" role="alert">
          <AlertIcon />
          Price data is not available right now. Try again later.{' '}
          <Button size="sm" ml={2} onClick={() => void load()}>Try again</Button>
        </Alert>
      )}
      {status === 'error' && (
        <Alert status="error" role="alert">
          <AlertIcon />
          Could not load price data.{' '}
          <Button size="sm" ml={2} onClick={() => void load()}>Try again</Button>
        </Alert>
      )}
      {status === 'loading' && (
        <Box role="status" display="flex" alignItems="center" gap={3}>
          <Spinner size="sm" />
          <Text>Loading price chart…</Text>
        </Box>
      )}
      {status === 'ready' && series && (
        <>
          <Heading as="h1" size="lg">
            {series.name} <Text as="span" color="gray.500" fontSize="md">{series.symbol}</Text>
          </Heading>
          {series.stale && (
            <Alert status="info" role="status">
              <AlertIcon />
              Showing saved prices. The latest refresh failed.
            </Alert>
          )}
          {latest ? (
            <Text>
              Last close <strong>₹{latest.close.toFixed(2)}</strong> on {latest.date.toISOString().slice(0, 10)}
            </Text>
          ) : null}
          {chartData.length > 0 ? (
            <PriceChart symbol={series.symbol} data={chartData} />
          ) : (
            <Text>No price data yet.</Text>
          )}
        </>
      )}
    </Stack>
  );
}
