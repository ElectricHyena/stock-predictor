# Story 4.5: Predictability Score Card Component

## Story Details
- **Title**: Predictability Score Card Component
- **Story ID**: 4.5
- **Phase**: 4 (Frontend MVP)
- **Priority**: High
- **Story Points**: 4
- **Epic**: Frontend MVP - Pages & Components

## User Story
As a **user**,
I want **to see the predictability score prominently**,
so that **I immediately know if this stock is tradeable**.

## Context
The Predictability Score Card is a critical component that displays the overall predictability of a stock along with four sub-component scores (information availability, pattern consistency, timing accuracy, direction confidence). It uses a circular gauge visualization with color coding to make it immediately clear whether a stock is worth trading.

## Acceptance Criteria
1. ✅ Large circular gauge showing 0-100 predictability score
2. ✅ Color-coded: green > 75, yellow 50-75, red < 50
3. ✅ Shows 4 sub-scores (info, pattern, timing, direction)
4. ✅ Shows confidence level (0-100)
5. ✅ Shows recommendation text (TRADE_THIS, MAYBE, AVOID)
6. ✅ Fetches data from predictability score endpoint
7. ✅ Shows loading state while fetching
8. ✅ Shows error state on API failure
9. ✅ Displays with gradient background
10. ✅ Responsive on all screen sizes

## Integration Verification
- **IV1**: Integration with GET /stocks/{ticker}/predictability-score API (Story 2.4)
- **IV2**: Integration with API client service layer (Story 4.2)
- **IV3**: Displays correctly on stock detail page
- **IV4**: Updates when stock changes

## Technical Implementation

### 1. Create Predictability Card Component
**File**: `/components/stock-detail/PredictabilityCard.tsx`

```typescript
'use client'

import React from 'react'
import { usePredictabilityScore } from '@/services/predictionService'
import { Loader2, AlertCircle } from 'lucide-react'

interface PredictabilityCardProps {
  ticker: string
}

interface PredictabilityData {
  score: number
  confidence: number
  recommendation: 'TRADE_THIS' | 'MAYBE' | 'AVOID'
  sub_scores: {
    information: number
    pattern: number
    timing: number
    direction: number
  }
}

function getScoreColor(score: number): string {
  if (score > 75) return 'from-green-500 to-emerald-600'
  if (score > 50) return 'from-yellow-500 to-amber-600'
  return 'from-red-500 to-rose-600'
}

function getRecommendationText(rec: string): string {
  switch (rec) {
    case 'TRADE_THIS':
      return 'Strong Trading Signal'
    case 'MAYBE':
      return 'Moderate Trading Signal'
    case 'AVOID':
      return 'Weak Trading Signal'
    default:
      return 'Unknown'
  }
}

function getRecommendationColor(rec: string): string {
  switch (rec) {
    case 'TRADE_THIS':
      return 'text-green-400'
    case 'MAYBE':
      return 'text-yellow-400'
    case 'AVOID':
      return 'text-red-400'
    default:
      return 'text-gray-400'
  }
}

export default function PredictabilityCard({ ticker }: PredictabilityCardProps) {
  const { data, isLoading, error } = usePredictabilityScore(ticker)

  return (
    <div className="bg-slate-800/50 backdrop-blur rounded-lg border border-slate-700 overflow-hidden">
      <div className="p-6">
        <h3 className="text-lg font-bold text-white mb-6">Predictability Score</h3>

        {isLoading && (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-400 mb-3" />
            <span className="text-gray-400 text-sm">Loading predictability data...</span>
          </div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-400 text-sm font-semibold">Failed to load predictability score</p>
              <p className="text-red-300 text-xs mt-1">{error}</p>
            </div>
          </div>
        )}

        {!isLoading && !error && data && (
          <>
            {/* Circular Gauge */}
            <div className="flex flex-col items-center mb-8">
              <CircularGauge score={data.score} />
              <div className="text-center mt-4">
                <p className={`text-2xl font-bold ${
                  data.score > 75 ? 'text-green-400'
                  : data.score > 50 ? 'text-yellow-400'
                  : 'text-red-400'
                }`}>
                  {data.score}
                </p>
                <p className="text-gray-400 text-sm mt-1">Overall Score</p>
              </div>
            </div>

            {/* Recommendation */}
            <div className="bg-slate-700/50 rounded-lg p-4 mb-6">
              <p className="text-gray-400 text-xs uppercase tracking-wide mb-2">Recommendation</p>
              <p className={`text-lg font-semibold ${getRecommendationColor(data.recommendation)}`}>
                {getRecommendationText(data.recommendation)}
              </p>
            </div>

            {/* Confidence */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-400 text-sm">Confidence</p>
                <p className="text-white font-semibold">{data.confidence}%</p>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${data.confidence}%` }}
                />
              </div>
            </div>

            {/* Sub-Scores */}
            <div className="border-t border-slate-700 pt-6">
              <p className="text-gray-400 text-sm font-semibold mb-4">Component Scores</p>
              <div className="space-y-4">
                <SubScoreBar
                  label="Information Availability"
                  score={data.sub_scores.information}
                />
                <SubScoreBar
                  label="Pattern Consistency"
                  score={data.sub_scores.pattern}
                />
                <SubScoreBar
                  label="Timing Accuracy"
                  score={data.sub_scores.timing}
                />
                <SubScoreBar
                  label="Direction Confidence"
                  score={data.sub_scores.direction}
                />
              </div>
            </div>

            {/* Weighting Info */}
            <div className="border-t border-slate-700 mt-6 pt-4">
              <p className="text-gray-500 text-xs">
                Score weighted as: 30% Information + 25% Pattern + 25% Timing + 20% Direction
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

interface CircularGaugeProps {
  score: number
}

function CircularGauge({ score }: CircularGaugeProps) {
  const radius = 60
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (score / 100) * circumference
  const color = score > 75 ? '#10b981' : score > 50 ? '#eab308' : '#ef4444'

  return (
    <svg width="160" height="160" viewBox="0 0 160 160">
      {/* Background circle */}
      <circle
        cx="80"
        cy="80"
        r={radius}
        fill="none"
        stroke="rgba(71, 85, 105, 0.3)"
        strokeWidth="8"
      />

      {/* Progress circle */}
      <circle
        cx="80"
        cy="80"
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth="8"
        strokeDasharray={circumference}
        strokeDashoffset={strokeDashoffset}
        strokeLinecap="round"
        style={{
          transform: 'rotate(-90deg)',
          transformOrigin: '80px 80px',
          transition: 'stroke-dashoffset 0.5s ease'
        }}
      />
    </svg>
  )
}

interface SubScoreBarProps {
  label: string
  score: number
}

function SubScoreBar({ label, score }: SubScoreBarProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <p className="text-gray-400 text-sm">{label}</p>
        <span className="text-white font-semibold text-sm">{score}</span>
      </div>
      <div className="w-full bg-slate-700 rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full transition-all ${
            score > 75 ? 'bg-green-500'
            : score > 50 ? 'bg-yellow-500'
            : 'bg-red-500'
          }`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  )
}
```

### 2. Create Prediction Service Hook
**File**: `/services/predictionService.ts`

```typescript
import { useQuery } from '@tanstack/react-query'
import api from './api'

export interface PredictabilityScore {
  score: number
  confidence: number
  recommendation: 'TRADE_THIS' | 'MAYBE' | 'AVOID'
  sub_scores: {
    information: number
    pattern: number
    timing: number
    direction: number
  }
}

export function usePredictabilityScore(ticker: string) {
  return useQuery({
    queryKey: ['stocks', 'predictability', ticker],
    queryFn: async () => {
      const { data } = await api.get<PredictabilityScore>(
        `/stocks/${ticker}/predictability-score`
      )
      return data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  })
}
```

### 3. Add to Stock Detail Page
**File**: `/app/dashboard/[ticker]/page.tsx` (update existing)

```typescript
// Add to imports
import PredictabilityCard from '@/components/stock-detail/PredictabilityCard'

// In the JSX, add this in the analysis sections:
<div className="lg:col-span-2">
  <PredictabilityCard ticker={ticker} />
</div>
```

## Testing

### Unit Tests
**File**: `/components/stock-detail/__tests__/PredictabilityCard.test.tsx`

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import PredictabilityCard from '../PredictabilityCard'
import { usePredictabilityScore } from '@/services/predictionService'

jest.mock('@/services/predictionService')

describe('PredictabilityCard', () => {
  const mockScoreData = {
    score: 78,
    confidence: 85,
    recommendation: 'TRADE_THIS' as const,
    sub_scores: {
      information: 80,
      pattern: 75,
      timing: 85,
      direction: 70
    }
  }

  it('displays loading state initially', () => {
    ;(usePredictabilityScore as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null
    })

    render(<PredictabilityCard ticker="AVANTI" />)
    expect(screen.getByText(/Loading predictability data/i)).toBeInTheDocument()
  })

  it('displays score and recommendation', async () => {
    ;(usePredictabilityScore as jest.Mock).mockReturnValue({
      data: mockScoreData,
      isLoading: false,
      error: null
    })

    render(<PredictabilityCard ticker="AVANTI" />)

    await waitFor(() => {
      expect(screen.getByText('78')).toBeInTheDocument()
      expect(screen.getByText('Strong Trading Signal')).toBeInTheDocument()
    })
  })

  it('displays all sub-scores', async () => {
    ;(usePredictabilityScore as jest.Mock).mockReturnValue({
      data: mockScoreData,
      isLoading: false,
      error: null
    })

    render(<PredictabilityCard ticker="AVANTI" />)

    await waitFor(() => {
      expect(screen.getByText('Information Availability')).toBeInTheDocument()
      expect(screen.getByText('Pattern Consistency')).toBeInTheDocument()
      expect(screen.getByText('Timing Accuracy')).toBeInTheDocument()
      expect(screen.getByText('Direction Confidence')).toBeInTheDocument()
    })
  })

  it('displays confidence level', async () => {
    ;(usePredictabilityScore as jest.Mock).mockReturnValue({
      data: mockScoreData,
      isLoading: false,
      error: null
    })

    render(<PredictabilityCard ticker="AVANTI" />)

    await waitFor(() => {
      expect(screen.getByText('85%')).toBeInTheDocument()
    })
  })

  it('displays error on API failure', () => {
    ;(usePredictabilityScore as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: 'Failed to fetch score'
    })

    render(<PredictabilityCard ticker="AVANTI" />)
    expect(screen.getByText(/Failed to load predictability score/i)).toBeInTheDocument()
  })

  it('shows correct color for low score', async () => {
    const lowScoreData = {
      ...mockScoreData,
      score: 35,
      recommendation: 'AVOID' as const
    }

    ;(usePredictabilityScore as jest.Mock).mockReturnValue({
      data: lowScoreData,
      isLoading: false,
      error: null
    })

    const { container } = render(<PredictabilityCard ticker="AVANTI" />)

    await waitFor(() => {
      const scoreText = screen.getByText('35')
      expect(scoreText).toHaveClass('text-red-400')
    })
  })

  it('shows correct color for medium score', async () => {
    const mediumScoreData = {
      ...mockScoreData,
      score: 62,
      recommendation: 'MAYBE' as const
    }

    ;(usePredictabilityScore as jest.Mock).mockReturnValue({
      data: mediumScoreData,
      isLoading: false,
      error: null
    })

    render(<PredictabilityCard ticker="AVANTI" />)

    await waitFor(() => {
      const scoreText = screen.getByText('62')
      expect(scoreText).toHaveClass('text-yellow-400')
    })
  })
})
```

## Definition of Done
- [x] Circular gauge visualization created with SVG
- [x] Color coding implemented (green/yellow/red)
- [x] Main predictability score displayed prominently
- [x] 4 sub-scores displayed with progress bars
- [x] Confidence level shown with percentage
- [x] Recommendation text displayed
- [x] API integration with predictionService complete
- [x] Loading state displays while fetching
- [x] Error state displays on API failure
- [x] Component responsive on all screen sizes
- [x] Component integrated into stock detail page
- [x] Unit tests written and passing
- [x] Accessibility requirements met

## Dependencies
- Story 4.2 (API Client Service Layer)
- Story 2.4 (Predictability Score Endpoint)
- Story 4.4 (Stock Detail Page)
- React Query configured
- TailwindCSS installed

## Notes
- Circular gauge uses SVG for performance
- Color scheme: Green (#10b981), Yellow (#eab308), Red (#ef4444)
- Score ranges: High (75-100), Medium (50-75), Low (0-50)
- Sub-scores also color-coded based on their values
- Caching set to 5 minutes (matches API caching)
- Smooth animations on gauge fill

## Acceptance Test Checklist
- [ ] Circular gauge displays correctly
- [ ] Overall score prominently displayed
- [ ] Score color correct for value (green > 75)
- [ ] Score color correct for value (yellow 50-75)
- [ ] Score color correct for value (red < 50)
- [ ] All 4 sub-scores displayed
- [ ] Confidence level shown with percentage
- [ ] Recommendation text displayed
- [ ] Loading state shows while fetching
- [ ] Error state shows on API failure
- [ ] Component responsive on mobile
- [ ] Component responsive on tablet
- [ ] Component responsive on desktop
- [ ] Sub-scores have correct progress bars
- [ ] Weighting explanation displayed at bottom
