'use client'

import React from 'react'
import { usePrediction } from '@/lib/services/predictionService'
import { TrendingUp, TrendingDown, Loader2, AlertCircle, Clock } from 'lucide-react'

interface PredictionBannerProps {
  ticker: string
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
          <p className="text-red-300 text-sm mt-1">{error.message}</p>
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
              <p className={`text-3xl font-bold ${textColor}`}>{isUp ? '↑' : '↓'}</p>
              <p className={`text-3xl font-bold ${textColor}`}>
                {data.magnitude_min > 0 ? '+' : ''}
                {data.magnitude_min.toFixed(1)}% to {data.magnitude_max > 0 ? '+' : ''}
                {data.magnitude_max.toFixed(1)}%
              </p>
            </div>
            <p className="text-white font-semibold text-lg">
              {isUp ? 'Expected Upward Movement' : 'Expected Downward Movement'}
            </p>
          </div>
        </div>

        <div className="lg:text-right space-y-4">
          <div className="bg-slate-800/30 rounded-lg p-4">
            <p className="text-gray-400 text-xs uppercase tracking-wide mb-2">Timing</p>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-400" />
              <p className="text-white font-semibold">{getTimingLabel(data.timing)}</p>
            </div>
          </div>

          <div className="bg-slate-800/30 rounded-lg p-4">
            <p className="text-gray-400 text-xs uppercase tracking-wide mb-2">Historical Win Rate</p>
            <p className={`text-2xl font-bold ${textColor}`}>{data.win_rate}%</p>
          </div>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-slate-700/50">
        <div className="flex items-center justify-between mb-2">
          <p className="text-gray-400 text-sm">Prediction Confidence</p>
          <p className="text-white font-semibold">{data.confidence}%</p>
        </div>
        <div className="w-full bg-slate-700/30 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              isUp ? 'bg-gradient-to-r from-green-500 to-emerald-500' : 'bg-gradient-to-r from-red-500 to-rose-500'
            }`}
            style={{ width: `${data.confidence}%` }}
          />
        </div>
      </div>

      {data.reasoning && (
        <div className="mt-4 pt-4 border-t border-slate-700/50">
          <p className="text-gray-400 text-xs uppercase tracking-wide mb-2">Reasoning</p>
          <p className="text-gray-300 text-sm">{data.reasoning}</p>
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-slate-700/50">
        <p className="text-gray-500 text-xs">
          Past performance does not guarantee future results. This prediction is based on historical patterns and
          should not be considered financial advice.
        </p>
      </div>
    </div>
  )
}
