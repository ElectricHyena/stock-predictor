'use client'

interface HistoricalData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface PatternTimelineProps {
  data: HistoricalData[]
}

export default function PatternTimeline({ data }: PatternTimelineProps) {
  if (!data || data.length === 0) {
    return <p className="text-slate-400">No data available</p>
  }

  // Identify key patterns and events
  const events = identifyPatterns(data)

  const displayEvents = events.slice(-10) // Show last 10 events

  return (
    <div className="space-y-4">
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-1 bg-slate-700"></div>

        {/* Timeline items */}
        <div className="space-y-6 ml-16">
          {displayEvents.map((event, idx) => (
            <div key={idx} className="relative">
              {/* Dot */}
              <div className={`absolute -left-14 top-1 w-8 h-8 rounded-full border-4 flex items-center justify-center ${
                event.type === 'peak' ? 'border-green-500 bg-slate-900' :
                event.type === 'valley' ? 'border-red-500 bg-slate-900' :
                'border-blue-500 bg-slate-900'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  event.type === 'peak' ? 'bg-green-500' :
                  event.type === 'valley' ? 'bg-red-500' :
                  'bg-blue-500'
                }`}></div>
              </div>

              {/* Content */}
              <div className="bg-slate-700 rounded-lg p-3">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-white">{event.label}</p>
                    <p className="text-sm text-slate-300 mt-1">{event.description}</p>
                  </div>
                  <span className="text-xs text-slate-400 whitespace-nowrap ml-2">
                    {new Date(event.date).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {events.length === 0 && (
        <p className="text-slate-400 text-center py-8">No significant patterns detected in this period</p>
      )}
    </div>
  )
}

interface Pattern {
  date: string
  type: 'peak' | 'valley' | 'trend'
  label: string
  description: string
  price: number
}

function identifyPatterns(data: HistoricalData[]): Pattern[] {
  const patterns: Pattern[] = []

  for (let i = 1; i < data.length - 1; i++) {
    const prev = data[i - 1]
    const current = data[i]
    const next = data[i + 1]

    // Peak detection
    if (current.high > prev.high && current.high > next.high) {
      patterns.push({
        date: current.date,
        type: 'peak',
        label: 'Local Peak',
        description: `Price reached $${current.high.toFixed(2)}`,
        price: current.high
      })
    }

    // Valley detection
    if (current.low < prev.low && current.low < next.low) {
      patterns.push({
        date: current.date,
        type: 'valley',
        label: 'Local Valley',
        description: `Price dipped to $${current.low.toFixed(2)}`,
        price: current.low
      })
    }

    // Volume spike
    if (current.volume > prev.volume * 1.5) {
      patterns.push({
        date: current.date,
        type: 'trend',
        label: 'High Volume',
        description: `${(current.volume / 1e6).toFixed(1)}M shares traded`,
        price: current.close
      })
    }
  }

  return patterns.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
}
