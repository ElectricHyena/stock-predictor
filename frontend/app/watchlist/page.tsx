'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import WatchlistTable from '@/components/watchlist/WatchlistTable'
import PortfolioInsights from '@/components/watchlist/PortfolioInsights'
import { Plus, Download, Trash2 } from 'lucide-react'

interface Stock {
  id: number
  symbol: string
  name: string
  current_price: number
  change_percent: number
  predictability_score: number
}

interface Watchlist {
  id: number
  name: string
  description?: string
  stocks: Stock[]
  created_at: string
}

export default function WatchlistPage() {
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [newSymbol, setNewSymbol] = useState('')
  const [selectedWatchlist, setSelectedWatchlist] = useState<Watchlist | null>(null)
  const [sortBy, setSortBy] = useState<'score' | 'price' | 'change' | 'name'>('score')
  const queryClient = useQueryClient()

  // Fetch watchlists
  const { data: watchlists, isLoading: watchlistsLoading } = useQuery({
    queryKey: ['watchlists'],
    queryFn: async () => {
      try {
        const response = await api.get('/watchlists')
        return response.data as Watchlist[]
      } catch (error) {
        // Fallback to localStorage for demo
        const stored = localStorage.getItem('watchlist')
        return stored ? JSON.parse(stored) : []
      }
    },
    staleTime: 5 * 60 * 1000
  })

  // Auto-select first watchlist
  useEffect(() => {
    if (watchlists && watchlists.length > 0 && !selectedWatchlist) {
      setSelectedWatchlist(watchlists[0])
    }
  }, [watchlists])

  // Add stock mutation
  const addStockMutation = useMutation({
    mutationFn: async (symbol: string) => {
      if (!selectedWatchlist) throw new Error('No watchlist selected')
      try {
        const response = await api.post(`/watchlists/${selectedWatchlist.id}/stocks`, {
          symbol: symbol.toUpperCase()
        })
        return response.data
      } catch (error) {
        // Fallback to localStorage
        const stored = localStorage.getItem(`watchlist_${selectedWatchlist.id}`)
        const stocks = stored ? JSON.parse(stored) : []
        stocks.push({ symbol: symbol.toUpperCase(), predictability_score: 0.5 })
        localStorage.setItem(`watchlist_${selectedWatchlist.id}`, JSON.stringify(stocks))
        return { symbol: symbol.toUpperCase() }
      }
    },
    onSuccess: () => {
      setNewSymbol('')
      setShowAddDialog(false)
      queryClient.invalidateQueries({ queryKey: ['watchlists'] })
    }
  })

  // Remove stock mutation
  const removeStockMutation = useMutation({
    mutationFn: async (stockId: number) => {
      if (!selectedWatchlist) throw new Error('No watchlist selected')
      try {
        await api.delete(`/watchlists/${selectedWatchlist.id}/stocks/${stockId}`)
      } catch (error) {
        // Fallback to localStorage
        const stored = localStorage.getItem(`watchlist_${selectedWatchlist.id}`)
        if (stored) {
          const stocks = JSON.parse(stored).filter((s: any) => s.id !== stockId)
          localStorage.setItem(`watchlist_${selectedWatchlist.id}`, JSON.stringify(stocks))
        }
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlists'] })
    }
  })

  const handleAddStock = async () => {
    if (newSymbol.trim()) {
      await addStockMutation.mutateAsync(newSymbol.trim())
    }
  }

  const handleRemoveStock = async (stockId: number) => {
    if (confirm('Remove this stock from watchlist?')) {
      await removeStockMutation.mutateAsync(stockId)
    }
  }

  const handleExport = () => {
    if (!selectedWatchlist) return

    const csv = [
      ['Symbol', 'Name', 'Price', 'Change %', 'Predictability Score'],
      ...selectedWatchlist.stocks.map(s => [
        s.symbol,
        s.name,
        s.current_price.toFixed(2),
        s.change_percent.toFixed(2),
        s.predictability_score.toFixed(3)
      ])
    ]
      .map(row => row.join(','))
      .join('\n')

    downloadFile(csv, `watchlist_${selectedWatchlist.name}.csv`, 'text/csv')
  }

  const sortedStocks = selectedWatchlist
    ? [...selectedWatchlist.stocks].sort((a, b) => {
      switch (sortBy) {
        case 'score':
          return b.predictability_score - a.predictability_score
        case 'price':
          return b.current_price - a.current_price
        case 'change':
          return b.change_percent - a.change_percent
        case 'name':
          return a.name.localeCompare(b.name)
        default:
          return 0
      }
    })
    : []

  if (watchlistsLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-12 bg-slate-700 rounded w-1/3"></div>
          <div className="h-96 bg-slate-700 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <h1 className="text-4xl font-bold">Watchlist</h1>
        <p className="text-slate-400">Track and manage your favorite stocks</p>
      </div>

      {/* Watchlist Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {watchlists && watchlists.map((wl: Watchlist) => (
          <button
            key={wl.id}
            onClick={() => setSelectedWatchlist(wl)}
            className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
              selectedWatchlist?.id === wl.id
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {wl.name} ({wl.stocks.length})
          </button>
        ))}
      </div>

      {selectedWatchlist ? (
        <div className="space-y-6">
          {/* Portfolio Insights */}
          {sortedStocks.length > 0 && (
            <PortfolioInsights stocks={sortedStocks} />
          )}

          {/* Actions */}
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setShowAddDialog(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-semibold"
            >
              <Plus size={18} />
              Add Stock
            </button>
            <button
              onClick={handleExport}
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
            >
              <Download size={18} />
              Export CSV
            </button>
          </div>

          {/* Sorting */}
          <div className="flex gap-2">
            <span className="text-slate-400 text-sm">Sort by:</span>
            {(['score', 'price', 'change', 'name'] as const).map(option => (
              <button
                key={option}
                onClick={() => setSortBy(option)}
                className={`px-3 py-1 rounded text-sm capitalize transition-colors ${
                  sortBy === option
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {option === 'score' ? 'Predictability' : option}
              </button>
            ))}
          </div>

          {/* Stocks Table */}
          {sortedStocks.length > 0 ? (
            <WatchlistTable
              stocks={sortedStocks}
              onRemove={handleRemoveStock}
            />
          ) : (
            <div className="bg-slate-800 rounded-lg p-12 text-center">
              <p className="text-slate-400 mb-4">No stocks in this watchlist</p>
              <button
                onClick={() => setShowAddDialog(true)}
                className="inline-flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                <Plus size={18} />
                Add Your First Stock
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-slate-800 rounded-lg p-12 text-center">
          <p className="text-slate-400">No watchlists found. Create one to get started.</p>
        </div>
      )}

      {/* Add Stock Dialog */}
      {showAddDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold mb-4">Add Stock to Watchlist</h2>
            <div className="space-y-4">
              <div>
                <input
                  type="text"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddStock()}
                  placeholder="Enter stock symbol (e.g., AAPL)"
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500"
                  autoFocus
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleAddStock}
                  disabled={addStockMutation.isPending || !newSymbol.trim()}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 font-semibold"
                >
                  {addStockMutation.isPending ? 'Adding...' : 'Add'}
                </button>
                <button
                  onClick={() => setShowAddDialog(false)}
                  className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function downloadFile(content: string, filename: string, type: string) {
  const element = document.createElement('a')
  element.setAttribute('href', `data:${type};charset=utf-8,${encodeURIComponent(content)}`)
  element.setAttribute('download', filename)
  element.style.display = 'none'
  document.body.appendChild(element)
  element.click()
  document.body.removeChild(element)
}
