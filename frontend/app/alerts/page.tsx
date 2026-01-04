'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import AlertForm from '@/components/alerts/AlertForm'
import AlertTable from '@/components/alerts/AlertTable'
import { Bell, Plus, Trash2 } from 'lucide-react'

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

interface AlertTrigger {
  id: string
  alert_id: string
  stock_symbol: string
  triggered_at: string
  current_value: number
  is_read: boolean
  dismissed_at?: string
}

export default function AlertsPage() {
  const [showAddForm, setShowAddForm] = useState(false)
  const [activeTab, setActiveTab] = useState<'alerts' | 'history'>('alerts')
  const queryClient = useQueryClient()

  // Fetch alerts
  const { data: alerts, isLoading: alertsLoading } = useQuery({
    queryKey: ['alerts'],
    queryFn: async () => {
      try {
        const response = await api.get('/alerts')
        return response.data as Alert[]
      } catch (error) {
        // Fallback to localStorage
        const stored = localStorage.getItem('alerts')
        return stored ? JSON.parse(stored) : []
      }
    },
    staleTime: 5 * 60 * 1000
  })

  // Fetch alert history
  const { data: history } = useQuery({
    queryKey: ['alert-history'],
    queryFn: async () => {
      try {
        const response = await api.get('/alerts/triggers')
        return response.data as AlertTrigger[]
      } catch (error) {
        return []
      }
    },
    staleTime: 2 * 60 * 1000
  })

  // Delete alert mutation
  const deleteAlertMutation = useMutation({
    mutationFn: async (alertId: string) => {
      try {
        await api.delete(`/alerts/${alertId}`)
      } catch (error) {
        // Fallback to localStorage
        const stored = localStorage.getItem('alerts')
        if (stored) {
          const alerts = JSON.parse(stored).filter((a: Alert) => a.id !== alertId)
          localStorage.setItem('alerts', JSON.stringify(alerts))
        }
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    }
  })

  // Toggle alert status mutation
  const toggleAlertMutation = useMutation({
    mutationFn: async ({ alertId, isActive }: { alertId: string, isActive: boolean }) => {
      try {
        const response = await api.put(`/alerts/${alertId}`, { is_active: !isActive })
        return response.data
      } catch (error) {
        // Fallback to localStorage
        const stored = localStorage.getItem('alerts')
        if (stored) {
          const allAlerts = JSON.parse(stored).map((a: Alert) =>
            a.id === alertId ? { ...a, is_active: !isActive } : a
          )
          localStorage.setItem('alerts', JSON.stringify(allAlerts))
        }
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    }
  })

  const handleDeleteAlert = async (alertId: string) => {
    if (confirm('Delete this alert?')) {
      await deleteAlertMutation.mutateAsync(alertId)
    }
  }

  const handleToggleAlert = async (alert: Alert) => {
    await toggleAlertMutation.mutateAsync({ alertId: alert.id, isActive: alert.is_active })
  }

  const handleCreateAlert = async (alertData: any) => {
    try {
      await api.post('/alerts', alertData)
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      setShowAddForm(false)
    } catch (error) {
      // Fallback to localStorage
      const stored = localStorage.getItem('alerts')
      const allAlerts = stored ? JSON.parse(stored) : []
      const newAlert = {
        ...alertData,
        id: Date.now().toString(),
        created_at: new Date().toISOString(),
        is_active: true
      }
      allAlerts.push(newAlert)
      localStorage.setItem('alerts', JSON.stringify(allAlerts))
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      setShowAddForm(false)
    }
  }

  const unreadCount = history?.filter(t => !t.is_read).length || 0

  if (alertsLoading) {
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
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">Alerts</h1>
          <p className="text-slate-400">Manage price and prediction alerts</p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-semibold"
        >
          <Plus size={18} />
          Create Alert
        </button>
      </div>

      {/* Unread Notifications Badge */}
      {unreadCount > 0 && (
        <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4 flex items-center gap-3">
          <Bell size={20} className="text-blue-400" />
          <div>
            <p className="font-semibold text-blue-400">You have {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}</p>
            <p className="text-sm text-slate-400">Check your alert history for details</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-700">
        {(['alerts', 'history'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium capitalize border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-300'
            }`}
          >
            {tab}
            {tab === 'history' && unreadCount > 0 && (
              <span className="ml-2 bg-red-600 text-white text-xs rounded-full px-2">
                {unreadCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'alerts' && (
        <div className="space-y-4">
          {alerts && alerts.length > 0 ? (
            <AlertTable
              alerts={alerts}
              onDelete={handleDeleteAlert}
              onToggle={handleToggleAlert}
              isLoading={deleteAlertMutation.isPending || toggleAlertMutation.isPending}
            />
          ) : (
            <div className="bg-slate-800 rounded-lg p-12 text-center">
              <Bell size={32} className="mx-auto mb-4 text-slate-600" />
              <p className="text-slate-400 mb-4">No alerts yet</p>
              <button
                onClick={() => setShowAddForm(true)}
                className="inline-flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                <Plus size={18} />
                Create Your First Alert
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <AlertHistory triggers={history || []} />
      )}

      {/* Add Alert Form Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-y-auto">
          <div className="bg-slate-800 rounded-lg p-6 w-full max-w-2xl my-8">
            <h2 className="text-2xl font-semibold mb-4">Create New Alert</h2>
            <AlertForm
              onSubmit={handleCreateAlert}
              onCancel={() => setShowAddForm(false)}
            />
          </div>
        </div>
      )}
    </div>
  )
}

function AlertHistory({ triggers }: { triggers: AlertTrigger[] }) {
  const [sortBy, setSortBy] = useState<'recent' | 'oldest'>('recent')

  const sortedTriggers = [...triggers].sort((a, b) => {
    const aTime = new Date(a.triggered_at).getTime()
    const bTime = new Date(b.triggered_at).getTime()
    return sortBy === 'recent' ? bTime - aTime : aTime - bTime
  })

  if (triggers.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-12 text-center">
        <p className="text-slate-400">No alert history yet</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {(['recent', 'oldest'] as const).map(option => (
          <button
            key={option}
            onClick={() => setSortBy(option)}
            className={`px-3 py-1 rounded text-sm capitalize transition-colors ${
              sortBy === option
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {option}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {sortedTriggers.map(trigger => (
          <div
            key={trigger.id}
            className={`bg-slate-800 rounded-lg p-4 border border-slate-700 ${
              !trigger.is_read ? 'border-blue-500' : ''
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-white">{trigger.stock_symbol}</span>
                  <span className="text-xs bg-slate-700 px-2 py-1 rounded">
                    {!trigger.is_read ? 'New' : 'Read'}
                  </span>
                </div>
                <p className="text-sm text-slate-400">
                  {new Date(trigger.triggered_at).toLocaleString()}
                </p>
                <p className="text-sm text-slate-300 mt-1">
                  Current Price: <span className="font-semibold text-blue-400">${trigger.current_value.toFixed(2)}</span>
                </p>
              </div>
              <div className="text-right text-sm text-slate-400">
                Alert #{trigger.alert_id}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
