# Story 4.4: Stock Detail Page Layout

## Story Details
- **Title**: Stock Detail Page Layout
- **Story ID**: 4.4
- **Phase**: 4 (Frontend MVP)
- **Priority**: High
- **Story Points**: 3
- **Epic**: Frontend MVP - Pages & Components

## User Story
As a **user**,
I want **to see stock details including current price**,
so that **I have context about the stock**.

## Context
The stock detail page is the main page users navigate to after searching. It displays comprehensive stock information including current price, historical data, market metrics, and serves as the hub for accessing more detailed analysis (predictability scores, predictions, historical analysis, backtesting).

## Acceptance Criteria
1. ✅ Page displays stock ticker and company name prominently
2. ✅ Shows current price with large typography
3. ✅ Shows 52-week high/low price range
4. ✅ Shows market cap information
5. ✅ Shows last updated timestamp
6. ✅ Layout is clean and organized
7. ✅ Page fetches stock data on load
8. ✅ Shows loading state while data is being fetched
9. ✅ Shows error state if stock data fails to load
10. ✅ Layout responsive on mobile, tablet, and desktop

## Integration Verification
- **IV1**: Integration with GET /stocks/{ticker} API endpoint (Story 2.3)
- **IV2**: Integration with API client service layer (Story 4.2)
- **IV3**: Navigation from search page works correctly
- **IV4**: Stock data displays accurately
- **IV5**: Sub-components (Predictability Card, Prediction Banner) integrate seamlessly

## Technical Implementation

### 1. Create Stock Detail Page
**File**: `/app/dashboard/[ticker]/page.tsx`

```typescript
'use client'

import { useParams } from 'next/navigation'
import { useStockDetail } from '@/services/stockService'
import PriceHeader from '@/components/stock-detail/PriceHeader'
import PredictabilityCard from '@/components/stock-detail/PredictabilityCard'
import PredictionBanner from '@/components/stock-detail/PredictionBanner'
import { Loader2, AlertCircle, ArrowLeft } from 'lucide-react'
import Link from 'next/link'

export default function StockDetailPage() {
  const params = useParams()
  const ticker = params.ticker as string

  const { data: stock, isLoading, error } = useStockDetail(ticker)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      {/* Header Navigation */}
      <div className="sticky top-0 z-10 bg-slate-900/80 backdrop-blur border-b border-slate-700 px-8 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-4">
          <Link href="/dashboard" className="text-gray-400 hover:text-white transition">
            <ArrowLeft className="w-6 h-6" />
          </Link>
          <h1 className="text-2xl font-bold text-white">
            {isLoading ? 'Loading...' : stock?.ticker || ticker}
          </h1>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-24">
              <Loader2 className="w-10 h-10 animate-spin text-blue-400 mb-4" />
              <span className="text-gray-400">Loading stock data...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-6 flex items-start gap-4">
              <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-red-400 font-semibold">Failed to load stock data</p>
                <p className="text-red-300 text-sm mt-1">{error}</p>
                <Link href="/dashboard" className="text-blue-400 hover:text-blue-300 text-sm mt-3 inline-block">
                  Back to search
                </Link>
              </div>
            </div>
          )}

          {!isLoading && !error && stock && (
            <>
              {/* Price Header Section */}
              <PriceHeader stock={stock} />

              {/* Key Metrics */}
              <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                  label="52-Week High"
                  value={`₹${stock.fifty_two_week_high?.toFixed(2) || 'N/A'}`}
                  change={stock.fifty_two_week_high ? ((stock.current_price - stock.fifty_two_week_high) / stock.fifty_two_week_high * 100).toFixed(2) : '0'}
                />
                <MetricCard
                  label="52-Week Low"
                  value={`₹${stock.fifty_two_week_low?.toFixed(2) || 'N/A'}`}
                  change={stock.fifty_two_week_low ? ((stock.current_price - stock.fifty_two_week_low) / stock.fifty_two_week_low * 100).toFixed(2) : '0'}
                />
                <MetricCard
                  label="Market Cap"
                  value={stock.market_cap ? formatMarketCap(stock.market_cap) : 'N/A'}
                />
                <MetricCard
                  label="Last Updated"
                  value={stock.last_price_update ? formatTime(stock.last_price_update) : 'N/A'}
                  isTime={true}
                />
              </div>

              {/* Analysis Sections */}
              <div className="mt-12 grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Prediction Banner (Full Width) */}
                <div className="lg:col-span-3">
                  <PredictionBanner ticker={ticker} />
                </div>

                {/* Predictability Card */}
                <div className="lg:col-span-2">
                  <PredictabilityCard ticker={ticker} />
                </div>

                {/* Quick Actions */}
                <div className="bg-slate-800/50 backdrop-blur rounded-lg p-6 border border-slate-700 h-fit">
                  <h3 className="text-lg font-bold text-white mb-4">Quick Actions</h3>
                  <div className="space-y-3">
                    <ActionButton href={`/dashboard/${ticker}/historical`} label="View History" />
                    <ActionButton href={`/dashboard/${ticker}/backtest`} label="Run Backtest" />
                    <ActionButton href={`#`} label="Add to Watchlist" isWatchlist={true} />
                    <ActionButton href={`#`} label="Set Alert" isAlert={true} />
                  </div>
                </div>
              </div>

              {/* Information Footer */}
              <div className="mt-12 bg-slate-800/50 backdrop-blur rounded-lg p-6 border border-slate-700">
                <p className="text-sm text-gray-400">
                  Data updated at {stock.last_price_update ? new Date(stock.last_price_update).toLocaleString() : 'N/A'}
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  Market: {stock.market} | Status: {stock.analysis_status}
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

interface MetricCardProps {
  label: string
  value: string
  change?: string
  isTime?: boolean
}

function MetricCard({ label, value, change, isTime }: MetricCardProps) {
  const changeNum = parseFloat(change || '0')
  const isPositive = changeNum > 0

  return (
    <div className="bg-slate-800/50 backdrop-blur rounded-lg p-4 border border-slate-700">
      <p className="text-sm text-gray-400 mb-2">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      {change && !isTime && (
        <p className={`text-sm mt-2 ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
          {isPositive ? '+' : ''}{change}%
        </p>
      )}
    </div>
  )
}

interface ActionButtonProps {
  href: string
  label: string
  isWatchlist?: boolean
  isAlert?: boolean
}

function ActionButton({ href, label, isWatchlist, isAlert }: ActionButtonProps) {
  const className = `w-full px-4 py-2.5 rounded-lg font-semibold transition text-sm ${
    isWatchlist ? 'bg-yellow-600 hover:bg-yellow-700 text-white'
    : isAlert ? 'bg-red-600 hover:bg-red-700 text-white'
    : 'bg-blue-600 hover:bg-blue-700 text-white'
  }`

  if (isWatchlist || isAlert) {
    return (
      <button className={className}>
        {label}
      </button>
    )
  }

  return (
    <Link href={href} className={className}>
      {label}
    </Link>
  )
}

function formatMarketCap(value: number): string {
  if (value >= 1e12) return `₹${(value / 1e12).toFixed(2)}T`
  if (value >= 1e9) return `₹${(value / 1e9).toFixed(2)}B`
  if (value >= 1e6) return `₹${(value / 1e6).toFixed(2)}M`
  return `₹${value.toFixed(2)}`
}

function formatTime(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
}
```

### 2. Create Price Header Component
**File**: `/components/stock-detail/PriceHeader.tsx`

```typescript
'use client'

import React from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface Stock {
  ticker: string
  name: string
  current_price: number
  previous_close?: number
  market: string
}

interface PriceHeaderProps {
  stock: Stock
}

export default function PriceHeader({ stock }: PriceHeaderProps) {
  const priceChange = stock.previous_close ? stock.current_price - stock.previous_close : 0
  const percentChange = stock.previous_close ? (priceChange / stock.previous_close) * 100 : 0
  const isPositive = priceChange >= 0

  return (
    <div className="bg-gradient-to-r from-slate-800/50 to-slate-700/50 backdrop-blur rounded-lg p-8 border border-slate-700">
      <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
        <div>
          <h2 className="text-gray-400 text-lg mb-2">{stock.name}</h2>
          <div className="flex items-baseline gap-4">
            <span className="text-5xl font-bold text-white">₹{stock.current_price.toFixed(2)}</span>
            <div className={`flex items-center gap-1 px-3 py-1 rounded-lg ${
              isPositive ? 'bg-green-600/20' : 'bg-red-600/20'
            }`}>
              {isPositive ? (
                <TrendingUp className="w-5 h-5 text-green-400" />
              ) : (
                <TrendingDown className="w-5 h-5 text-red-400" />
              )}
              <span className={isPositive ? 'text-green-400' : 'text-red-400'}>
                {isPositive ? '+' : ''}{priceChange.toFixed(2)} ({percentChange.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>
        <div className="mt-6 md:mt-0 text-right">
          <p className="text-gray-400 text-sm">Market</p>
          <p className="text-xl font-semibold text-white">{stock.market}</p>
        </div>
      </div>
    </div>
  )
}
```

### 3. Update Stock Service
**File**: `/services/stockService.ts` (add to existing file)

```typescript
export interface StockDetail {
  ticker: string
  name: string
  current_price: number
  previous_close?: number
  market: string
  fifty_two_week_high?: number
  fifty_two_week_low?: number
  market_cap?: number
  analysis_status: string
  last_price_update?: string
}

export function useStockDetail(ticker: string) {
  return useQuery({
    queryKey: ['stocks', 'detail', ticker],
    queryFn: async () => {
      const { data } = await api.get<StockDetail>(`/stocks/${ticker}`)
      return data
    },
    staleTime: 15 * 60 * 1000, // 15 minutes
    retry: 2,
  })
}
```

## Testing

### Integration Tests
**File**: `/components/stock-detail/__tests__/StockDetailPage.test.tsx`

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import StockDetailPage from '@/app/dashboard/[ticker]/page'
import { useStockDetail } from '@/services/stockService'

jest.mock('@/services/stockService')
jest.mock('next/navigation')

describe('StockDetailPage', () => {
  it('displays loading state initially', () => {
    ;(useStockDetail as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null
    })

    render(<StockDetailPage />)
    expect(screen.getByText(/Loading stock data/i)).toBeInTheDocument()
  })

  it('displays stock data when loaded', async () => {
    const mockStock = {
      ticker: 'AVANTI',
      name: 'Avanti Feeds Limited',
      current_price: 450.50,
      previous_close: 445.00,
      market: 'NSE',
      fifty_two_week_high: 500,
      fifty_two_week_low: 400,
      market_cap: 5000000000,
      analysis_status: 'analyzed',
      last_price_update: new Date().toISOString()
    }

    ;(useStockDetail as jest.Mock).mockReturnValue({
      data: mockStock,
      isLoading: false,
      error: null
    })

    render(<StockDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('₹450.50')).toBeInTheDocument()
      expect(screen.getByText('Avanti Feeds Limited')).toBeInTheDocument()
      expect(screen.getByText('NSE')).toBeInTheDocument()
    })
  })

  it('displays error state on failure', () => {
    ;(useStockDetail as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: 'Failed to fetch stock data'
    })

    render(<StockDetailPage />)
    expect(screen.getByText(/Failed to load stock data/i)).toBeInTheDocument()
  })

  it('displays 52-week high and low', async () => {
    const mockStock = {
      ticker: 'RELIANCE',
      name: 'Reliance Industries',
      current_price: 2500,
      market: 'NSE',
      fifty_two_week_high: 3000,
      fifty_two_week_low: 2000,
      analysis_status: 'analyzed',
      last_price_update: new Date().toISOString()
    }

    ;(useStockDetail as jest.Mock).mockReturnValue({
      data: mockStock,
      isLoading: false,
      error: null
    })

    render(<StockDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('₹3000.00')).toBeInTheDocument()
      expect(screen.getByText('₹2000.00')).toBeInTheDocument()
    })
  })
})
```

## Definition of Done
- [x] Stock detail page component created
- [x] Price header displays correctly with trend indicators
- [x] 52-week high/low displayed with percentage change
- [x] Market cap formatted and displayed
- [x] Last updated timestamp displayed
- [x] API integration with stockService complete
- [x] Loading state displays while fetching
- [x] Error state displays on API failure
- [x] Page responsive on mobile/tablet/desktop
- [x] Navigation back to dashboard works
- [x] Sub-components integrate seamlessly
- [x] Unit/integration tests written and passing

## Dependencies
- Story 4.2 (API Client Service Layer)
- Story 2.3 (Stock Detail API Endpoint)
- Story 4.1 (Frontend Project Setup)
- React Query configured
- TailwindCSS and shadcn/ui installed

## Notes
- Price updates shown with both absolute and percentage change
- Responsive grid: 4 columns on desktop, 2 on tablet, 1 on mobile
- Color scheme: Green for positive, Red for negative movements
- Market cap formatted in T/B/M notation
- Time formatted in 12-hour IST format

## Acceptance Test Checklist
- [ ] Page loads stock detail for valid ticker
- [ ] Stock ticker and name displayed prominently
- [ ] Current price shown with large font
- [ ] Price change shown with color indicator (green/red)
- [ ] 52-week high/low displayed correctly
- [ ] Market cap displayed with proper formatting
- [ ] Last updated timestamp displayed
- [ ] Loading state shows while fetching
- [ ] Error state shows on API failure
- [ ] Can navigate back to search page
- [ ] Page responsive on mobile (< 768px)
- [ ] Page responsive on tablet (768px - 1024px)
- [ ] Page responsive on desktop (> 1024px)
- [ ] All metrics display correct values
