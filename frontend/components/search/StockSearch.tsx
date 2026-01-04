'use client'

import React from 'react'
import { Search, Filter } from 'lucide-react'

interface StockSearchProps {
  query: string
  onQueryChange: (value: string) => void
  market: string
  onMarketChange: (value: string) => void
}

export default function StockSearch({
  query,
  onQueryChange,
  market,
  onMarketChange,
}: StockSearchProps) {
  return (
    <div className="bg-slate-800/50 backdrop-blur rounded-lg p-6 border border-slate-700">
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by ticker or company name..."
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-gray-400" />
          <select
            value={market}
            onChange={(e) => onMarketChange(e.target.value)}
            className="px-4 py-2.5 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500 transition"
          >
            <option value="NSE">NSE</option>
            <option value="BSE">BSE</option>
            <option value="NYSE">NYSE</option>
          </select>
        </div>
      </div>
    </div>
  )
}
