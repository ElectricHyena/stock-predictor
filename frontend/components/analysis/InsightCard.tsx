'use client'

interface Insight {
  title: string
  description: string
  value: string | number
  icon: string
}

interface InsightCardProps {
  insight: Insight
}

export default function InsightCard({ insight }: InsightCardProps) {
  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-blue-500 transition-colors">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-slate-400 text-sm">{insight.description}</p>
          <h3 className="text-lg font-semibold text-white mt-1">{insight.title}</h3>
        </div>
        <span className="text-3xl">{insight.icon}</span>
      </div>
      <p className="text-2xl font-bold text-blue-400">
        {insight.value}
      </p>
    </div>
  )
}
