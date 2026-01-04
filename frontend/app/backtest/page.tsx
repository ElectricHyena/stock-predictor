'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import StrategyBuilder from '@/components/backtest/StrategyBuilder'
import StrategyPreview from '@/components/backtest/StrategyPreview'
import { Save, Plus, Copy } from 'lucide-react'

interface Strategy {
  id?: string
  name: string
  description: string
  entryConditions: Condition[]
  exitConditions: Condition[]
  positionSizing: PositionSizing
  riskManagement: RiskManagement
  universe: StockUniverse
  complexity?: 'simple' | 'moderate' | 'complex'
}

interface Condition {
  id: string
  type: 'price' | 'indicator' | 'volume' | 'time' | 'predictability'
  operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
  value: string | number
  logicOperator?: 'AND' | 'OR'
}

interface PositionSizing {
  type: 'fixed' | 'percentage' | 'dynamic'
  value: number
  maxAllocation?: number
}

interface RiskManagement {
  stopLoss: number
  takeProfit: number
  maxRisk: number
  maxDrawdown: number
}

interface StockUniverse {
  type: 'watchlist' | 'individual' | 'sector'
  value: string | string[]
}

const STRATEGY_TEMPLATES: Array<{ name: string; description: string; entryConditions: Condition[] }> = [
  {
    name: 'Momentum',
    description: 'Buy on uptrend, sell on reversal',
    entryConditions: [
      { id: '1', type: 'price', operator: 'gt', value: 'yesterday_close', logicOperator: 'AND' },
      { id: '2', type: 'indicator', operator: 'gt', value: '50' }
    ]
  },
  {
    name: 'Mean Reversion',
    description: 'Buy when price drops, sell when recovers',
    entryConditions: [
      { id: '1', type: 'price', operator: 'lt', value: 'moving_average_20', logicOperator: 'AND' },
      { id: '2', type: 'indicator', operator: 'lt', value: '30' }
    ]
  },
  {
    name: 'Breakout',
    description: 'Buy above resistance, exit below support',
    entryConditions: [
      { id: '1', type: 'price', operator: 'gt', value: '52w_high' }
    ]
  },
  {
    name: 'Value',
    description: 'Buy undervalued stocks with strong fundamentals',
    entryConditions: [
      { id: '1', type: 'predictability', operator: 'gt', value: '0.7' }
    ]
  },
  {
    name: 'Contrarian',
    description: 'Buy when market is pessimistic',
    entryConditions: [
      { id: '1', type: 'predictability', operator: 'lt', value: '0.3', logicOperator: 'AND' },
      { id: '2', type: 'volume', operator: 'gt', value: '2' }
    ]
  }
]

export default function BacktestPage() {
  const [strategy, setStrategy] = useState<Strategy>({
    name: '',
    description: '',
    entryConditions: [],
    exitConditions: [],
    positionSizing: { type: 'fixed', value: 100 },
    riskManagement: { stopLoss: 2, takeProfit: 5, maxRisk: 100, maxDrawdown: 20 },
    universe: { type: 'individual', value: '' }
  })
  const [showPreview, setShowPreview] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [validationErrors, setValidationErrors] = useState<string[]>([])

  const { data: savedStrategies } = useQuery({
    queryKey: ['strategies'],
    queryFn: async () => {
      const response = await api.get('/strategies')
      return response.data || []
    },
    staleTime: 10 * 60 * 1000
  })

  const validateStrategy = (): boolean => {
    const errors: string[] = []

    if (!strategy.name.trim()) errors.push('Strategy name is required')
    if (strategy.entryConditions.length === 0) errors.push('At least one entry condition is required')
    if (strategy.entryConditions.length > 10) errors.push('Maximum 10 entry conditions allowed')
    if (strategy.exitConditions.length > 10) errors.push('Maximum 10 exit conditions allowed')

    // Check for contradictions
    const entryPrices = strategy.entryConditions.filter(c => c.type === 'price')
    if (entryPrices.some(c => c.operator === 'gt') && entryPrices.some(c => c.operator === 'lt')) {
      errors.push('Conflicting price conditions detected')
    }

    if (strategy.positionSizing.maxAllocation && strategy.positionSizing.maxAllocation > 100) {
      errors.push('Position allocation cannot exceed 100%')
    }

    setValidationErrors(errors)
    return errors.length === 0
  }

  const handleSaveStrategy = async () => {
    if (!validateStrategy()) return

    setIsSaving(true)
    try {
      const payload = {
        ...strategy,
        complexity: calculateComplexity(strategy)
      }

      await api.post('/strategies', payload)
      alert('Strategy saved successfully!')
      setStrategy({
        name: '',
        description: '',
        entryConditions: [],
        exitConditions: [],
        positionSizing: { type: 'fixed', value: 100 },
        riskManagement: { stopLoss: 2, takeProfit: 5, maxRisk: 100, maxDrawdown: 20 },
        universe: { type: 'individual', value: '' }
      })
    } catch (error) {
      alert('Failed to save strategy')
      console.error(error)
    } finally {
      setIsSaving(false)
    }
  }

  const loadTemplate = (template: typeof STRATEGY_TEMPLATES[0]) => {
    setStrategy({
      ...strategy,
      name: template.name,
      description: template.description,
      entryConditions: template.entryConditions
    })
  }

  const loadSavedStrategy = (savedStrategy: any) => {
    setStrategy(savedStrategy)
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold">Backtest Strategy Builder</h1>
        <p className="text-slate-400">Create and test custom trading strategies</p>
      </div>

      {/* Templates */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Copy size={20} />
          Quick Start Templates
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
          {STRATEGY_TEMPLATES.map((template, idx) => (
            <button
              key={idx}
              onClick={() => loadTemplate(template)}
              className="p-3 border border-slate-700 rounded-lg hover:border-blue-500 hover:bg-slate-700 transition-colors text-left"
            >
              <p className="font-semibold text-white">{template.name}</p>
              <p className="text-xs text-slate-400 mt-1">{template.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
          <p className="font-semibold text-red-400 mb-2">Validation Errors:</p>
          <ul className="space-y-1">
            {validationErrors.map((error, idx) => (
              <li key={idx} className="text-red-300 text-sm">• {error}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Builder */}
        <div className="lg:col-span-2">
          <StrategyBuilder
            strategy={strategy}
            onStrategyChange={setStrategy}
          />
        </div>

        {/* Preview & Actions */}
        <div className="space-y-4">
          <div className="bg-slate-800 rounded-lg p-6 sticky top-4 space-y-4">
            <h3 className="font-semibold text-lg">Summary</h3>

            <div>
              <label className="block text-sm text-slate-400 mb-2">Strategy Name</label>
              <input
                type="text"
                value={strategy.name}
                onChange={(e) => setStrategy({ ...strategy, name: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
                placeholder="e.g., My Momentum Strategy"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">Description</label>
              <textarea
                value={strategy.description}
                onChange={(e) => setStrategy({ ...strategy, description: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white text-sm"
                rows={3}
                placeholder="Describe your strategy..."
              />
            </div>

            <StrategyPreview strategy={strategy} />

            <div className="space-y-2 pt-4">
              <button
                onClick={() => setShowPreview(!showPreview)}
                className="w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
              >
                {showPreview ? 'Hide' : 'Show'} Details
              </button>
              <button
                onClick={handleSaveStrategy}
                disabled={isSaving}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 font-semibold"
              >
                <Save size={18} />
                Save Strategy
              </button>
            </div>
          </div>

          {/* Saved Strategies */}
          {savedStrategies && savedStrategies.length > 0 && (
            <div className="bg-slate-800 rounded-lg p-6">
              <h3 className="font-semibold mb-3">Your Strategies</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {savedStrategies.map((saved: any) => (
                  <button
                    key={saved.id}
                    onClick={() => loadSavedStrategy(saved)}
                    className="w-full text-left p-2 border border-slate-700 rounded hover:bg-slate-700 transition-colors"
                  >
                    <p className="text-sm font-medium text-white">{saved.name}</p>
                    <p className="text-xs text-slate-400">{saved.description}</p>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function calculateComplexity(strategy: Strategy): 'simple' | 'moderate' | 'complex' {
  const totalConditions = strategy.entryConditions.length + strategy.exitConditions.length
  if (totalConditions <= 2) return 'simple'
  if (totalConditions <= 6) return 'moderate'
  return 'complex'
}
