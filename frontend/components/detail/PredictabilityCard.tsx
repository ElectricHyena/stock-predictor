'use client'

import React from 'react'
import { usePredictabilityScore } from '@/lib/services/predictionService'
import { Loader2, AlertCircle } from 'lucide-react'

interface PredictabilityCardProps {
  ticker: string
}

function getScoreColor(score: number): string {
  if (score > 75) return 'text-green-400'
  if (score > 50) return 'text-yellow-400'
  return 'text-red-400'
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
              <p className="text-red-400 text-sm font-semibold">Failed to load score</p>
              <p className="text-red-300 text-xs mt-1">{error.message}</p>
            </div>
          </div>
        )}

        {!isLoading && !error && data && (
          <>
            <div className="flex flex-col items-center mb-8">
              <CircularGauge score={data.score} />
              <div className="text-center mt-4">
                <p className={`text-2xl font-bold ${getScoreColor(data.score)}`}>
                  {data.score}
                </p>
                <p className="text-gray-400 text-sm mt-1">Overall Score</p>
              </div>
            </div>

            <div className="bg-slate-700/50 rounded-lg p-4 mb-6">
              <p className="text-gray-400 text-xs uppercase tracking-wide mb-2">Recommendation</p>
              <p className={`text-lg font-semibold ${getRecommendationColor(data.recommendation)}`}>
                {getRecommendationText(data.recommendation)}
              </p>
            </div>

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

            <div className="border-t border-slate-700 pt-6">
              <p className="text-gray-400 text-sm font-semibold mb-4">Component Scores</p>
              <div className="space-y-4">
                <SubScoreBar label="Information Availability" score={data.sub_scores.information} />
                <SubScoreBar label="Pattern Consistency" score={data.sub_scores.pattern} />
                <SubScoreBar label="Timing Accuracy" score={data.sub_scores.timing} />
                <SubScoreBar label="Direction Confidence" score={data.sub_scores.direction} />
              </div>
            </div>

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
      <circle cx="80" cy="80" r={radius} fill="none" stroke="rgba(71, 85, 105, 0.3)" strokeWidth="8" />
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
          transition: 'stroke-dashoffset 0.5s ease',
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
            score > 75 ? 'bg-green-500' : score > 50 ? 'bg-yellow-500' : 'bg-red-500'
          }`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  )
}
