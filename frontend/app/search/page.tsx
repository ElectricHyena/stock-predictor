'use client'

import { useState } from 'react'
import { useStockSearch } from '@/lib/services/stockService'
import { useDebounce } from '@/lib/hooks/useDebounce'
import StockSearch from '@/components/search/StockSearch'
import StockCard from '@/components/search/StockCard'
import { Loader2, AlertCircle } from 'lucide-react'

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [market, setMarket] = useState('NSE')

  const debouncedQuery = useDebounce(searchQuery, 300)
  const { data: results, isLoading, error } = useStockSearch(debouncedQuery, market)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-8">Stock Discovery</h1>

        <StockSearch
          query={searchQuery}
          onQueryChange={setSearchQuery}
          market={market}
          onMarketChange={setMarket}
        />

        <div className="mt-8">
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
              <span className="ml-2 text-gray-400">Searching stocks...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4 flex items-center">
              <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
              <span className="text-red-400">{error.message}</span>
            </div>
          )}

          {!isLoading && !error && results && results.length === 0 && debouncedQuery && (
            <div className="text-center py-12">
              <p className="text-gray-400 text-lg">No stocks found for "{debouncedQuery}"</p>
              <p className="text-gray-500 text-sm mt-2">Try searching with a different ticker or company name</p>
            </div>
          )}

          {!isLoading && !error && results && results.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {results.map((stock) => (
                <StockCard key={stock.ticker} stock={stock} />
              ))}
            </div>
          )}

          {!isLoading && !error && (!results || results.length === 0) && !debouncedQuery && (
            <div className="text-center py-12">
              <p className="text-gray-400 text-lg">Start by searching for a stock ticker</p>
              <p className="text-gray-500 text-sm mt-2">Enter a ticker (e.g., AVANTI, RELIANCE) or company name</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
