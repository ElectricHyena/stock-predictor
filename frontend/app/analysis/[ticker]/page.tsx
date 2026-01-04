'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import PriceChartWithEvents from '@/components/analysis/PriceChartWithEvents'
import InsightCard from '@/components/analysis/InsightCard'
import PatternTimeline from '@/components/analysis/PatternTimeline'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Bar } from 'recharts'
import { Download, TrendingUp } from 'lucide-react'

interface AnalysisPageProps {
  params: {
    ticker: string
  }
}

interface StockData {
  ticker: string
  name: string
  current_price: number
  previous_close: number
  market_cap?: number
  fifty_two_week_high?: number
  fifty_two_week_low?: number
}

interface HistoricalData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface Insight {
  title: string
  description: string
  value: string | number
  icon: string
}

const PERIOD_OPTIONS = [
  { label: '1M', value: '1m' },
  { label: '3M', value: '3m' },
  { label: '6M', value: '6m' },
  { label: '1Y', value: '1y' },
  { label: 'All', value: 'all' }
]

export default function AnalysisPage({ params }: AnalysisPageProps) {
  const [selectedPeriod, setSelectedPeriod] = useState('1y')
  const [chartData, setChartData] = useState<HistoricalData[]>([])
  const [isExporting, setIsExporting] = useState(false)

  const ticker = params.ticker.toUpperCase()

  // Fetch stock details
  const { data: stockData, isLoading: stockLoading } = useQuery({
    queryKey: ['stock', ticker],
    queryFn: async () => {
      const response = await api.get(`/stocks/${ticker}`)
      return response.data as StockData
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Fetch historical data
  const { data: historicalData, isLoading: historyLoading } = useQuery({
    queryKey: ['historical', ticker, selectedPeriod],
    queryFn: async () => {
      const response = await api.get(`/stocks/${ticker}/historical`, {
        params: { period: selectedPeriod }
      })
      return response.data as HistoricalData[]
    },
    enabled: !!ticker,
    staleTime: 10 * 60 * 1000,
  })

  // Process data for insights
  const insights: Insight[] = historicalData ? [
    {
      title: 'Highest Volatility Period',
      description: 'Period with maximum price swings',
      value: `${((Math.max(...historicalData.map(d => d.high - d.low)) / (historicalData[0]?.close || 1)) * 100).toFixed(2)}%`,
      icon: '📈'
    },
    {
      title: 'Average Volume',
      description: 'Trading volume during period',
      value: `${(historicalData.reduce((sum, d) => sum + d.volume, 0) / historicalData.length / 1e6).toFixed(2)}M`,
      icon: '📊'
    },
    {
      title: 'Period Return',
      description: 'Overall return for selected period',
      value: `${(((historicalData[historicalData.length - 1]?.close || 0) - (historicalData[0]?.open || 0)) / (historicalData[0]?.open || 1) * 100).toFixed(2)}%`,
      icon: '💹'
    }
  ] : []

  const handleExportCSV = async () => {
    if (!historicalData || !stockData) return

    setIsExporting(true)
    try {
      const csv = generateCSV(historicalData, stockData)
      downloadFile(csv, `${ticker}_analysis_${selectedPeriod}.csv`, 'text/csv')
    } finally {
      setIsExporting(false)
    }
  }

  const handleExportPDF = async () => {
    setIsExporting(true)
    try {
      // In production, use jsPDF or similar library
      alert('PDF export feature coming soon')
    } finally {
      setIsExporting(false)
    }
  }

  if (stockLoading || historyLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-12 bg-slate-700 rounded-lg w-1/3"></div>
          <div className="h-96 bg-slate-700 rounded-lg"></div>
        </div>
      </div>
    )
  }

  if (!stockData) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-red-400">Stock not found</p>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white">{stockData.name}</h1>
            <p className="text-2xl text-blue-400 mt-2">${stockData.current_price.toFixed(2)}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleExportCSV}
              disabled={isExporting}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
            >
              <Download size={18} />
              CSV
            </button>
            <button
              onClick={handleExportPDF}
              disabled={isExporting}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
            >
              <Download size={18} />
              PDF
            </button>
          </div>
        </div>

        {/* Period Selector */}
        <div className="flex gap-2 flex-wrap">
          {PERIOD_OPTIONS.map(period => (
            <button
              key={period.value}
              onClick={() => setSelectedPeriod(period.value)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedPeriod === period.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {period.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Chart */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <TrendingUp size={24} />
          Price Chart
        </h2>
        <PriceChartWithEvents data={historicalData || []} ticker={ticker} />
      </div>

      {/* Insights Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {insights.map((insight, index) => (
          <InsightCard key={index} insight={insight} />
        ))}
      </div>

      {/* Pattern Timeline */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Pattern Timeline</h2>
        <PatternTimeline data={historicalData || []} />
      </div>

      {/* Additional Metrics */}
      {stockData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            label="52W High"
            value={stockData.fifty_two_week_high ? `$${stockData.fifty_two_week_high.toFixed(2)}` : 'N/A'}
          />
          <MetricCard
            label="52W Low"
            value={stockData.fifty_two_week_low ? `$${stockData.fifty_two_week_low.toFixed(2)}` : 'N/A'}
          />
          <MetricCard
            label="Market Cap"
            value={stockData.market_cap ? formatMarketCap(stockData.market_cap) : 'N/A'}
          />
          <MetricCard
            label="Change"
            value={stockData.previous_close ?
              `${(((stockData.current_price - stockData.previous_close) / stockData.previous_close) * 100).toFixed(2)}%`
              : 'N/A'}
            isPositive={stockData.previous_close ? stockData.current_price >= stockData.previous_close : undefined}
          />
        </div>
      )}
    </div>
  )
}

interface MetricCardProps {
  label: string
  value: string
  isPositive?: boolean
}

function MetricCard({ label, value, isPositive }: MetricCardProps) {
  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <p className="text-slate-400 text-sm">{label}</p>
      <p className={`text-xl font-semibold mt-1 ${
        isPositive === true ? 'text-green-400' :
        isPositive === false ? 'text-red-400' :
        'text-white'
      }`}>
        {value}
      </p>
    </div>
  )
}

function generateCSV(data: HistoricalData[], stock: StockData): string {
  const headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
  const rows = data.map(d => [d.date, d.open, d.high, d.low, d.close, d.volume])

  const csv = [
    `${stock.ticker} - Historical Analysis`,
    `Exported: ${new Date().toISOString()}`,
    '',
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n')

  return csv
}

function downloadFile(content: string, filename: string, type: string) {
  const element = document.createElement('a')
  element.setAttribute('href', `data:${type};charset=utf-8,${encodeURIComponent(content)}`)
  element.setAttribute('download', filename)
  element.style.display = 'none'
  document.body.appendChild(element)
  element.click()
  document.body.removeChild(element)
}

function formatMarketCap(cap: number): string {
  if (cap >= 1e12) return `$${(cap / 1e12).toFixed(2)}T`
  if (cap >= 1e9) return `$${(cap / 1e9).toFixed(2)}B`
  if (cap >= 1e6) return `$${(cap / 1e6).toFixed(2)}M`
  return `$${cap.toFixed(0)}`
}
