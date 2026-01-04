'use client'

import { TrendingUp, Award, Target } from 'lucide-react'

interface Stock {
  id: number
  symbol: string
  name: string
  current_price: number
  change_percent: number
  predictability_score: number
}

interface PortfolioInsightsProps {
  stocks: Stock[]
}

export default function PortfolioInsights({ stocks }: PortfolioInsightsProps) {
  if (stocks.length === 0) return null

  // Calculate portfolio metrics
  const topByScore = [...stocks]
    .sort((a, b) => b.predictability_score - a.predictability_score)
    .slice(0, 3)

  const topByGain = [...stocks]
    .sort((a, b) => b.change_percent - a.change_percent)
    .slice(0, 3)

  const avgScore = stocks.reduce((sum, s) => sum + s.predictability_score, 0) / stocks.length
  const avgChange = stocks.reduce((sum, s) => sum + s.change_percent, 0) / stocks.length

  const gainers = stocks.filter(s => s.change_percent > 0).length
  const losers = stocks.filter(s => s.change_percent < 0).length

  return (
    <div className="space-y-4">
      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-lg p-4 border border-slate-600">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Total Stocks</p>
              <p className="text-3xl font-bold text-white mt-1">{stocks.length}</p>
            </div>
            <Target size={32} className="text-blue-400 opacity-50" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-lg p-4 border border-slate-600">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Avg Predictability</p>
              <p className={`text-3xl font-bold mt-1 ${
                avgScore > 0.6 ? 'text-green-400' :
                avgScore > 0.4 ? 'text-yellow-400' :
                'text-red-400'
              }`}>
                {(avgScore * 100).toFixed(0)}%
              </p>
            </div>
            <Award size={32} className="opacity-50" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-lg p-4 border border-slate-600">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Gainers</p>
              <div className="flex gap-2 mt-1">
                <p className="text-2xl font-bold text-green-400">{gainers}</p>
                <p className="text-slate-400">/</p>
                <p className="text-2xl font-bold text-red-400">{losers}</p>
              </div>
            </div>
            <TrendingUp size={32} className="text-green-400 opacity-50" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-lg p-4 border border-slate-600">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Avg Change</p>
              <p className={`text-3xl font-bold mt-1 ${
                avgChange > 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {avgChange > 0 ? '+' : ''}{avgChange.toFixed(2)}%
              </p>
            </div>
            <TrendingUp size={32} className={avgChange > 0 ? 'text-green-400 opacity-50' : 'text-red-400 opacity-50'} />
          </div>
        </div>
      </div>

      {/* Top Stocks by Predictability */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          🎯 Top 3 by Predictability Score
        </h3>
        <div className="space-y-3">
          {topByScore.map((stock, idx) => (
            <div key={stock.id} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-8 h-8 bg-blue-600 rounded-full font-semibold text-white">
                  {idx + 1}
                </div>
                <div>
                  <p className="font-semibold text-white">{stock.symbol}</p>
                  <p className="text-xs text-slate-400">{stock.name}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-bold text-green-400">
                  {(stock.predictability_score * 100).toFixed(0)}%
                </p>
                <p className="text-xs text-slate-400">Score</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Movers */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          📈 Top 3 Gainers
        </h3>
        <div className="space-y-3">
          {topByGain.map((stock, idx) => (
            <div key={stock.id} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-8 h-8 bg-green-600 rounded-full font-semibold text-white">
                  {idx + 1}
                </div>
                <div>
                  <p className="font-semibold text-white">{stock.symbol}</p>
                  <p className="text-xs text-slate-400">${stock.current_price.toFixed(2)}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-bold text-green-400">
                  +{stock.change_percent.toFixed(2)}%
                </p>
                <p className="text-xs text-slate-400">Change</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
