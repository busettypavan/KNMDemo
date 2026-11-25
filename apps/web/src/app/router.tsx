// Scaffold-owned glue file (STORY-105). Modules register at the markers below; do not edit the marked lines by hand.
// knm:imports
import { Navigate } from 'react-router-dom';
import { AuthPage } from '../features/auth/AuthPage'; // knm:module accounts
import { StockList } from '../features/stocks/StockList'; // knm:module stock-list
import { StockDetail } from '../features/stocks/StockDetail'; // knm:module stock-list
import { StocksLayout } from '../features/stocks/StocksLayout'; // knm:module watchlist

export const router = [
  // knm:entries
  { id: 'home', path: '/', element: <Navigate to="/stocks" replace /> },
  { id: 'sign-in', path: '/sign-in', element: <AuthPage /> }, // knm:module accounts
  { id: 'stocks', path: '/stocks', element: <StocksLayout><StockList /></StocksLayout> }, // knm:module stock-list
  { id: 'stock-detail', path: '/stocks/:symbol', element: <StocksLayout><StockDetail /></StocksLayout> }, // knm:module stock-list
  // knm:entries-end
];
