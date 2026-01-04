'use client'

import { useParams } from 'next/navigation'
import Link from 'next/link'
import { useStockDetail } from '@/lib/services/stockService'
import { Loader2, AlertCircle, ArrowLeft } from 'lucide-react'
import PriceHeader from '@/components/detail/PriceHeader'
import PredictabilityCard from '@/components/detail/PredictabilityCard'
import PredictionBanner from '@/components/detail/PredictionBanner'

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
          {isPositive ? '+' : ''}
          {change}%
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
    isWatchlist
      ? 'bg-yellow-600 hover:bg-yellow-700 text-white'
      : isAlert
        ? 'bg-red-600 hover:bg-red-700 text-white'
        : 'bg-blue-600 hover:bg-blue-700 text-white'
  }`

  if (isWatchlist || isAlert) {
    return <button className={className}>{label}</button>
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

export default function StockDetailPage() {
  const params = useParams()
  const ticker = params.ticker as string

  const { data: stock, isLoading, error } = useStockDetail(ticker)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      {/* Header Navigation */}
      <div className="sticky top-16 z-10 bg-slate-900/80 backdrop-blur border-b border-slate-700 px-8 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-4">
          <Link href="/search" className="text-gray-400 hover:text-white transition">
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
                <p className="text-red-300 text-sm mt-1">{error.message}</p>
                <Link href="/search" className="text-blue-400 hover:text-blue-300 text-sm mt-3 inline-block">
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
                  change={
                    stock.fifty_two_week_high
                      ? ((stock.current_price - stock.fifty_two_week_high) / stock.fifty_two_week_high * 100).toFixed(2)
                      : '0'
                  }
                />
                <MetricCard
                  label="52-Week Low"
                  value={`₹${stock.fifty_two_week_low?.toFixed(2) || 'N/A'}`}
                  change={
                    stock.fifty_two_week_low
                      ? ((stock.current_price - stock.fifty_two_week_low) / stock.fifty_two_week_low * 100).toFixed(2)
                      : '0'
                  }
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
                    <ActionButton href="#" label="Add to Watchlist" isWatchlist={true} />
                    <ActionButton href="#" label="Set Alert" isAlert={true} />
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
