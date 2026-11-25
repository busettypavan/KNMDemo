// The stock pages' frame: the page on the left and the watchlist sidebar on the right. On a phone the sidebar moves
// below the page.
import React from 'react';
import { Box, Flex } from '@chakra-ui/react';
import { WatchlistSidebar } from '../watchlist/WatchlistSidebar';

export function StocksLayout({ children }: { children?: React.ReactNode }) {
  return (
    <Flex direction={{ base: 'column', md: 'row' }} gap={6} align="flex-start">
      <Box flex="1" minW={0} w="100%">{children}</Box>
      <Box w={{ base: '100%', md: '260px' }} flexShrink={0}>
        <WatchlistSidebar />
      </Box>
    </Flex>
  );
}
