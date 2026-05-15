'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import {
  Play,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Activity,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Info
} from 'lucide-react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function BacktestPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [error, setError] = useState('')

  const [config, setConfig] = useState({
    exchange: 'bybit',
    symbol: 'BTC/USDT',
    strategy: 'ma_crossover',
    timeframe: '15m',
    days: 30,
    capital: 100
  })

  const runBacktest = async () => {
    setLoading(true)
    setError('')
    setResults(null)

    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }

    try {
      const response = await axios.post(
        `${API_URL}/api/backtest`,
        config,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setResults(response.data.backtest)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Backtest failed')
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value)
  }

  const getStrategyInfo = () => {
    const strategies: any = {
      ma_crossover: {
        name: 'MA Crossover',
        desc: 'Moving average crossover with RSI and volume confirmation',
        bestFor: 'Trending markets'
      },
      grid: {
        name: 'Grid Trading',
        desc: 'Buy low, sell high within a price range',
        bestFor: 'Sideways/ranging markets'
      },
      dca: {
        name: 'DCA',
        desc: 'Regular buys to accumulate over time',
        bestFor: 'Long-term accumulation'
      },
      macd: {
        name: 'MACD',
        desc: 'MACD crossover with histogram and RSI confirmation',
        bestFor: 'Momentum trading'
      }
    }
    return strategies[config.strategy] || strategies.ma_crossover
  }

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Strategy Backtesting</h1>
          <p className="text-gray-400">Test your strategy on historical data before going live</p>
        </div>

        {/* Configuration */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Backtest Configuration</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Exchange
              </label>
              <select
                value={config.exchange}
                onChange={(e) => setConfig({ ...config, exchange: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              >
                <option value="bybit">Bybit</option>
                <option value="binance">Binance</option>
                <option value="okx">OKX</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Trading Pair
              </label>
              <select
                value={config.symbol}
                onChange={(e) => setConfig({ ...config, symbol: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              >
                <option value="BTC/USDT">BTC/USDT</option>
                <option value="ETH/USDT">ETH/USDT</option>
                <option value="SOL/USDT">SOL/USDT</option>
                <option value="XRP/USDT">XRP/USDT</option>
                <option value="ADA/USDT">ADA/USDT</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Strategy
              </label>
              <select
                value={config.strategy}
                onChange={(e) => setConfig({ ...config, strategy: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              >
                <option value="ma_crossover">MA Crossover</option>
                <option value="grid">Grid Trading</option>
                <option value="dca">DCA</option>
                <option value="macd">MACD</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Timeframe
              </label>
              <select
                value={config.timeframe}
                onChange={(e) => setConfig({ ...config, timeframe: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              >
                <option value="15m">15 minutes</option>
                <option value="1h">1 hour</option>
                <option value="4h">4 hours</option>
                <option value="1d">1 day</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Historical Days
              </label>
              <input
                type="number"
                min="7"
                max="365"
                value={config.days}
                onChange={(e) => setConfig({ ...config, days: parseInt(e.target.value) })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Initial Capital (USDT)
              </label>
              <input
                type="number"
                min="100"
                step="100"
                value={config.capital}
                onChange={(e) => setConfig({ ...config, capital: parseFloat(e.target.value) })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              />
            </div>
          </div>

          {/* Strategy Info */}
          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-400 mt-0.5" />
              <div>
                <h4 className="font-semibold text-white mb-1">{getStrategyInfo().name}</h4>
                <p className="text-sm text-gray-300 mb-1">{getStrategyInfo().desc}</p>
                <p className="text-xs text-blue-400">Best for: {getStrategyInfo().bestFor}</p>
              </div>
            </div>
          </div>

          <button
            onClick={runBacktest}
            disabled={loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Activity className="w-5 h-5 animate-spin" />
                Running Backtest...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                Run Backtest
              </>
            )}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 text-red-400">
            {error}
          </div>
        )}

        {/* Results */}
        {results && (
          <>
            {/* Performance Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className={`rounded-lg p-6 ${results.total_pnl >= 0 ? 'bg-gradient-to-br from-green-600 to-green-700' : 'bg-gradient-to-br from-red-600 to-red-700'}`}>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <p className="text-green-100 text-sm font-medium">Total P&L</p>
                    <h3 className="text-3xl font-bold text-white mt-1">
                      {formatCurrency(results.total_pnl)}
                    </h3>
                    <p className={`text-sm mt-1 ${results.total_pnl_percent >= 0 ? 'text-green-100' : 'text-red-100'}`}>
                      {results.total_pnl_percent >= 0 ? '+' : ''}{results.total_pnl_percent}%
                    </p>
                  </div>
                  <DollarSign className="w-10 h-10 text-green-100" />
                </div>
              </div>

              <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <p className="text-blue-100 text-sm font-medium">Win Rate</p>
                    <h3 className="text-3xl font-bold text-white mt-1">
                      {results.win_rate}%
                    </h3>
                    <p className="text-blue-100 text-sm mt-1">
                      {results.winning_trades}W / {results.losing_trades}L
                    </p>
                  </div>
                  <Target className="w-10 h-10 text-blue-100" />
                </div>
              </div>

              <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <p className="text-purple-100 text-sm font-medium">Profit Factor</p>
                    <h3 className="text-3xl font-bold text-white mt-1">
                      {results.profit_factor}
                    </h3>
                    <p className="text-purple-100 text-sm mt-1">
                      {results.total_trades} trades
                    </p>
                  </div>
                  <BarChart3 className="w-10 h-10 text-purple-100" />
                </div>
              </div>

              <div className="bg-gradient-to-br from-orange-600 to-orange-700 rounded-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <p className="text-orange-100 text-sm font-medium">Max Drawdown</p>
                    <h3 className="text-3xl font-bold text-white mt-1">
                      {results.max_drawdown_percent}%
                    </h3>
                    <p className="text-orange-100 text-sm mt-1">
                      {formatCurrency(results.max_drawdown)}
                    </p>
                  </div>
                  <TrendingDown className="w-10 h-10 text-orange-100" />
                </div>
              </div>
            </div>

            {/* Equity Curve Chart */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Equity Curve</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={results.equity_curve.map((e: any) => ({
                  timestamp: new Date(e.timestamp).toLocaleDateString(),
                  equity: e.equity
                }))}>
                  <defs>
                    <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="timestamp" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="equity"
                    stroke="#10b981"
                    strokeWidth={2}
                    fill="url(#equityGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Detailed Stats */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Detailed Statistics</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-400 mb-2">Trade Stats</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Total Trades:</span>
                      <span className="text-white font-semibold">{results.total_trades}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Avg Duration:</span>
                      <span className="text-white font-semibold">{results.avg_duration_hours.toFixed(1)}h</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Best Trade:</span>
                      <span className="text-green-400 font-semibold">{formatCurrency(results.best_trade)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Worst Trade:</span>
                      <span className="text-red-400 font-semibold">{formatCurrency(results.worst_trade)}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-400 mb-2">Performance</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Avg Win:</span>
                      <span className="text-green-400 font-semibold">{formatCurrency(results.avg_win)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Avg Loss:</span>
                      <span className="text-red-400 font-semibold">{formatCurrency(results.avg_loss)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Sharpe Ratio:</span>
                      <span className="text-white font-semibold">{results.sharpe_ratio}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Profit Factor:</span>
                      <span className="text-white font-semibold">{results.profit_factor}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-400 mb-2">Capital</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Initial:</span>
                      <span className="text-white font-semibold">{formatCurrency(results.initial_capital)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Final:</span>
                      <span className="text-white font-semibold">{formatCurrency(results.final_capital)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Return:</span>
                      <span className={`font-semibold ${results.total_pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {results.total_pnl_percent >= 0 ? '+' : ''}{results.total_pnl_percent}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Max DD:</span>
                      <span className="text-orange-400 font-semibold">-{results.max_drawdown_percent}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendation */}
            <div className={`rounded-lg p-6 border ${
              results.win_rate >= 60 && results.total_pnl > 0 && results.max_drawdown_percent < 20
                ? 'bg-green-500/10 border-green-500'
                : results.total_pnl > 0
                ? 'bg-blue-500/10 border-blue-500'
                : 'bg-red-500/10 border-red-500'
            }`}>
              <div className="flex items-start gap-3">
                {results.win_rate >= 60 && results.total_pnl > 0 && results.max_drawdown_percent < 20 ? (
                  <>
                    <CheckCircle className="w-6 h-6 text-green-400 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-white mb-1">Excellent Strategy Performance! ✅</h4>
                      <p className="text-sm text-gray-300">
                        This strategy shows strong performance with {results.win_rate}% win rate and low drawdown.
                        Consider running it live with real capital!
                      </p>
                    </div>
                  </>
                ) : results.total_pnl > 0 ? (
                  <>
                    <Info className="w-6 h-6 text-blue-400 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-white mb-1">Moderate Performance</h4>
                      <p className="text-sm text-gray-300">
                        Strategy is profitable but consider optimizing parameters or trying different timeframes.
                        Test with paper trading first.
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-6 h-6 text-red-400 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-white mb-1">Poor Performance</h4>
                      <p className="text-sm text-gray-300">
                        Strategy lost money in this backtest. Try adjusting parameters, different strategy, or different market conditions.
                        DO NOT trade this configuration live.
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>
          </>
        )}

      </div>
    </div>
  )
}
