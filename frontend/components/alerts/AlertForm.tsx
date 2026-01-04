'use client'

import { useState } from 'react'
import { AlertCircle } from 'lucide-react'

interface AlertFormProps {
  onSubmit: (data: any) => void
  onCancel: () => void
}

const ALERT_TYPES = [
  { value: 'price_up', label: 'Price rises above target' },
  { value: 'price_down', label: 'Price falls below target' },
  { value: 'prediction_change', label: 'Prediction score changes' },
  { value: 'volume_spike', label: 'Volume spike detected' },
  { value: 'dividend', label: 'Dividend announced' }
]

const CONDITION_TYPES = [
  { value: 'absolute', label: 'Absolute ($)' },
  { value: 'percentage', label: 'Percentage (%)' }
]

const FREQUENCIES = [
  { value: 'realtime', label: 'Real-time' },
  { value: 'daily', label: 'Daily digest' },
  { value: 'weekly', label: 'Weekly digest' }
]

export default function AlertForm({ onSubmit, onCancel }: AlertFormProps) {
  const [formData, setFormData] = useState({
    stock_symbol: '',
    alert_type: 'price_up',
    condition_type: 'percentage',
    threshold_value: '',
    frequency: 'realtime'
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.stock_symbol.trim()) {
      newErrors.stock_symbol = 'Stock symbol is required'
    }

    if (!formData.threshold_value) {
      newErrors.threshold_value = 'Threshold value is required'
    } else if (isNaN(parseFloat(formData.threshold_value))) {
      newErrors.threshold_value = 'Must be a valid number'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return

    onSubmit({
      ...formData,
      stock_symbol: formData.stock_symbol.toUpperCase(),
      threshold_value: parseFloat(formData.threshold_value)
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Stock Symbol */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Stock Symbol
        </label>
        <input
          type="text"
          value={formData.stock_symbol}
          onChange={(e) => setFormData({ ...formData, stock_symbol: e.target.value.toUpperCase() })}
          placeholder="e.g., AAPL"
          className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none"
        />
        {errors.stock_symbol && (
          <p className="text-red-400 text-sm mt-1">{errors.stock_symbol}</p>
        )}
      </div>

      {/* Alert Type */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Alert Type
        </label>
        <select
          value={formData.alert_type}
          onChange={(e) => setFormData({ ...formData, alert_type: e.target.value })}
          className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
        >
          {ALERT_TYPES.map(type => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Threshold Section */}
      {(formData.alert_type === 'price_up' || formData.alert_type === 'price_down' || formData.alert_type === 'prediction_change' || formData.alert_type === 'volume_spike') && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Condition Type
              </label>
              <select
                value={formData.condition_type}
                onChange={(e) => setFormData({ ...formData, condition_type: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
              >
                {CONDITION_TYPES.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Threshold Value
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.threshold_value}
                onChange={(e) => setFormData({ ...formData, threshold_value: e.target.value })}
                placeholder={formData.condition_type === 'percentage' ? '5' : '150.00'}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none"
              />
              {errors.threshold_value && (
                <p className="text-red-400 text-sm mt-1">{errors.threshold_value}</p>
              )}
            </div>
          </div>

          <div className="flex items-start gap-2 p-3 bg-blue-900/20 border border-blue-700 rounded">
            <AlertCircle size={18} className="text-blue-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-blue-300">
              {formData.alert_type === 'price_up' && `Alert when ${formData.stock_symbol || 'stock'} price rises ${formData.condition_type === 'percentage' ? 'by' : 'to'} ${formData.threshold_value || '___'} ${formData.condition_type === 'percentage' ? '%' : '$'}`}
              {formData.alert_type === 'price_down' && `Alert when ${formData.stock_symbol || 'stock'} price falls ${formData.condition_type === 'percentage' ? 'by' : 'to'} ${formData.threshold_value || '___'} ${formData.condition_type === 'percentage' ? '%' : '$'}`}
              {formData.alert_type === 'prediction_change' && `Alert when prediction score changes by ${formData.threshold_value || '___'} points`}
              {formData.alert_type === 'volume_spike' && `Alert when volume spikes ${formData.threshold_value || '___'} times average`}
            </p>
          </div>
        </>
      )}

      {/* Frequency */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Notification Frequency
        </label>
        <select
          value={formData.frequency}
          onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
          className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
        >
          {FREQUENCIES.map(freq => (
            <option key={freq.value} value={freq.value}>
              {freq.label}
            </option>
          ))}
        </select>
        <p className="text-xs text-slate-400 mt-1">
          {formData.frequency === 'realtime' && 'Get notified immediately when alert triggers'}
          {formData.frequency === 'daily' && 'Receive a daily digest of triggered alerts'}
          {formData.frequency === 'weekly' && 'Receive a weekly digest of triggered alerts'}
        </p>
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-4 border-t border-slate-700">
        <button
          type="submit"
          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-semibold text-white"
        >
          Create Alert
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors font-semibold text-white"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
