# Story 4.6: Prediction Banner Component

## Story Details
- **Title**: Prediction Banner Component
- **Story ID**: 4.6
- **Phase**: 4 (Frontend MVP)
- **Priority**: High
- **Story Points**: 3
- **Epic**: Frontend MVP - Pages & Components

## User Story
As a **user**,
I want **to see what move is predicted today**,
so that **I know the immediate trading opportunity**.

## Context
The Prediction Banner is a prominent, eye-catching component that displays the current prediction for a stock including predicted direction (UP/DOWN), expected magnitude (e.g., "+2% to +4%"), timing information, and historical win rate. This is the most actionable insight for traders and should be immediately visible on the stock detail page.

## Acceptance Criteria
1. ✅ Shows predicted direction (UP/DOWN) with clear icon
2. ✅ Shows expected move magnitude as a range
3. ✅ Shows timing information (same-day, next-day, lagged)
4. ✅ Shows historical win rate as percentage
5. ✅ Shows reasoning or confidence text
6. ✅ Color-coded: green for UP, red for DOWN
7. ✅ Fetches prediction from API endpoint
8. ✅ Shows loading state while fetching
9. ✅ Shows error state on API failure
10. ✅ Responsive on all screen sizes

## Integration Verification
- **IV1**: Integration with GET /stocks/{ticker}/prediction API (Story 2.5)
- **IV2**: Integration with API client service layer (Story 4.2)
- **IV3**: Displays correctly on stock detail page
- **IV4**: Updates when stock changes

## Technical Implementation

### 1. Create Prediction Banner Component
**File**: `/components/stock-detail/PredictionBanner.tsx`

```typescript
'use client'

import React from 'react'
import { usePrediction } from '@/services/predictionService'
import { TrendingUp, TrendingDown, Loader2, AlertCircle, Clock, TrendingUpIcon } from 'lucide-react'

interface PredictionBannerProps {
  ticker: string
}

interface PredictionData {
  direction: 'UP' | 'DOWN'
  magnitude_min: number
  magnitude_max: number
  timing: 'same-day' | 'next-day' | 'lagged'
  win_rate: number
  confidence: number
  reasoning?: string
}

function getTimingLabel(timing: string): string {
  switch (timing) {
    case 'same-day':
      return 'Same Day'
    case 'next-day':
      return 'Next Trading Day'
    case 'lagged':
      return '2-5 Days'
    default:
      return 'Unknown'
  }
}

function getTimingIcon(timing: string) {
  return <Clock className="w-5 h-5" />
}

export default function PredictionBanner({ ticker }: PredictionBannerProps) {
  const { data, isLoading, error } = usePrediction(ticker)

  if (isLoading) {
    return (
      <div className="bg-slate-800/50 backdrop-blur rounded-lg p-8 border border-slate-700 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-blue-400 mr-3" />
        <span className="text-gray-400">Loading prediction...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-900/20 backdrop-blur rounded-lg p-6 border border-red-500/30 flex items-start gap-4">
        <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-red-400 font-semibold">Failed to load prediction</p>
          <p className="text-red-300 text-sm mt-1">{error}</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return null
  }

  const isUp = data.direction === 'UP'
  const bgGradient = isUp
    ? 'from-green-900/30 to-emerald-900/30 border-green-500/30'
    : 'from-red-900/30 to-rose-900/30 border-red-500/30'
  const textColor = isUp ? 'text-green-400' : 'text-red-400'
  const iconBg = isUp ? 'bg-green-500/20' : 'bg-red-500/20'

  return (
    <div className={`bg-gradient-to-r ${bgGradient} backdrop-blur rounded-lg p-8 border`}>
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
        {/* Direction and Magnitude */}
        <div className="flex items-start gap-6">
          <div className={`${iconBg} rounded-lg p-4 flex-shrink-0`}>
            {isUp ? (
              <TrendingUp className={`w-8 h-8 ${textColor}`} />
            ) : (
              <TrendingDown className={`w-8 h-8 ${textColor}`} />
            )}
          </div>

          <div>
            <p className="text-gray-400 text-sm uppercase tracking-wide mb-2">Today's Prediction</p>
            <div className="flex items-baseline gap-2 mb-3">
              <p className={`text-3xl font-bold ${textColor}`}>
                {isUp ? '↑' : '↓'}
              </p>
              <p className={`text-3xl font-bold ${textColor}`}>
                {data.magnitude_min > 0 ? '+' : ''}{data.magnitude_min.toFixed(1)}% to {data.magnitude_max > 0 ? '+' : ''}{data.magnitude_max.toFixed(1)}%
              </p>
            </div>
            <p className="text-white font-semibold text-lg">
              {isUp ? 'Expected Upward Movement' : 'Expected Downward Movement'}
            </p>
          </div>
        </div>

        {/* Timing and Win Rate */}
        <div className="lg:text-right space-y-4">
          <div className="bg-slate-800/30 rounded-lg p-4">
            <p className="text-gray-400 text-xs uppercase tracking-wide mb-2">Timing</p>
            <div className="flex items-center gap-2">
              {getTimingIcon(data.timing)}
              <p className="text-white font-semibold">
                {getTimingLabel(data.timing)}
              </p>
            </div>
          </div>

          <div className="bg-slate-800/30 rounded-lg p-4">
            <p className="text-gray-400 text-xs uppercase tracking-wide mb-2">Historical Win Rate</p>
            <p className={`text-2xl font-bold ${textColor}`}>
              {data.win_rate}%
            </p>
          </div>
        </div>
      </div>

      {/* Confidence Bar */}
      <div className="mt-6 pt-6 border-t border-slate-700/50">
        <div className="flex items-center justify-between mb-2">
          <p className="text-gray-400 text-sm">Prediction Confidence</p>
          <p className="text-white font-semibold">{data.confidence}%</p>
        </div>
        <div className="w-full bg-slate-700/30 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              isUp ? 'bg-gradient-to-r from-green-500 to-emerald-500'
              : 'bg-gradient-to-r from-red-500 to-rose-500'
            }`}
            style={{ width: `${data.confidence}%` }}
          />
        </div>
      </div>

      {/* Reasoning */}
      {data.reasoning && (
        <div className="mt-4 pt-4 border-t border-slate-700/50">
          <p className="text-gray-400 text-xs uppercase tracking-wide mb-2">Reasoning</p>
          <p className="text-gray-300 text-sm">{data.reasoning}</p>
        </div>
      )}

      {/* Disclaimer */}
      <div className="mt-4 pt-4 border-t border-slate-700/50">
        <p className="text-gray-500 text-xs">
          Past performance does not guarantee future results. This prediction is based on historical patterns and should not be considered financial advice.
        </p>
      </div>
    </div>
  )
}
```

### 2. Update Prediction Service
**File**: `/services/predictionService.ts` (add to existing file)

```typescript
export interface Prediction {
  direction: 'UP' | 'DOWN'
  magnitude_min: number
  magnitude_max: number
  timing: 'same-day' | 'next-day' | 'lagged'
  win_rate: number
  confidence: number
  reasoning?: string
}

export function usePrediction(ticker: string) {
  return useQuery({
    queryKey: ['stocks', 'prediction', ticker],
    queryFn: async () => {
      const { data } = await api.get<Prediction>(
        `/stocks/${ticker}/prediction`
      )
      return data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  })
}
```

### 3. Add to Stock Detail Page
**File**: `/app/dashboard/[ticker]/page.tsx` (update imports and JSX)

```typescript
// Add to imports
import PredictionBanner from '@/components/stock-detail/PredictionBanner'

// In the JSX, add in the analysis sections:
{/* Prediction Banner (Full Width) */}
<div className="lg:col-span-3">
  <PredictionBanner ticker={ticker} />
</div>
```

## Testing

### Unit Tests
**File**: `/components/stock-detail/__tests__/PredictionBanner.test.tsx`

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import PredictionBanner from '../PredictionBanner'
import { usePrediction } from '@/services/predictionService'

jest.mock('@/services/predictionService')

describe('PredictionBanner', () => {
  const mockPredictionUp = {
    direction: 'UP' as const,
    magnitude_min: 2.0,
    magnitude_max: 4.0,
    timing: 'same-day' as const,
    win_rate: 72,
    confidence: 85,
    reasoning: 'Strong bullish pattern detected with positive news catalyst'
  }

  const mockPredictionDown = {
    direction: 'DOWN' as const,
    magnitude_min: -1.5,
    magnitude_max: -3.0,
    timing: 'next-day' as const,
    win_rate: 65,
    confidence: 70,
    reasoning: 'Bearish technical setup with resistance at current levels'
  }

  it('displays loading state initially', () => {
    ;(usePrediction as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null
    })

    render(<PredictionBanner ticker="AVANTI" />)
    expect(screen.getByText(/Loading prediction/i)).toBeInTheDocument()
  })

  it('displays upward prediction correctly', async () => {
    ;(usePrediction as jest.Mock).mockReturnValue({
      data: mockPredictionUp,
      isLoading: false,
      error: null
    })

    render(<PredictionBanner ticker="AVANTI" />)

    await waitFor(() => {
      expect(screen.getByText(/Expected Upward Movement/i)).toBeInTheDocument()
      expect(screen.getByText('+2.0% to +4.0%')).toBeInTheDocument()
      expect(screen.getByText('72%')).toBeInTheDocument()
      expect(screen.getByText('Same Day')).toBeInTheDocument()
    })
  })

  it('displays downward prediction correctly', async () => {
    ;(usePrediction as jest.Mock).mockReturnValue({
      data: mockPredictionDown,
      isLoading: false,
      error: null
    })

    render(<PredictionBanner ticker="AVANTI" />)

    await waitFor(() => {
      expect(screen.getByText(/Expected Downward Movement/i)).toBeInTheDocument()
      expect(screen.getByText('-1.5% to -3.0%')).toBeInTheDocument()
      expect(screen.getByText('65%')).toBeInTheDocument()
      expect(screen.getByText('Next Trading Day')).toBeInTheDocument()
    })
  })

  it('displays confidence bar with correct width', async () => {
    ;(usePrediction as jest.Mock).mockReturnValue({
      data: mockPredictionUp,
      isLoading: false,
      error: null
    })

    const { container } = render(<PredictionBanner ticker="AVANTI" />)

    await waitFor(() => {
      const confidenceBar = container.querySelector('[style*="width"]')
      expect(confidenceBar).toHaveStyle('width: 85%')
    })
  })

  it('displays reasoning when available', async () => {
    ;(usePrediction as jest.Mock).mockReturnValue({
      data: mockPredictionUp,
      isLoading: false,
      error: null
    })

    render(<PredictionBanner ticker="AVANTI" />)

    await waitFor(() => {
      expect(screen.getByText(/Strong bullish pattern detected/i)).toBeInTheDocument()
    })
  })

  it('displays error on API failure', () => {
    ;(usePrediction as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: 'Failed to fetch prediction'
    })

    render(<PredictionBanner ticker="AVANTI" />)
    expect(screen.getByText(/Failed to load prediction/i)).toBeInTheDocument()
  })

  it('shows green colors for UP direction', async () => {
    ;(usePrediction as jest.Mock).mockReturnValue({
      data: mockPredictionUp,
      isLoading: false,
      error: null
    })

    const { container } = render(<PredictionBanner ticker="AVANTI" />)

    await waitFor(() => {
      const greenElements = container.querySelectorAll('.text-green-400')
      expect(greenElements.length).toBeGreaterThan(0)
    })
  })

  it('shows red colors for DOWN direction', async () => {
    ;(usePrediction as jest.Mock).mockReturnValue({
      data: mockPredictionDown,
      isLoading: false,
      error: null
    })

    const { container } = render(<PredictionBanner ticker="AVANTI" />)

    await waitFor(() => {
      const redElements = container.querySelectorAll('.text-red-400')
      expect(redElements.length).toBeGreaterThan(0)
    })
  })

  it('handles different timing values', async () => {
    const laggedPrediction = {
      ...mockPredictionUp,
      timing: 'lagged' as const
    }

    ;(usePrediction as jest.Mock).mockReturnValue({
      data: laggedPrediction,
      isLoading: false,
      error: null
    })

    render(<PredictionBanner ticker="AVANTI" />)

    await waitFor(() => {
      expect(screen.getByText('2-5 Days')).toBeInTheDocument()
    })
  })
})
```

### Integration Tests
**File**: `/app/dashboard/__tests__/[ticker].integration.test.tsx`

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import StockDetailPage from '@/app/dashboard/[ticker]/page'
import { useStockDetail } from '@/services/stockService'
import { usePrediction } from '@/services/predictionService'

jest.mock('@/services/stockService')
jest.mock('@/services/predictionService')
jest.mock('next/navigation')

describe('Stock Detail Page - Prediction Banner Integration', () => {
  const mockStock = {
    ticker: 'AVANTI',
    name: 'Avanti Feeds Limited',
    current_price: 450.50,
    market: 'NSE',
    analysis_status: 'analyzed',
    last_price_update: new Date().toISOString()
  }

  const mockPrediction = {
    direction: 'UP' as const,
    magnitude_min: 2.0,
    magnitude_max: 4.0,
    timing: 'same-day' as const,
    win_rate: 72,
    confidence: 85,
    reasoning: 'Bullish technical setup'
  }

  it('displays both stock data and prediction together', async () => {
    ;(useStockDetail as jest.Mock).mockReturnValue({
      data: mockStock,
      isLoading: false,
      error: null
    })

    ;(usePrediction as jest.Mock).mockReturnValue({
      data: mockPrediction,
      isLoading: false,
      error: null
    })

    render(<StockDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('AVANTI')).toBeInTheDocument()
      expect(screen.getByText(/Expected Upward Movement/i)).toBeInTheDocument()
    })
  })
})
```

## Definition of Done
- [x] Prediction banner component created
- [x] Direction (UP/DOWN) displayed with icon
- [x] Magnitude range displayed prominently
- [x] Timing information displayed with label
- [x] Win rate displayed as percentage
- [x] Confidence level shown with progress bar
- [x] Color scheme applied (green for UP, red for DOWN)
- [x] API integration with predictionService complete
- [x] Loading state displays while fetching
- [x] Error state displays on API failure
- [x] Reasoning/confidence text displayed when available
- [x] Disclaimer message included
- [x] Component responsive on all screen sizes
- [x] Component integrated into stock detail page
- [x] Unit tests written and passing
- [x] Integration tests written and passing

## Dependencies
- Story 4.2 (API Client Service Layer)
- Story 2.5 (Prediction Endpoint)
- Story 4.4 (Stock Detail Page)
- React Query configured
- TailwindCSS installed
- Lucide React icons

## Notes
- Banner spans full width on detail page
- Gradient backgrounds for visual impact
- Color scheme: Green (#10b981) for UP, Red (#ef4444) for DOWN
- Confidence bar uses gradient matching direction
- Win rate displayed as integer percentage
- Magnitude range displayed with +/- signs
- Timing labels translated to user-friendly text
- Disclaimer included to manage expectations

## Acceptance Test Checklist
- [ ] Banner shows predicted direction (UP/DOWN)
- [ ] Direction icon visible and correct color
- [ ] Magnitude range displayed (e.g., "+2.0% to +4.0%")
- [ ] Timing displayed correctly (Same Day, Next Day, 2-5 Days)
- [ ] Win rate displayed as percentage
- [ ] Confidence level shown with filled progress bar
- [ ] Green background for UP predictions
- [ ] Red background for DOWN predictions
- [ ] Loading state shows while fetching
- [ ] Error state shows on API failure
- [ ] Reasoning text displays when available
- [ ] Disclaimer message visible
- [ ] Component responsive on mobile
- [ ] Component responsive on tablet
- [ ] Component responsive on desktop
- [ ] Integrates seamlessly on detail page
