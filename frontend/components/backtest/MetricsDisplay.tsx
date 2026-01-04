'use client'

import BacktestResults from './BacktestResults'

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
  trades: any[]
  benchmark_return?: number
  monthly_returns?: Record<string, number>
  equity_curve?: Array<{ date: string; value: number; benchmark_value?: number }>
}

interface MetricsDisplayProps {
  result: BacktestResult
}

export default function MetricsDisplay({ result }: MetricsDisplayProps) {
  const metrics = [
    {
      label: 'Total Return',
      value: `${result.total_return.toFixed(2)}%`,
      highlight: result.total_return > 0 ? 'positive' : 'negative'
    },
    {
      label: 'Annual Return',
      value: `${result.annual_return.toFixed(2)}%`,
      highlight: result.annual_return > 0 ? 'positive' : 'negative'
    },
    {
      label: 'Sharpe Ratio',
      value: result.sharpe_ratio.toFixed(2),
      highlight: result.sharpe_ratio > 1 ? 'positive' : result.sharpe_ratio > 0 ? 'neutral' : 'negative'
    },
    {
      label: 'Sortino Ratio',
      value: result.sortino_ratio.toFixed(2),
      highlight: result.sortino_ratio > 1 ? 'positive' : 'neutral'
    },
    {
      label: 'Max Drawdown',
      value: `${result.max_drawdown.toFixed(2)}%`,
      highlight: 'negative'
    },
    {
      label: 'Calmar Ratio',
      value: result.calmar_ratio.toFixed(2),
      highlight: result.calmar_ratio > 0.5 ? 'positive' : 'neutral'
    },
    {
      label: 'Win Rate',
      value: `${result.win_rate.toFixed(1)}%`,
      highlight: result.win_rate > 50 ? 'positive' : 'negative'
    },
    {
      label: 'Profit Factor',
      value: result.profit_factor.toFixed(2),
      highlight: result.profit_factor > 1.5 ? 'positive' : result.profit_factor > 1 ? 'neutral' : 'negative'
    },
    {
      label: 'Total Trades',
      value: result.total_trades.toString(),
      highlight: 'neutral'
    },
    {
      label: 'Winning Trades',
      value: `${result.winning_trades}/${result.losing_trades}`,
      highlight: 'neutral'
    }
  ]

  const benchmarkReturn = result.benchmark_return || 0
  const outperformance = result.total_return - benchmarkReturn

  return (
    <div className="space-y-8">
      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {metrics.map((metric, idx) => (
          <div key={idx} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <p className="text-slate-400 text-xs uppercase tracking-wider">{metric.label}</p>
            <p className={`text-2xl font-bold mt-2 ${
              metric.highlight === 'positive' ? 'text-green-400' :
              metric.highlight === 'negative' ? 'text-red-400' :
              'text-white'
            }`}>
              {metric.value}
            </p>
          </div>
        ))}
      </div>

      {/* Benchmark Comparison */}
      {result.benchmark_return !== undefined && (
        <div className="bg-gradient-to-r from-slate-800 to-slate-700 rounded-lg p-6 border border-slate-600">
          <h3 className="text-lg font-semibold mb-4">Benchmark Comparison</h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-slate-400 text-sm">Strategy Return</p>
              <p className={`text-2xl font-bold mt-1 ${
                result.total_return > 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {result.total_return.toFixed(2)}%
              </p>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Benchmark (S&P 500)</p>
              <p className={`text-2xl font-bold mt-1 ${
                benchmarkReturn > 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {benchmarkReturn.toFixed(2)}%
              </p>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Outperformance</p>
              <p className={`text-2xl font-bold mt-1 ${
                outperformance > 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {outperformance > 0 ? '+' : ''}{outperformance.toFixed(2)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Equity Curve */}
      {result.equity_curve && result.equity_curve.length > 0 && (
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Equity Curve</h3>
          <BacktestResults equityCurve={result.equity_curve} />
        </div>
      )}

      {/* Strategy Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Trade Summary</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Total Trades</span>
              <span className="font-semibold">{result.total_trades}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Winning Trades</span>
              <span className="font-semibold text-green-400">{result.winning_trades}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Losing Trades</span>
              <span className="font-semibold text-red-400">{result.losing_trades}</span>
            </div>
            <div className="border-t border-slate-700 pt-3 mt-3 flex justify-between items-center">
              <span className="text-slate-400">Win Rate</span>
              <span className={`font-semibold text-lg ${
                result.win_rate > 50 ? 'text-green-400' : 'text-red-400'
              }`}>
                {result.win_rate.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Risk Metrics</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Max Drawdown</span>
              <span className="font-semibold text-red-400">{result.max_drawdown.toFixed(2)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Profit Factor</span>
              <span className={`font-semibold ${
                result.profit_factor > 1.5 ? 'text-green-400' :
                result.profit_factor > 1 ? 'text-yellow-400' :
                'text-red-400'
              }`}>
                {result.profit_factor.toFixed(2)}x
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Sharpe Ratio</span>
              <span className={`font-semibold ${
                result.sharpe_ratio > 1 ? 'text-green-400' :
                result.sharpe_ratio > 0 ? 'text-yellow-400' :
                'text-red-400'
              }`}>
                {result.sharpe_ratio.toFixed(2)}
              </span>
            </div>
            <div className="border-t border-slate-700 pt-3 mt-3 flex justify-between items-center">
              <span className="text-slate-400">Sortino Ratio</span>
              <span className="font-semibold">{result.sortino_ratio.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
