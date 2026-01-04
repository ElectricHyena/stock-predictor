'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import BacktestResults from '@/components/backtest/BacktestResults'
import { Download, TrendingUp, Calendar } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'

interface BacktestResultsPageProps {
  params: {
    id: string
  }
}

interface BacktestResult {
  id: string
  strategy_name: string
  ticker: string
  start_date: string
  end_date: string
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  profit_factor: number
  total_return: number
  annual_return: number
  sharpe_ratio: number
  sortino_ratio: number
  max_drawdown: number
  calmar_ratio: number
  trades: Trade[]
  benchmark_return?: number
  monthly_returns?: Record<string, number>
  equity_curve?: EquityPoint[]
}

interface Trade {
  id: string
  entry_date: string
  exit_date: string
  entry_price: number
  exit_price: number
  quantity: number
  pnl: number
  pnl_percent: number
  duration_days: number
}

interface EquityPoint {
  date: string
  value: number
  benchmark_value?: number
}

export default function BacktestResultsPage({ params }: BacktestResultsPageProps) {
  const [comparisonIds, setComparisonIds] = useState<string[]>([])
  const [selectedTab, setSelectedTab] = useState<'summary' | 'trades' | 'performance'>('summary')

  const { data: result, isLoading } = useQuery({
    queryKey: ['backtest', params.id],
    queryFn: async () => {
      const response = await api.get(`/backtests/${params.id}`)
      return response.data as BacktestResult
    },
    staleTime: 10 * 60 * 1000
  })

  const { data: comparisonResults } = useQuery({
    queryKey: ['backtests', comparisonIds],
    queryFn: async () => {
      if (comparisonIds.length === 0) return []
      const responses = await Promise.all(
        comparisonIds.map(id => api.get(`/backtests/${id}`))
      )
      return responses.map(r => r.data)
    },
    enabled: comparisonIds.length > 0
  })

  const handleExportCSV = () => {
    if (!result) return
    const csv = generateCSV(result)
    downloadFile(csv, `backtest_${result.id}.csv`, 'text/csv')
  }

  const handleExportPDF = () => {
    alert('PDF export feature coming soon')
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-12 bg-slate-700 rounded w-1/3"></div>
          <div className="h-96 bg-slate-700 rounded"></div>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-red-400">Backtest results not found</p>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-4xl font-bold">{result.strategy_name}</h1>
            <p className="text-slate-400 mt-2">
              {result.ticker} | {result.start_date} to {result.end_date}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              <Download size={18} />
              Export CSV
            </button>
            <button
              onClick={handleExportPDF}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              <Download size={18} />
              PDF Report
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-slate-700">
          {(['summary', 'trades', 'performance'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setSelectedTab(tab)}
              className={`px-4 py-2 font-medium capitalize border-b-2 transition-colors ${
                selectedTab === tab
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Content based on selected tab */}
      {selectedTab === 'summary' && (
        <div className="space-y-6">
          <MetricsDisplay result={result} />

          {/* Comparison Section */}
          {comparisonResults && comparisonResults.length > 0 && (
            <div className="bg-slate-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Strategy Comparison</h2>
              <ComparisonTable results={[result, ...comparisonResults]} />
            </div>
          )}
        </div>
      )}

      {selectedTab === 'trades' && (
        <div className="bg-slate-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Trade List</h2>
          <TradeTable trades={result.trades} />
        </div>
      )}

      {selectedTab === 'performance' && (
        <div className="space-y-6">
          {/* Equity Curve Chart */}
          <div className="bg-slate-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Equity Curve</h2>
            <EquityCurveChart
              equityCurve={result.equity_curve || generateEquityCurve(result.trades)}
              benchmarkReturn={result.benchmark_return}
            />
          </div>

          {/* Monthly Returns */}
          <div className="bg-slate-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Monthly Returns</h2>
            <MonthlyReturnsChart returns={result.monthly_returns || {}} />
          </div>

          {/* Additional Risk Metrics */}
          <div className="bg-slate-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Risk Metrics</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-700/50 rounded-lg p-4">
                <p className="text-slate-400 text-sm">Sortino Ratio</p>
                <p className="text-2xl font-bold text-white mt-1">{result.sortino_ratio?.toFixed(2) || 'N/A'}</p>
                <p className="text-xs text-slate-500 mt-1">Downside risk-adjusted return</p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4">
                <p className="text-slate-400 text-sm">Calmar Ratio</p>
                <p className="text-2xl font-bold text-white mt-1">{result.calmar_ratio?.toFixed(2) || 'N/A'}</p>
                <p className="text-xs text-slate-500 mt-1">Annual return / Max drawdown</p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4">
                <p className="text-slate-400 text-sm">Benchmark Return</p>
                <p className={`text-2xl font-bold mt-1 ${(result.benchmark_return || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {result.benchmark_return ? `${result.benchmark_return.toFixed(2)}%` : 'N/A'}
                </p>
                <p className="text-xs text-slate-500 mt-1">Market performance comparison</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function MetricsDisplay({ result }: { result: BacktestResult }) {
  const metrics = [
    { label: 'Total Return', value: `${result.total_return.toFixed(2)}%`, highlight: result.total_return > 0 },
    { label: 'Annual Return', value: `${result.annual_return.toFixed(2)}%`, highlight: result.annual_return > 0 },
    { label: 'Sharpe Ratio', value: result.sharpe_ratio.toFixed(2) },
    { label: 'Max Drawdown', value: `${result.max_drawdown.toFixed(2)}%`, highlight: false },
    { label: 'Win Rate', value: `${result.win_rate.toFixed(1)}%` },
    { label: 'Profit Factor', value: result.profit_factor.toFixed(2) },
    { label: 'Total Trades', value: result.total_trades.toString() },
    { label: 'Winning Trades', value: `${result.winning_trades} / ${result.losing_trades}` }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric, idx) => (
        <div key={idx} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <p className="text-slate-400 text-sm">{metric.label}</p>
          <p className={`text-2xl font-bold mt-2 ${
            metric.highlight === true ? 'text-green-400' :
            metric.highlight === false ? 'text-red-400' :
            'text-white'
          }`}>
            {metric.value}
          </p>
        </div>
      ))}
    </div>
  )
}

function TradeTable({ trades }: { trades: Trade[] }) {
  const [sortBy, setSortBy] = useState<'date' | 'pnl' | 'duration'>('date')

  const sortedTrades = [...trades].sort((a, b) => {
    switch (sortBy) {
      case 'pnl':
        return b.pnl - a.pnl
      case 'duration':
        return b.duration_days - a.duration_days
      default:
        return new Date(b.entry_date).getTime() - new Date(a.entry_date).getTime()
    }
  })

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {(['date', 'pnl', 'duration'] as const).map(key => (
          <button
            key={key}
            onClick={() => setSortBy(key)}
            className={`px-3 py-1 rounded text-sm capitalize ${
              sortBy === key
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Sort by {key}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-700">
            <tr>
              <th className="text-left py-2 px-2">Entry Date</th>
              <th className="text-right py-2 px-2">Entry Price</th>
              <th className="text-right py-2 px-2">Exit Price</th>
              <th className="text-right py-2 px-2">P&L</th>
              <th className="text-right py-2 px-2">P&L %</th>
              <th className="text-right py-2 px-2">Duration (days)</th>
            </tr>
          </thead>
          <tbody>
            {sortedTrades.map(trade => (
              <tr key={trade.id} className="border-b border-slate-700 hover:bg-slate-700/50">
                <td className="py-2 px-2">{new Date(trade.entry_date).toLocaleDateString()}</td>
                <td className="text-right py-2 px-2">${trade.entry_price.toFixed(2)}</td>
                <td className="text-right py-2 px-2">${trade.exit_price.toFixed(2)}</td>
                <td className={`text-right py-2 px-2 font-semibold ${
                  trade.pnl > 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  ${trade.pnl.toFixed(2)}
                </td>
                <td className={`text-right py-2 px-2 ${
                  trade.pnl_percent > 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {trade.pnl_percent > 0 ? '+' : ''}{trade.pnl_percent.toFixed(2)}%
                </td>
                <td className="text-right py-2 px-2">{trade.duration_days}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-slate-400 text-sm">
        Showing {sortedTrades.length} trades
      </p>
    </div>
  )
}

function ComparisonTable({ results }: { results: BacktestResult[] }) {
  const metrics = ['total_return', 'annual_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'profit_factor']

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-slate-700">
          <tr>
            <th className="text-left py-2 px-2">Strategy</th>
            {metrics.map(metric => (
              <th key={metric} className="text-right py-2 px-2 capitalize">
                {metric.replace('_', ' ')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {results.map(result => (
            <tr key={result.id} className="border-b border-slate-700 hover:bg-slate-700/50">
              <td className="py-2 px-2 font-semibold">{result.strategy_name}</td>
              <td className="text-right py-2 px-2 text-green-400">{result.total_return.toFixed(2)}%</td>
              <td className="text-right py-2 px-2">{result.annual_return.toFixed(2)}%</td>
              <td className="text-right py-2 px-2">{result.sharpe_ratio.toFixed(2)}</td>
              <td className="text-right py-2 px-2 text-red-400">{result.max_drawdown.toFixed(2)}%</td>
              <td className="text-right py-2 px-2">{result.win_rate.toFixed(1)}%</td>
              <td className="text-right py-2 px-2">{result.profit_factor.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function MonthlyReturnsChart({ returns }: { returns: Record<string, number> }) {
  if (Object.keys(returns).length === 0) {
    return <p className="text-slate-400">No monthly returns data available</p>
  }

  const months = Object.entries(returns)
    .map(([month, value]) => ({
      month: new Date(month).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
      value
    }))
    .slice(-12)

  return (
    <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
      {months.map((m, idx) => (
        <div key={idx} className="text-center p-2 bg-slate-700 rounded">
          <p className="text-xs text-slate-400">{m.month}</p>
          <p className={`font-semibold ${m.value > 0 ? 'text-green-400' : 'text-red-400'}`}>
            {m.value > 0 ? '+' : ''}{m.value.toFixed(1)}%
          </p>
        </div>
      ))}
    </div>
  )
}

function generateCSV(result: BacktestResult): string {
  const lines = [
    `Strategy,${result.strategy_name}`,
    `Ticker,${result.ticker}`,
    `Period,"${result.start_date} to ${result.end_date}"`,
    '',
    'Metrics',
    `Total Return,${result.total_return}%`,
    `Annual Return,${result.annual_return}%`,
    `Sharpe Ratio,${result.sharpe_ratio}`,
    `Max Drawdown,${result.max_drawdown}%`,
    `Win Rate,${result.win_rate}%`,
    `Profit Factor,${result.profit_factor}`,
    `Total Trades,${result.total_trades}`,
    '',
    'Trades',
    'Entry Date,Entry Price,Exit Date,Exit Price,P&L,P&L %,Duration Days',
    ...result.trades.map(t =>
      `${t.entry_date},${t.entry_price},${t.exit_date},${t.exit_price},${t.pnl},${t.pnl_percent},${t.duration_days}`
    )
  ]

  return lines.join('\n')
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

/**
 * Equity Curve Chart Component
 */
function EquityCurveChart({ equityCurve, benchmarkReturn }: { equityCurve: EquityPoint[]; benchmarkReturn?: number }) {
  if (!equityCurve || equityCurve.length === 0) {
    return <p className="text-slate-400">No equity curve data available</p>
  }

  const chartData = equityCurve.map((point, idx) => ({
    date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    portfolio: point.value,
    benchmark: point.benchmark_value ?? (benchmarkReturn ? 100 * (1 + (benchmarkReturn / 100) * (idx / equityCurve.length)) : undefined)
  }))

  const minValue = Math.min(...chartData.map(d => Math.min(d.portfolio, d.benchmark || Infinity)))
  const maxValue = Math.max(...chartData.map(d => Math.max(d.portfolio, d.benchmark || 0)))
  const padding = (maxValue - minValue) * 0.05

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis
          dataKey="date"
          stroke="#94a3b8"
          style={{ fontSize: '12px' }}
          tick={{ fill: '#94a3b8' }}
        />
        <YAxis
          stroke="#94a3b8"
          style={{ fontSize: '12px' }}
          tick={{ fill: '#94a3b8' }}
          domain={[minValue - padding, maxValue + padding]}
          tickFormatter={(value) => `$${value.toFixed(0)}`}
        />
        <Tooltip
          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
          labelStyle={{ color: '#f1f5f9' }}
          formatter={(value: any) => typeof value === 'number' ? `$${value.toFixed(2)}` : value}
        />
        <Legend wrapperStyle={{ paddingTop: '20px' }} />

        {/* Starting Value Reference */}
        <ReferenceLine y={100} stroke="#94a3b8" strokeDasharray="3 3" label={{ value: 'Initial ($100)', fill: '#94a3b8', fontSize: 11 }} />

        {/* Portfolio Equity Curve */}
        <Line
          type="monotone"
          dataKey="portfolio"
          stroke="#3b82f6"
          dot={false}
          strokeWidth={2}
          name="Portfolio"
          isAnimationActive={false}
        />

        {/* Benchmark Line (if available) */}
        {chartData[0]?.benchmark !== undefined && (
          <Line
            type="monotone"
            dataKey="benchmark"
            stroke="#6b7280"
            dot={false}
            strokeWidth={1}
            strokeDasharray="5 5"
            name="Benchmark"
            isAnimationActive={false}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  )
}

/**
 * Generate equity curve from trades (for when backend doesn't provide it)
 */
function generateEquityCurve(trades: Trade[]): EquityPoint[] {
  if (!trades || trades.length === 0) {
    return []
  }

  // Sort trades by entry date
  const sortedTrades = [...trades].sort((a, b) =>
    new Date(a.entry_date).getTime() - new Date(b.entry_date).getTime()
  )

  const equityCurve: EquityPoint[] = []
  let portfolioValue = 100 // Start with $100

  // Add starting point
  equityCurve.push({
    date: sortedTrades[0].entry_date,
    value: portfolioValue
  })

  // Build equity curve from trade results
  for (const trade of sortedTrades) {
    // Apply trade P&L percentage to portfolio
    portfolioValue = portfolioValue * (1 + trade.pnl_percent / 100)

    equityCurve.push({
      date: trade.exit_date,
      value: parseFloat(portfolioValue.toFixed(2))
    })
  }

  return equityCurve
}
