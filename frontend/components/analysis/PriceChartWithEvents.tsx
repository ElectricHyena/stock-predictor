'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Bar, ReferenceLine } from 'recharts'
import { useMemo, useState } from 'react'

interface HistoricalData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface PriceChartWithEventsProps {
  data: HistoricalData[]
  ticker: string
}

type IndicatorType = 'price' | 'rsi' | 'macd'

export default function PriceChartWithEvents({ data, ticker }: PriceChartWithEventsProps) {
  const [activeIndicator, setActiveIndicator] = useState<IndicatorType>('price')

  // Calculate all technical indicators
  const chartData = useMemo(() => {
    const closes = data.map(d => d.close)
    const rsiValues = calculateRSI(closes, 14)
    const macdData = calculateMACD(closes, 12, 26, 9)

    return data.map((d, idx) => {
      const sma20 = idx >= 19
        ? data.slice(idx - 19, idx + 1).reduce((sum, x) => sum + x.close, 0) / 20
        : d.close

      const ema12 = idx >= 11
        ? calculateEMA(data.slice(0, idx + 1).map(x => x.close), 12)
        : d.close

      return {
        ...d,
        date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        sma20: parseFloat(sma20.toFixed(2)),
        ema12: parseFloat(ema12.toFixed(2)),
        rsi: rsiValues[idx] || 50,
        macd: macdData.macd[idx] || 0,
        signal: macdData.signal[idx] || 0,
        histogram: macdData.histogram[idx] || 0,
      }
    })
  }, [data])

  const minPrice = Math.min(...data.map(d => d.low))
  const maxPrice = Math.max(...data.map(d => d.high))

  return (
    <div className="space-y-4">
      {/* Indicator Selector */}
      <div className="flex gap-2">
        {(['price', 'rsi', 'macd'] as IndicatorType[]).map((indicator) => (
          <button
            key={indicator}
            onClick={() => setActiveIndicator(indicator)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              activeIndicator === indicator
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
            }`}
          >
            {indicator.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Price Chart with Moving Averages */}
      {activeIndicator === 'price' && (
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
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
              domain={[minPrice * 0.99, maxPrice * 1.01]}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
              labelStyle={{ color: '#f1f5f9' }}
              formatter={(value: any) => typeof value === 'number' ? `$${value.toFixed(2)}` : value}
            />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />

            {/* Price Line */}
            <Line
              type="monotone"
              dataKey="close"
              stroke="#3b82f6"
              dot={false}
              strokeWidth={2}
              name="Price"
              isAnimationActive={false}
            />

            {/* SMA 20 */}
            <Line
              type="monotone"
              dataKey="sma20"
              stroke="#8b5cf6"
              dot={false}
              strokeWidth={1}
              strokeDasharray="5 5"
              name="SMA 20"
              isAnimationActive={false}
            />

            {/* EMA 12 */}
            <Line
              type="monotone"
              dataKey="ema12"
              stroke="#ec4899"
              dot={false}
              strokeWidth={1}
              strokeDasharray="5 5"
              name="EMA 12"
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      )}

      {/* RSI Chart */}
      {activeIndicator === 'rsi' && (
        <div>
          <p className="text-sm text-gray-400 mb-2">RSI (14) - Relative Strength Index</p>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
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
                domain={[0, 100]}
                ticks={[0, 30, 50, 70, 100]}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                labelStyle={{ color: '#f1f5f9' }}
                formatter={(value: any) => typeof value === 'number' ? value.toFixed(2) : value}
              />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />

              {/* Overbought/Oversold zones */}
              <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'Overbought (70)', fill: '#ef4444', fontSize: 11 }} />
              <ReferenceLine y={30} stroke="#22c55e" strokeDasharray="3 3" label={{ value: 'Oversold (30)', fill: '#22c55e', fontSize: 11 }} />
              <ReferenceLine y={50} stroke="#94a3b8" strokeDasharray="2 2" />

              {/* RSI Line */}
              <Line
                type="monotone"
                dataKey="rsi"
                stroke="#f59e0b"
                dot={false}
                strokeWidth={2}
                name="RSI (14)"
                isAnimationActive={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
          <div className="mt-2 flex gap-4 text-xs text-gray-400">
            <span><span className="text-red-400">Above 70:</span> Overbought (potential sell signal)</span>
            <span><span className="text-green-400">Below 30:</span> Oversold (potential buy signal)</span>
          </div>
        </div>
      )}

      {/* MACD Chart */}
      {activeIndicator === 'macd' && (
        <div>
          <p className="text-sm text-gray-400 mb-2">MACD (12, 26, 9) - Moving Average Convergence Divergence</p>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
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
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                labelStyle={{ color: '#f1f5f9' }}
                formatter={(value: any) => typeof value === 'number' ? value.toFixed(4) : value}
              />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />

              {/* Zero line */}
              <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="2 2" />

              {/* MACD Histogram */}
              <Bar
                dataKey="histogram"
                name="Histogram"
                isAnimationActive={false}
                fill="#6b7280"
              />

              {/* MACD Line */}
              <Line
                type="monotone"
                dataKey="macd"
                stroke="#3b82f6"
                dot={false}
                strokeWidth={2}
                name="MACD"
                isAnimationActive={false}
              />

              {/* Signal Line */}
              <Line
                type="monotone"
                dataKey="signal"
                stroke="#ef4444"
                dot={false}
                strokeWidth={2}
                name="Signal"
                isAnimationActive={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
          <div className="mt-2 flex gap-4 text-xs text-gray-400">
            <span><span className="text-blue-400">MACD crosses above Signal:</span> Bullish</span>
            <span><span className="text-red-400">MACD crosses below Signal:</span> Bearish</span>
          </div>
        </div>
      )}
    </div>
  )
}

function calculateEMA(prices: number[], period: number): number {
  if (prices.length === 0) return 0
  if (prices.length < period) {
    return prices.reduce((a, b) => a + b, 0) / prices.length
  }

  const multiplier = 2 / (period + 1)
  let ema = prices.slice(0, period).reduce((a, b) => a + b, 0) / period

  for (let i = period; i < prices.length; i++) {
    ema = prices[i] * multiplier + ema * (1 - multiplier)
  }

  return ema
}

/**
 * Calculate RSI (Relative Strength Index)
 */
function calculateRSI(prices: number[], period: number = 14): number[] {
  if (prices.length < period + 1) {
    return prices.map(() => 50)
  }

  const rsi: number[] = []
  let avgGain = 0
  let avgLoss = 0

  // Calculate initial average gain/loss
  for (let i = 1; i <= period; i++) {
    const change = prices[i] - prices[i - 1]
    if (change > 0) {
      avgGain += change
    } else {
      avgLoss += Math.abs(change)
    }
  }

  avgGain /= period
  avgLoss /= period

  // First RSI values (before period is complete)
  for (let i = 0; i < period; i++) {
    rsi.push(50)
  }

  // First real RSI
  if (avgLoss === 0) {
    rsi.push(100)
  } else {
    const rs = avgGain / avgLoss
    rsi.push(100 - 100 / (1 + rs))
  }

  // Calculate subsequent RSI values
  for (let i = period + 1; i < prices.length; i++) {
    const change = prices[i] - prices[i - 1]
    let currentGain = 0
    let currentLoss = 0

    if (change > 0) {
      currentGain = change
    } else {
      currentLoss = Math.abs(change)
    }

    avgGain = (avgGain * (period - 1) + currentGain) / period
    avgLoss = (avgLoss * (period - 1) + currentLoss) / period

    if (avgLoss === 0) {
      rsi.push(100)
    } else {
      const rs = avgGain / avgLoss
      rsi.push(100 - 100 / (1 + rs))
    }
  }

  return rsi
}

/**
 * Calculate MACD (Moving Average Convergence Divergence)
 */
function calculateMACD(
  prices: number[],
  fastPeriod: number = 12,
  slowPeriod: number = 26,
  signalPeriod: number = 9
): { macd: number[]; signal: number[]; histogram: number[] } {
  if (prices.length < slowPeriod) {
    return {
      macd: prices.map(() => 0),
      signal: prices.map(() => 0),
      histogram: prices.map(() => 0),
    }
  }

  // Calculate EMAs
  const multiplierFast = 2 / (fastPeriod + 1)
  const multiplierSlow = 2 / (slowPeriod + 1)
  const multiplierSignal = 2 / (signalPeriod + 1)

  const emaFast: number[] = []
  const emaSlow: number[] = []
  const macd: number[] = []
  const signal: number[] = []
  const histogram: number[] = []

  // Initialize EMAs
  let emaFastVal = prices.slice(0, fastPeriod).reduce((a, b) => a + b, 0) / fastPeriod
  let emaSlowVal = prices.slice(0, slowPeriod).reduce((a, b) => a + b, 0) / slowPeriod

  for (let i = 0; i < slowPeriod; i++) {
    emaFast.push(0)
    emaSlow.push(0)
    macd.push(0)
    signal.push(0)
    histogram.push(0)
  }

  // Calculate MACD line
  for (let i = slowPeriod; i < prices.length; i++) {
    emaFastVal = prices[i] * multiplierFast + emaFastVal * (1 - multiplierFast)
    emaSlowVal = prices[i] * multiplierSlow + emaSlowVal * (1 - multiplierSlow)
    emaFast.push(emaFastVal)
    emaSlow.push(emaSlowVal)
    macd.push(emaFastVal - emaSlowVal)
  }

  // Calculate Signal line
  const macdValues = macd.slice(slowPeriod)
  if (macdValues.length >= signalPeriod) {
    let signalVal = macdValues.slice(0, signalPeriod).reduce((a, b) => a + b, 0) / signalPeriod

    for (let i = 0; i < slowPeriod + signalPeriod - 1; i++) {
      signal.push(0)
      histogram.push(0)
    }

    for (let i = signalPeriod - 1; i < macdValues.length; i++) {
      signalVal = macdValues[i] * multiplierSignal + signalVal * (1 - multiplierSignal)
      signal.push(signalVal)
      histogram.push(macd[slowPeriod + i] - signalVal)
    }
  }

  return { macd, signal, histogram }
}
