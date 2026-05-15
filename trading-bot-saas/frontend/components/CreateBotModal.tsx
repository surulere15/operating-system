'use client'

import { useState } from 'react'
import { X } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface CreateBotModalProps {
  onClose: () => void
  onSuccess: () => void
}

export default function CreateBotModal({ onClose, onSuccess }: CreateBotModalProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    name: '',
    exchange: 'bybit',
    strategy: 'ma_crossover',
    capital: 35,
    markets: ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
    confidence_threshold: 60,
    max_daily_loss: 10,
    max_position_loss: 3,
    scan_interval: 300
  })

  const [leverageConfig, setLeverageConfig] = useState({
    'BTC/USDT': 15,
    'ETH/USDT': 15,
    'SOL/USDT': 20
  })

  const availableMarkets = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT',
    'DOT/USDT', 'LINK/USDT', 'UNI/USDT', 'ATOM/USDT', 'LTC/USDT', 'BCH/USDT',
    'NEAR/USDT', 'APT/USDT', 'ARB/USDT', 'OP/USDT', 'INJ/USDT', 'TIA/USDT',
    'SEI/USDT', 'SUI/USDT', 'FET/USDT', 'RNDR/USDT', 'IMX/USDT', 'AAVE/USDT',
    'CRV/USDT', 'LDO/USDT', 'MKR/USDT', 'SNX/USDT', 'COMP/USDT', 'DOGE/USDT',
    'WIF/USDT', 'BONK/USDT', 'FLOKI/USDT', 'SAND/USDT', 'MANA/USDT', 'AXS/USDT',
    'GALA/USDT'
  ]

  const handleMarketToggle = (market: string) => {
    setFormData(prev => {
      const markets = prev.markets.includes(market)
        ? prev.markets.filter(m => m !== market)
        : [...prev.markets, market]

      return { ...prev, markets }
    })

    // Add default leverage if adding new market
    if (!formData.markets.includes(market)) {
      setLeverageConfig(prev => ({
        ...prev,
        [market]: 15
      }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const token = localStorage.getItem('token')

    try {
      // Build config object
      const config = {
        strategy: formData.strategy,
        markets: formData.markets,
        leverage: leverageConfig,
        confidence_threshold: formData.confidence_threshold,
        max_daily_loss: formData.max_daily_loss,
        max_position_loss: formData.max_position_loss,
        scan_interval: formData.scan_interval
      }

      await axios.post(
        `${API_URL}/api/bots`,
        {
          name: formData.name,
          exchange: formData.exchange,
          capital: formData.capital,
          config
        },
        { headers: { Authorization: `Bearer ${token}` } }
      )

      onSuccess()
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create bot')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gray-800 border-b border-gray-700 p-6 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-white">Create Trading Bot</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Bot Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="My Trading Bot"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Exchange
              </label>
              <select
                value={formData.exchange}
                onChange={(e) => setFormData({ ...formData, exchange: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="bybit">Bybit</option>
                <option value="binance">Binance</option>
                <option value="okx">OKX</option>
                <option value="kraken">Kraken</option>
                <option value="coinbase">Coinbase</option>
                <option value="kucoin">KuCoin</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Trading Strategy ⭐ NEW
              </label>
              <select
                value={formData.strategy}
                onChange={(e) => setFormData({ ...formData, strategy: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="ma_crossover">MA Crossover (Trending)</option>
                <option value="grid">Grid Trading (Ranging)</option>
                <option value="dca">DCA (Accumulation)</option>
                <option value="macd">MACD (Momentum)</option>
              </select>
              <p className="text-gray-400 text-xs mt-1">
                {formData.strategy === 'ma_crossover' && 'Best for trending markets - Moving Average crossover'}
                {formData.strategy === 'grid' && 'Best for sideways markets - Buy low, sell high'}
                {formData.strategy === 'dca' && 'Best for long-term - Regular buys over time'}
                {formData.strategy === 'macd' && 'Best for momentum - MACD crossover signals'}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Capital (USDT) *
              </label>
              <input
                type="number"
                required
                min="35"
                step="0.01"
                value={formData.capital}
                onChange={(e) => setFormData({ ...formData, capital: parseFloat(e.target.value) })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="35"
              />
              <p className="text-gray-400 text-xs mt-1">Minimum: $35 USDT</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Scan Interval (seconds)
              </label>
              <input
                type="number"
                min="60"
                step="1"
                value={formData.scan_interval}
                onChange={(e) => setFormData({ ...formData, scan_interval: parseInt(e.target.value) })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-gray-400 text-xs mt-1">How often to scan markets</p>
            </div>
          </div>

          {/* Risk Management */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Risk Management</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Confidence Threshold (%)
                </label>
                <input
                  type="number"
                  min="50"
                  max="100"
                  value={formData.confidence_threshold}
                  onChange={(e) => setFormData({ ...formData, confidence_threshold: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-gray-400 text-xs mt-1">Min signal confidence to trade</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Max Daily Loss (%)
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={formData.max_daily_loss}
                  onChange={(e) => setFormData({ ...formData, max_daily_loss: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-gray-400 text-xs mt-1">Stop trading if hit</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Max Position Loss (%)
                </label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={formData.max_position_loss}
                  onChange={(e) => setFormData({ ...formData, max_position_loss: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-gray-400 text-xs mt-1">Stop loss per trade</p>
              </div>
            </div>
          </div>

          {/* Markets Selection */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">
              Trading Markets ({formData.markets.length} selected)
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
              {availableMarkets.map(market => (
                <button
                  key={market}
                  type="button"
                  onClick={() => handleMarketToggle(market)}
                  className={`px-3 py-2 rounded-lg text-sm font-semibold transition ${
                    formData.markets.includes(market)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {market.replace('/USDT', '')}
                </button>
              ))}
            </div>
          </div>

          {/* Leverage Configuration */}
          {formData.markets.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Leverage Settings</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {formData.markets.map(market => (
                  <div key={market}>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      {market.replace('/USDT', '')}
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={leverageConfig[market] || 15}
                      onChange={(e) => setLeverageConfig({
                        ...leverageConfig,
                        [market]: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                ))}
              </div>
              <p className="text-yellow-400 text-sm mt-4">
                ⚠️ Higher leverage = higher risk. Recommended: 10-25x
              </p>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500 rounded-lg text-red-400">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-4 pt-4 border-t border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || formData.markets.length === 0}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Bot'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
