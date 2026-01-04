'use client'

import { Trash2, Power, PowerOff, Clock } from 'lucide-react'

interface Alert {
  id: string
  stock_symbol: string
  alert_type: 'price_up' | 'price_down' | 'prediction_change' | 'volume_spike' | 'dividend'
  condition_type: 'absolute' | 'percentage'
  threshold_value: number
  frequency: 'realtime' | 'daily' | 'weekly'
  is_active: boolean
  created_at: string
  last_triggered_at?: string
}

interface AlertTableProps {
  alerts: Alert[]
  onDelete: (alertId: string) => void
  onToggle: (alert: Alert) => void
  isLoading?: boolean
}

const ALERT_TYPE_LABELS: Record<string, string> = {
  price_up: '📈 Price Up',
  price_down: '📉 Price Down',
  prediction_change: '🎯 Prediction Change',
  volume_spike: '📊 Volume Spike',
  dividend: '💰 Dividend'
}

const FREQUENCY_LABELS: Record<string, string> = {
  realtime: 'Real-time',
  daily: 'Daily',
  weekly: 'Weekly'
}

export default function AlertTable({
  alerts,
  onDelete,
  onToggle,
  isLoading
}: AlertTableProps) {
  if (alerts.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400">
        No alerts configured
      </div>
    )
  }

  return (
    <div className="bg-slate-800 rounded-lg overflow-hidden border border-slate-700">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-700 border-b border-slate-600">
            <tr>
              <th className="text-left px-6 py-3 font-semibold text-slate-200">Stock</th>
              <th className="text-left px-6 py-3 font-semibold text-slate-200">Alert Type</th>
              <th className="text-left px-6 py-3 font-semibold text-slate-200">Trigger</th>
              <th className="text-center px-6 py-3 font-semibold text-slate-200">Frequency</th>
              <th className="text-center px-6 py-3 font-semibold text-slate-200">Status</th>
              <th className="text-left px-6 py-3 font-semibold text-slate-200">Last Triggered</th>
              <th className="text-center px-6 py-3 font-semibold text-slate-200">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {alerts.map(alert => (
              <tr key={alert.id} className="hover:bg-slate-700/50 transition-colors">
                <td className="px-6 py-4">
                  <span className="font-semibold text-white">{alert.stock_symbol}</span>
                </td>
                <td className="px-6 py-4">
                  <span className="text-slate-300">{ALERT_TYPE_LABELS[alert.alert_type]}</span>
                </td>
                <td className="px-6 py-4">
                  <span className="text-slate-300">
                    {alert.threshold_value}{alert.condition_type === 'percentage' ? '%' : '$'}
                  </span>
                </td>
                <td className="px-6 py-4 text-center">
                  <span className="inline-flex items-center gap-1 text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
                    <Clock size={12} />
                    {FREQUENCY_LABELS[alert.frequency]}
                  </span>
                </td>
                <td className="px-6 py-4 text-center">
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                    alert.is_active
                      ? 'bg-green-900/30 text-green-400'
                      : 'bg-slate-700 text-slate-400'
                  }`}>
                    {alert.is_active ? (
                      <>
                        <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                        Active
                      </>
                    ) : (
                      <>
                        <span className="w-2 h-2 bg-slate-500 rounded-full"></span>
                        Inactive
                      </>
                    )}
                  </span>
                </td>
                <td className="px-6 py-4">
                  {alert.last_triggered_at ? (
                    <span className="text-sm text-slate-400">
                      {new Date(alert.last_triggered_at).toLocaleDateString()}
                    </span>
                  ) : (
                    <span className="text-sm text-slate-500">Never</span>
                  )}
                </td>
                <td className="px-6 py-4 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <button
                      onClick={() => onToggle(alert)}
                      disabled={isLoading}
                      className={`p-1 rounded transition-colors ${
                        alert.is_active
                          ? 'text-yellow-400 hover:bg-yellow-600/20'
                          : 'text-green-400 hover:bg-green-600/20'
                      } disabled:opacity-50`}
                      title={alert.is_active ? 'Disable alert' : 'Enable alert'}
                    >
                      {alert.is_active ? (
                        <Power size={18} />
                      ) : (
                        <PowerOff size={18} />
                      )}
                    </button>
                    <button
                      onClick={() => onDelete(alert.id)}
                      disabled={isLoading}
                      className="p-1 text-red-400 hover:bg-red-600/20 rounded transition-colors disabled:opacity-50"
                      title="Delete alert"
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
