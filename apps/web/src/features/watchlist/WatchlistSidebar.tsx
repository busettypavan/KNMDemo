// The watchlist sidebar beside the stock pages (REQ-340, WI-041): the stocks the signed-in user follows, with price and
// day change, a link to each stock, a remove button, and an add box. Signed-out readers are asked to sign in.
import React, { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Alert, AlertIcon, Box, Button, FormControl, FormLabel, Heading, HStack, IconButton, Input, Link, Stack, Text } from '@chakra-ui/react';
import { api as defaultApi } from '../../api/client';
import { formatDayChange, formatPrice } from '../stocks/StockList';

export interface WatchlistEntry {
  symbol: string;
  name: string;
  price: number | null;
  dayChange: number | null;
  dayChangePct: number | null;
}

export interface WatchlistPage {
  items: WatchlistEntry[];
}

export interface WatchlistClient {
  GET(path: '/watchlist'): Promise<{ data?: WatchlistPage; response: { ok: boolean; status: number } }>;
  POST(
    path: '/watchlist',
    init: { body: { symbol: string } }
  ): Promise<{ data?: WatchlistPage; response: { ok: boolean; status: number } }>;
  DELETE(
    path: '/watchlist/{symbol}',
    init: { params: { path: { symbol: string } } }
  ): Promise<{ data?: WatchlistPage; response: { ok: boolean; status: number } }>;
}

/** What the reader types: "reliance" or "RELIANCE.NS". The list stores NSE tickers with the .NS suffix. */
export function toTicker(input: string): string {
  const symbol = input.trim().toUpperCase();
  if (!symbol) return '';
  return symbol.includes('.') ? symbol : `${symbol}.NS`;
}

type Status = 'loading' | 'ready' | 'signin' | 'error';

export interface WatchlistSidebarProps {
  client?: WatchlistClient;
}

export function WatchlistSidebar({ client = defaultApi as unknown as WatchlistClient }: WatchlistSidebarProps) {
  const [items, setItems] = useState<WatchlistEntry[]>([]);
  const [status, setStatus] = useState<Status>('loading');
  const [input, setInput] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const apply = useCallback((page: WatchlistPage | undefined) => {
    setItems(page?.items ?? []);
    setStatus('ready');
  }, []);

  useEffect(() => {
    let active = true;
    client
      .GET('/watchlist')
      .then(({ data, response }) => {
        if (!active) return;
        if (response.status === 401) return setStatus('signin');
        if (!response.ok || !data) return setStatus('error');
        apply(data);
      })
      .catch(() => active && setStatus('error'));
    return () => {
      active = false;
    };
  }, [client, apply]);

  const add = async (event: React.FormEvent) => {
    event.preventDefault();
    const symbol = toTicker(input);
    if (!symbol) return;
    setBusy(true);
    setMessage(null);
    try {
      const { data, response } = await client.POST('/watchlist', { body: { symbol } });
      if (response.status === 401) return setStatus('signin');
      if (response.status === 404) return setMessage(`${symbol} is not on the Nifty 100 list.`);
      if (!response.ok) return setMessage('Could not update your watchlist.');
      apply(data);
      setInput('');
    } catch {
      setMessage('Could not update your watchlist.');
    } finally {
      setBusy(false);
    }
  };

  const remove = async (symbol: string) => {
    setMessage(null);
    try {
      const { data, response } = await client.DELETE('/watchlist/{symbol}', { params: { path: { symbol } } });
      if (response.status === 401) return setStatus('signin');
      if (!response.ok) return setMessage('Could not update your watchlist.');
      apply(data);
    } catch {
      setMessage('Could not update your watchlist.');
    }
  };

  if (status === 'signin') {
    return (
      <Alert status="info" role="status" borderRadius="md">
        <AlertIcon />
        <Text fontSize="sm">
          <Link as={RouterLink} to="/sign-in" color="blue.600">Sign in</Link> to keep a watchlist.
        </Text>
      </Alert>
    );
  }

  return (
    <Box as="aside" aria-label="Watchlist" borderWidth="1px" borderRadius="md" p={4}>
      <Stack spacing={3}>
        <Heading as="h2" size="sm">Watchlist</Heading>
        <form onSubmit={add} aria-label="Add to watchlist">
          <FormControl>
            <FormLabel srOnly>Stock symbol</FormLabel>
            <HStack>
              <Input
                size="sm"
                placeholder="e.g. RELIANCE"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                aria-label="Stock symbol"
              />
              <Button size="sm" type="submit" isLoading={busy} variant="outline">+ Add</Button>
            </HStack>
          </FormControl>
        </form>
        {message && <Alert status="warning" role="alert" borderRadius="md"><AlertIcon />{message}</Alert>}
        {status === 'error' && <Alert status="error" role="alert" borderRadius="md"><AlertIcon />Could not load your watchlist.</Alert>}
        {status === 'ready' && items.length === 0 && <Text fontSize="sm">No stocks in your watchlist yet.</Text>}
        <Stack as="ul" spacing={2} listStyleType="none" m={0} p={0}>
          {items.map((item) => (
            <HStack as="li" key={item.symbol} justify="space-between" align="flex-start">
              <Box>
                <Link as={RouterLink} to={`/stocks/${encodeURIComponent(item.symbol)}`} color="blue.600" fontWeight="semibold" fontSize="sm">
                  {item.symbol}
                </Link>
                <Text fontSize="xs" color="gray.600">{formatPrice(item.price)}</Text>
                <Text fontSize="xs" color={item.dayChange === null || item.dayChange === 0 ? undefined : item.dayChange > 0 ? 'green.600' : 'red.600'}>
                  {formatDayChange(item.dayChange, item.dayChangePct)}
                </Text>
              </Box>
              <IconButton
                aria-label={`Remove ${item.symbol}`}
                icon={<Text as="span" aria-hidden>×</Text>}
                size="xs"
                variant="ghost"
                onClick={() => void remove(item.symbol)}
              />
            </HStack>
          ))}
        </Stack>
      </Stack>
    </Box>
  );
}
