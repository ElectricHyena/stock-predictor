'use client'

import { useState } from 'react'
import { Plus, X } from 'lucide-react'

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

interface Strategy {
  name: string
  description: string
  entryConditions: Condition[]
  exitConditions: Condition[]
  positionSizing: PositionSizing
  riskManagement: RiskManagement
  universe: StockUniverse
}

interface StrategyBuilderProps {
  strategy: Strategy
  onStrategyChange: (strategy: Strategy) => void
}

const CONDITION_TYPES = [
  { value: 'price', label: 'Price' },
  { value: 'indicator', label: 'Indicator (RSI, MACD)' },
  { value: 'volume', label: 'Volume' },
  { value: 'time', label: 'Time' },
  { value: 'predictability', label: 'Predictability Score' }
]

const OPERATORS = [
  { value: 'gt', label: '>' },
  { value: 'gte', label: '>=' },
  { value: 'lt', label: '<' },
  { value: 'lte', label: '<=' },
  { value: 'eq', label: '=' }
]

export default function StrategyBuilder({ strategy, onStrategyChange }: StrategyBuilderProps) {
  const addCondition = (isExit: boolean) => {
    const newCondition: Condition = {
      id: Date.now().toString(),
      type: 'price',
      operator: 'gt',
      value: '',
      logicOperator: isExit ? strategy.exitConditions.length > 0 ? 'AND' : undefined : strategy.entryConditions.length > 0 ? 'AND' : undefined
    }

    if (isExit) {
      onStrategyChange({
        ...strategy,
        exitConditions: [...strategy.exitConditions, newCondition]
      })
    } else {
      onStrategyChange({
        ...strategy,
        entryConditions: [...strategy.entryConditions, newCondition]
      })
    }
  }

  const removeCondition = (id: string, isExit: boolean) => {
    if (isExit) {
      onStrategyChange({
        ...strategy,
        exitConditions: strategy.exitConditions.filter(c => c.id !== id)
      })
    } else {
      onStrategyChange({
        ...strategy,
        entryConditions: strategy.entryConditions.filter(c => c.id !== id)
      })
    }
  }

  const updateCondition = (id: string, updates: Partial<Condition>, isExit: boolean) => {
    const conditions = isExit ? strategy.exitConditions : strategy.entryConditions
    const updated = conditions.map(c => c.id === id ? { ...c, ...updates } : c)

    if (isExit) {
      onStrategyChange({ ...strategy, exitConditions: updated })
    } else {
      onStrategyChange({ ...strategy, entryConditions: updated })
    }
  }

  return (
    <div className="space-y-6">
      {/* Entry Conditions */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          📈 Entry Conditions
        </h3>

        <div className="space-y-3">
          {strategy.entryConditions.map((condition, idx) => (
            <ConditionRow
              key={condition.id}
              condition={condition}
              isFirst={idx === 0}
              onChange={(updates) => updateCondition(condition.id, updates, false)}
              onRemove={() => removeCondition(condition.id, false)}
            />
          ))}
        </div>

        <button
          onClick={() => addCondition(false)}
          className="mt-4 flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded transition-colors text-sm"
        >
          <Plus size={16} />
          Add Entry Condition
        </button>
      </div>

      {/* Exit Conditions */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          📉 Exit Conditions
        </h3>

        <div className="space-y-3">
          {strategy.exitConditions.map((condition, idx) => (
            <ConditionRow
              key={condition.id}
              condition={condition}
              isFirst={idx === 0}
              onChange={(updates) => updateCondition(condition.id, updates, true)}
              onRemove={() => removeCondition(condition.id, true)}
            />
          ))}
        </div>

        <button
          onClick={() => addCondition(true)}
          className="mt-4 flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded transition-colors text-sm"
        >
          <Plus size={16} />
          Add Exit Condition
        </button>
      </div>

      {/* Position Sizing */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">💰 Position Sizing</h3>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">Type</label>
            <select
              value={strategy.positionSizing.type}
              onChange={(e) => onStrategyChange({
                ...strategy,
                positionSizing: { ...strategy.positionSizing, type: e.target.value as any }
              })}
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
            >
              <option value="fixed">Fixed ($)</option>
              <option value="percentage">Percentage (%)</option>
              <option value="dynamic">Dynamic</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-2">Value</label>
            <input
              type="number"
              value={strategy.positionSizing.value}
              onChange={(e) => onStrategyChange({
                ...strategy,
                positionSizing: { ...strategy.positionSizing, value: parseFloat(e.target.value) }
              })}
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
            />
          </div>
        </div>

        {strategy.positionSizing.type === 'percentage' && (
          <div className="mt-4">
            <label className="block text-sm text-slate-400 mb-2">Max Allocation (%)</label>
            <input
              type="number"
              value={strategy.positionSizing.maxAllocation || 100}
              onChange={(e) => onStrategyChange({
                ...strategy,
                positionSizing: { ...strategy.positionSizing, maxAllocation: parseFloat(e.target.value) }
              })}
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
            />
          </div>
        )}
      </div>

      {/* Risk Management */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">⚠️ Risk Management</h3>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">Stop Loss (%)</label>
            <input
              type="number"
              value={strategy.riskManagement.stopLoss}
              onChange={(e) => onStrategyChange({
                ...strategy,
                riskManagement: { ...strategy.riskManagement, stopLoss: parseFloat(e.target.value) }
              })}
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-2">Take Profit (%)</label>
            <input
              type="number"
              value={strategy.riskManagement.takeProfit}
              onChange={(e) => onStrategyChange({
                ...strategy,
                riskManagement: { ...strategy.riskManagement, takeProfit: parseFloat(e.target.value) }
              })}
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-2">Max Risk per Trade (%)</label>
            <input
              type="number"
              value={strategy.riskManagement.maxRisk}
              onChange={(e) => onStrategyChange({
                ...strategy,
                riskManagement: { ...strategy.riskManagement, maxRisk: parseFloat(e.target.value) }
              })}
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-2">Max Drawdown (%)</label>
            <input
              type="number"
              value={strategy.riskManagement.maxDrawdown}
              onChange={(e) => onStrategyChange({
                ...strategy,
                riskManagement: { ...strategy.riskManagement, maxDrawdown: parseFloat(e.target.value) }
              })}
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
            />
          </div>
        </div>
      </div>

      {/* Stock Universe */}
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">📊 Stock Universe</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">Universe Type</label>
            <select
              value={strategy.universe.type}
              onChange={(e) => onStrategyChange({
                ...strategy,
                universe: { ...strategy.universe, type: e.target.value as any }
              })}
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
            >
              <option value="watchlist">Watchlist</option>
              <option value="individual">Individual Stocks</option>
              <option value="sector">Sector</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-2">
              {strategy.universe.type === 'sector' ? 'Sector' : 'Stocks/Watchlist'}
            </label>
            <input
              type="text"
              value={typeof strategy.universe.value === 'string' ? strategy.universe.value : ''}
              onChange={(e) => onStrategyChange({
                ...strategy,
                universe: { ...strategy.universe, value: e.target.value }
              })}
              placeholder={
                strategy.universe.type === 'sector'
                  ? 'e.g., Technology, Healthcare'
                  : 'e.g., AAPL, MSFT, GOOGL'
              }
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
            />
            <p className="text-xs text-slate-400 mt-1">
              {strategy.universe.type === 'individual' ? 'Separate symbols with commas' : ''}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

interface ConditionRowProps {
  condition: Condition
  isFirst: boolean
  onChange: (updates: Partial<Condition>) => void
  onRemove: () => void
}

function ConditionRow({ condition, isFirst, onChange, onRemove }: ConditionRowProps) {
  return (
    <div className="flex items-end gap-2 p-3 bg-slate-700/50 rounded border border-slate-600">
      {!isFirst && (
        <div className="flex-shrink-0">
          <select
            value={condition.logicOperator || 'AND'}
            onChange={(e) => onChange({ logicOperator: e.target.value as 'AND' | 'OR' })}
            className="bg-slate-600 border border-slate-500 rounded px-2 py-1 text-white text-sm"
          >
            <option value="AND">AND</option>
            <option value="OR">OR</option>
          </select>
        </div>
      )}

      <select
        value={condition.type}
        onChange={(e) => onChange({ type: e.target.value as any })}
        className="flex-1 bg-slate-600 border border-slate-500 rounded px-2 py-1 text-white text-sm"
      >
        {CONDITION_TYPES.map(t => (
          <option key={t.value} value={t.value}>{t.label}</option>
        ))}
      </select>

      <select
        value={condition.operator}
        onChange={(e) => onChange({ operator: e.target.value as any })}
        className="flex-shrink-0 bg-slate-600 border border-slate-500 rounded px-2 py-1 text-white text-sm"
      >
        {OPERATORS.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>

      <input
        type="text"
        value={condition.value}
        onChange={(e) => onChange({ value: e.target.value })}
        placeholder="Value"
        className="flex-1 bg-slate-600 border border-slate-500 rounded px-2 py-1 text-white text-sm"
      />

      <button
        onClick={onRemove}
        className="flex-shrink-0 p-1 hover:bg-red-600/50 rounded transition-colors"
      >
        <X size={18} className="text-red-400" />
      </button>
    </div>
  )
}
