'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface EquityPoint {
  date: string
  value: number
  benchmark_value?: number
}

interface BacktestResultsProps {
  equityCurve: EquityPoint[]
}

export default function BacktestResults({ equityCurve }: BacktestResultsProps) {
  if (!equityCurve || equityCurve.length === 0) {
    return <p className="text-slate-400">No equity curve data available</p>
  }

  const chartData = equityCurve.map(point => ({
    date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    value: parseFloat(point.value.toFixed(2)),
    benchmark_value: point.benchmark_value ? parseFloat(point.benchmark_value.toFixed(2)) : undefined
  }))

  const minValue = Math.min(...chartData.map(d => Math.min(d.value, d.benchmark_value || d.value)))
  const maxValue = Math.max(...chartData.map(d => Math.max(d.value, d.benchmark_value || d.value)))

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
          domain={[minValue * 0.98, maxValue * 1.02]}
        />
        <Tooltip
          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
          labelStyle={{ color: '#f1f5f9' }}
          formatter={(value: any) => typeof value === 'number' ? `$${value.toFixed(2)}` : value}
        />
        <Legend wrapperStyle={{ paddingTop: '20px' }} />

        <Line
          type="monotone"
          dataKey="value"
          stroke="#3b82f6"
          dot={false}
          strokeWidth={2}
          name="Strategy"
          isAnimationActive={false}
        />

        {chartData.some(d => d.benchmark_value) && (
          <Line
            type="monotone"
            dataKey="benchmark_value"
            stroke="#8b5cf6"
            dot={false}
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Benchmark (S&P 500)"
            isAnimationActive={false}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  )
}
