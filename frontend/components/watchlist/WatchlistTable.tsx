'use client'

import { TrendingUp, TrendingDown, Trash2, Eye } from 'lucide-react'
import Link from 'next/link'

interface Stock {
  id: number
  symbol: string
  name: string
  current_price: number
  change_percent: number
  predictability_score: number
}

interface WatchlistTableProps {
  stocks: Stock[]
  onRemove: (stockId: number) => void
}

export default function WatchlistTable({ stocks, onRemove }: WatchlistTableProps) {
  const getPredictabilityColor = (score: number): string => {
    if (score >= 0.7) return 'text-green-400'
    if (score >= 0.5) return 'text-yellow-400'
    return 'text-red-400'
  }

  return (
    <div className="bg-slate-800 rounded-lg overflow-hidden border border-slate-700">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-700 border-b border-slate-600">
            <tr>
              <th className="text-left px-6 py-3 font-semibold text-slate-200">Symbol</th>
              <th className="text-left px-6 py-3 font-semibold text-slate-200">Name</th>
              <th className="text-right px-6 py-3 font-semibold text-slate-200">Price</th>
              <th className="text-right px-6 py-3 font-semibold text-slate-200">Change</th>
              <th className="text-center px-6 py-3 font-semibold text-slate-200">Predictability</th>
              <th className="text-center px-6 py-3 font-semibold text-slate-200">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {stocks.map(stock => (
              <tr key={stock.id} className="hover:bg-slate-700/50 transition-colors">
                <td className="px-6 py-4">
                  <span className="font-semibold text-white">{stock.symbol}</span>
                </td>
                <td className="px-6 py-4 text-slate-300">{stock.name}</td>
                <td className="px-6 py-4 text-right">
                  <span className="font-semibold text-white">${stock.current_price.toFixed(2)}</span>
                </td>
                <td className="px-6 py-4 text-right">
                  <div className={`flex items-center justify-end gap-1 ${
                    stock.change_percent > 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {stock.change_percent > 0 ? (
                      <TrendingUp size={16} />
                    ) : (
                      <TrendingDown size={16} />
                    )}
                    <span className="font-semibold">
                      {stock.change_percent > 0 ? '+' : ''}{stock.change_percent.toFixed(2)}%
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 text-center">
                  <div className="flex items-center justify-center">
                    <div className="relative w-24 h-6 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          stock.predictability_score >= 0.7 ? 'bg-green-500' :
                          stock.predictability_score >= 0.5 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${stock.predictability_score * 100}%` }}
                      ></div>
                    </div>
                    <span className={`ml-2 text-sm font-semibold ${getPredictabilityColor(stock.predictability_score)}`}>
                      {(stock.predictability_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <Link
                      href={`/analysis/${stock.symbol}`}
                      className="p-1 hover:bg-blue-600/20 rounded transition-colors text-blue-400 hover:text-blue-300"
                      title="View analysis"
                    >
                      <Eye size={18} />
                    </Link>
                    <button
                      onClick={() => onRemove(stock.id)}
                      className="p-1 hover:bg-red-600/20 rounded transition-colors text-red-400 hover:text-red-300"
                      title="Remove from watchlist"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
