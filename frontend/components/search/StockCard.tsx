'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { TrendingUp } from 'lucide-react'
import { Stock } from '@/lib/services/stockService'

interface StockCardProps {
  stock: Stock
}

function getPredictabilityColor(score?: number) {
  if (!score) return 'bg-gray-600'
  if (score > 75) return 'bg-green-600'
  if (score > 50) return 'bg-yellow-600'
  return 'bg-red-600'
}

function getPredictabilityLabel(score?: number) {
  if (!score) return 'Not Analyzed'
  if (score > 75) return 'High'
  if (score > 50) return 'Medium'
  return 'Low'
}

export default function StockCard({ stock }: StockCardProps) {
  const router = useRouter()

  const handleClick = () => {
    router.push(`/dashboard/${stock.ticker}`)
  }

  return (
    <div
      onClick={handleClick}
      className="bg-slate-800/50 backdrop-blur rounded-lg p-6 border border-slate-700 hover:border-blue-500 cursor-pointer transition transform hover:scale-105"
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-bold text-white">{stock.ticker}</h3>
          <p className="text-sm text-gray-400">{stock.name}</p>
          <p className="text-xs text-gray-500 mt-1">{stock.market}</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-white">₹{stock.current_price.toFixed(2)}</p>
          <p className="text-xs text-gray-500">Current</p>
        </div>
      </div>

      <div className="border-t border-slate-700 pt-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`px-3 py-1 rounded-full ${getPredictabilityColor(stock.predictability_score)}`}>
              <p className="text-sm font-semibold text-white">
                {stock.predictability_score ? `${stock.predictability_score}` : '-'}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-400">Predictability</p>
              <p className="text-sm font-semibold text-white">
                {getPredictabilityLabel(stock.predictability_score)}
              </p>
            </div>
          </div>
          <TrendingUp className="w-5 h-5 text-blue-400" />
        </div>
      </div>

      <div className="mt-4 text-xs text-gray-500">
        Status: {stock.analysis_status}
      </div>
    </div>
  )
}
