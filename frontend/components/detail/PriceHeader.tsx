'use client'

import React from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { StockDetail } from '@/lib/services/stockService'

interface PriceHeaderProps {
  stock: StockDetail
}

export default function PriceHeader({ stock }: PriceHeaderProps) {
  const priceChange = stock.previous_close ? stock.current_price - stock.previous_close : 0
  const percentChange = stock.previous_close ? (priceChange / stock.previous_close) * 100 : 0
  const isPositive = priceChange >= 0

  return (
    <div className="bg-gradient-to-r from-slate-800/50 to-slate-700/50 backdrop-blur rounded-lg p-8 border border-slate-700">
      <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
        <div>
          <h2 className="text-gray-400 text-lg mb-2">{stock.name}</h2>
          <div className="flex items-baseline gap-4">
            <span className="text-5xl font-bold text-white">₹{stock.current_price.toFixed(2)}</span>
            <div
              className={`flex items-center gap-1 px-3 py-1 rounded-lg ${
                isPositive ? 'bg-green-600/20' : 'bg-red-600/20'
              }`}
            >
              {isPositive ? (
                <TrendingUp className="w-5 h-5 text-green-400" />
              ) : (
                <TrendingDown className="w-5 h-5 text-red-400" />
              )}
              <span className={isPositive ? 'text-green-400' : 'text-red-400'}>
                {isPositive ? '+' : ''}
                {priceChange.toFixed(2)} ({percentChange.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>
        <div className="mt-6 md:mt-0 text-right">
          <p className="text-gray-400 text-sm">Market</p>
          <p className="text-xl font-semibold text-white">{stock.market}</p>
        </div>
      </div>
    </div>
  )
}
