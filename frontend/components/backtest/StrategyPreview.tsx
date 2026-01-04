'use client'

interface Condition {
  id: string
  type: 'price' | 'indicator' | 'volume' | 'time' | 'predictability'
  operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
  value: string | number
  logicOperator?: 'AND' | 'OR'
}

interface StrategyPreviewProps {
  strategy: {
    name: string
    description: string
    entryConditions: Condition[]
    exitConditions: Condition[]
    positionSizing: { type: string; value: number; maxAllocation?: number }
    riskManagement: { stopLoss: number; takeProfit: number; maxRisk: number; maxDrawdown: number }
    universe: { type: string; value: string | string[] }
  }
}

export default function StrategyPreview({ strategy }: StrategyPreviewProps) {
  const formatCondition = (cond: Condition, isFirst: boolean): string => {
    const operators: Record<string, string> = {
      gt: '>',
      gte: '>=',
      lt: '<',
      lte: '<=',
      eq: '='
    }

    const prefix = !isFirst ? `${cond.logicOperator || 'AND'} ` : ''
    const typeLabel = cond.type.charAt(0).toUpperCase() + cond.type.slice(1)

    return `${prefix}${typeLabel} ${operators[cond.operator]} ${cond.value}`
  }

  return (
    <div className="bg-slate-700 rounded-lg p-4 space-y-3 text-sm">
      {strategy.name && (
        <div>
          <p className="text-slate-400">Strategy:</p>
          <p className="font-semibold text-white">{strategy.name}</p>
        </div>
      )}

      {strategy.entryConditions.length > 0 && (
        <div>
          <p className="text-slate-400">Entry Logic:</p>
          <div className="font-mono text-xs text-blue-300 space-y-1 mt-1">
            {strategy.entryConditions.map((cond, idx) => (
              <p key={cond.id}>
                {formatCondition(cond, idx === 0)}
              </p>
            ))}
          </div>
        </div>
      )}

      {strategy.exitConditions.length > 0 && (
        <div>
          <p className="text-slate-400">Exit Logic:</p>
          <div className="font-mono text-xs text-red-300 space-y-1 mt-1">
            {strategy.exitConditions.map((cond, idx) => (
              <p key={cond.id}>
                {formatCondition(cond, idx === 0)}
              </p>
            ))}
          </div>
        </div>
      )}

      <div className="pt-2 border-t border-slate-600 space-y-2">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <p className="text-slate-400">Position Size:</p>
            <p className="font-semibold text-white">
              {strategy.positionSizing.value}{strategy.positionSizing.type === 'percentage' ? '%' : ''}
            </p>
          </div>
          <div>
            <p className="text-slate-400">Stop Loss:</p>
            <p className="font-semibold text-red-400">
              -{strategy.riskManagement.stopLoss}%
            </p>
          </div>
          <div>
            <p className="text-slate-400">Take Profit:</p>
            <p className="font-semibold text-green-400">
              +{strategy.riskManagement.takeProfit}%
            </p>
          </div>
          <div>
            <p className="text-slate-400">Max Drawdown:</p>
            <p className="font-semibold text-white">
              {strategy.riskManagement.maxDrawdown}%
            </p>
          </div>
        </div>
      </div>

      {strategy.universe.value && (
        <div>
          <p className="text-slate-400">Universe:</p>
          <p className="text-white font-mono text-xs break-all">
            {typeof strategy.universe.value === 'string'
              ? strategy.universe.value
              : strategy.universe.value.join(', ')}
          </p>
        </div>
      )}

      {strategy.entryConditions.length === 0 && (
        <p className="text-yellow-400 text-xs">
          ⚠️ Add at least one entry condition
        </p>
      )}
    </div>
  )
}
