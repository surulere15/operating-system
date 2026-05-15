'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Award,
  Activity,
  Filter,
  Download,
  RefreshCcw,
  X,
  ChevronLeft,
  ChevronRight
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
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Trade {
  id: number
  bot_id: number
  bot_name: string
  exchange: string
  symbol: string
  side: 'buy' | 'sell'
  entry_price: number
  exit_price: number | null
  quantity: number
  leverage: number
  pnl: number | null
  pnl_percent: number | null
  status: 'open' | 'closed' | 'cancelled'
  opened_at: string
  closed_at: string | null
  stop_loss: number | null
  take_profit: number | null
}

interface Stats {
  total_trades: number
  open_positions: number
  total_pnl: number
  total_pnl_percent: number
  win_rate: number
  best_trade: number
  worst_trade: number
  avg_trade_duration: number
  total_volume: number
}

export default function TradesPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [trades, setTrades] = useState<Trade[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [bots, setBots] = useState<any[]>([])

  // Filters
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({
    exchange: 'all',
    bot_id: 'all',
    status: 'all',
    date_from: '',
    date_to: ''
  })

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const tradesPerPage = 20

  useEffect(() => {
    loadData()
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }

    try {
      const headers = { Authorization: `Bearer ${token}` }
      const [tradesRes, statsRes, botsRes] = await Promise.all([
        axios.get(`${API_URL}/api/trades`, { headers }),
        axios.get(`${API_URL}/api/trades/stats`, { headers }),
        axios.get(`${API_URL}/api/bots`, { headers })
      ])

      setTrades(tradesRes.data)
      setStats(statsRes.data)
      setBots(botsRes.data)
    } catch (err: any) {
      console.error('Failed to load trades:', err)
      if (err.response?.status === 401) {
        router.push('/login')
      }
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

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  const formatDate = (date: string) => {
    return new Date(date).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const exportToCSV = () => {
    const filteredTrades = getFilteredTrades()
    const csv = [
      ['ID', 'Bot', 'Exchange', 'Symbol', 'Side', 'Entry Price', 'Exit Price', 'Quantity', 'Leverage', 'P&L', 'P&L %', 'Status', 'Opened', 'Closed'],
      ...filteredTrades.map(t => [
        t.id,
        t.bot_name,
        t.exchange,
        t.symbol,
        t.side,
        t.entry_price,
        t.exit_price || '',
        t.quantity,
        t.leverage,
        t.pnl || '',
        t.pnl_percent || '',
        t.status,
        t.opened_at,
        t.closed_at || ''
      ])
    ].map(row => row.join(',')).join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `trades_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
  }

  const getFilteredTrades = () => {
    return trades.filter(trade => {
      if (filters.exchange !== 'all' && trade.exchange !== filters.exchange) return false
      if (filters.bot_id !== 'all' && trade.bot_id.toString() !== filters.bot_id) return false
      if (filters.status !== 'all' && trade.status !== filters.status) return false
      if (filters.date_from && new Date(trade.opened_at) < new Date(filters.date_from)) return false
      if (filters.date_to && new Date(trade.opened_at) > new Date(filters.date_to)) return false
      return true
    })
  }

  const getPaginatedTrades = () => {
    const filtered = getFilteredTrades()
    const startIdx = (currentPage - 1) * tradesPerPage
    return filtered.slice(startIdx, startIdx + tradesPerPage)
  }

  const getTotalPages = () => {
    return Math.ceil(getFilteredTrades().length / tradesPerPage)
  }

  // Chart data
  const getPnLChartData = () => {
    const closedTrades = trades
      .filter(t => t.status === 'closed' && t.closed_at)
      .sort((a, b) => new Date(a.closed_at!).getTime() - new Date(b.closed_at!).getTime())

    let cumulative = 0
    return closedTrades.map(trade => {
      cumulative += trade.pnl || 0
      return {
        date: new Date(trade.closed_at!).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        pnl: parseFloat(cumulative.toFixed(2)),
        trade_pnl: parseFloat((trade.pnl || 0).toFixed(2))
      }
    })
  }

  const getWinLossData = () => {
    const closedTrades = trades.filter(t => t.status === 'closed')
    const wins = closedTrades.filter(t => (t.pnl || 0) > 0).length
    const losses = closedTrades.filter(t => (t.pnl || 0) <= 0).length

    return [
      { name: 'Wins', value: wins, color: '#10b981' },
      { name: 'Losses', value: losses, color: '#ef4444' }
    ]
  }

  const getExchangeBreakdown = () => {
    const breakdown: { [key: string]: number } = {}
    trades.forEach(t => {
      breakdown[t.exchange] = (breakdown[t.exchange] || 0) + 1
    })

    return Object.entries(breakdown).map(([exchange, count]) => ({
      exchange: exchange.toUpperCase(),
      trades: count
    }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCcw className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading trades...</p>
        </div>
      </div>
    )
  }

  const openPositions = trades.filter(t => t.status === 'open')
  const pnlChartData = getPnLChartData()
  const winLossData = getWinLossData()
  const exchangeData = getExchangeBreakdown()

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Trade Dashboard</h1>
            <p className="text-gray-400">Track your trading performance in real-time</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition flex items-center gap-2"
            >
              <Filter className="w-4 h-4" />
              Filters
            </button>
            <button
              onClick={exportToCSV}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
            <button
              onClick={loadData}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition flex items-center gap-2"
            >
              <RefreshCcw className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-white">Filter Trades</h3>
              <button
                onClick={() => setShowFilters(false)}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Exchange</label>
                <select
                  value={filters.exchange}
                  onChange={(e) => setFilters({ ...filters, exchange: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                >
                  <option value="all">All Exchanges</option>
                  <option value="bybit">Bybit</option>
                  <option value="binance">Binance</option>
                  <option value="okx">OKX</option>
                  <option value="kraken">Kraken</option>
                  <option value="coinbase">Coinbase</option>
                  <option value="kucoin">KuCoin</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Bot</label>
                <select
                  value={filters.bot_id}
                  onChange={(e) => setFilters({ ...filters, bot_id: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                >
                  <option value="all">All Bots</option>
                  {bots.map(bot => (
                    <option key={bot.id} value={bot.id}>{bot.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Status</label>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                >
                  <option value="all">All Statuses</option>
                  <option value="open">Open</option>
                  <option value="closed">Closed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">From Date</label>
                <input
                  type="date"
                  value={filters.date_from}
                  onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">To Date</label>
                <input
                  type="date"
                  value={filters.date_to}
                  onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                />
              </div>
            </div>

            <button
              onClick={() => setFilters({ exchange: 'all', bot_id: 'all', status: 'all', date_from: '', date_to: '' })}
              className="mt-4 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition text-sm"
            >
              Clear Filters
            </button>
          </div>
        )}

        {/* Performance Metrics */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-lg p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className="text-green-100 text-sm font-medium">Total P&L</p>
                  <h3 className={`text-3xl font-bold mt-1 ${stats.total_pnl >= 0 ? 'text-white' : 'text-red-200'}`}>
                    {formatCurrency(stats.total_pnl)}
                  </h3>
                  <p className={`text-sm mt-1 ${stats.total_pnl_percent >= 0 ? 'text-green-100' : 'text-red-200'}`}>
                    {formatPercent(stats.total_pnl_percent)}
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
                    {stats.win_rate.toFixed(1)}%
                  </h3>
                  <p className="text-blue-100 text-sm mt-1">
                    {stats.total_trades} total trades
                  </p>
                </div>
                <Target className="w-10 h-10 text-blue-100" />
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-lg p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className="text-purple-100 text-sm font-medium">Best Trade</p>
                  <h3 className="text-3xl font-bold text-white mt-1">
                    {formatCurrency(stats.best_trade)}
                  </h3>
                  <p className="text-purple-100 text-sm mt-1">Single trade profit</p>
                </div>
                <Award className="w-10 h-10 text-purple-100" />
              </div>
            </div>

            <div className="bg-gradient-to-br from-orange-600 to-orange-700 rounded-lg p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className="text-orange-100 text-sm font-medium">Open Positions</p>
                  <h3 className="text-3xl font-bold text-white mt-1">
                    {stats.open_positions}
                  </h3>
                  <p className="text-orange-100 text-sm mt-1">Active trades</p>
                </div>
                <Activity className="w-10 h-10 text-orange-100" />
              </div>
            </div>
          </div>
        )}

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Cumulative P&L Chart */}
          <div className="lg:col-span-2 bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">Cumulative P&L</h3>
            {pnlChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={pnlChartData}>
                  <defs>
                    <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="pnl"
                    stroke="#10b981"
                    strokeWidth={2}
                    fill="url(#colorPnl)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-gray-400">
                No trade data available
              </div>
            )}
          </div>

          {/* Win/Loss Pie Chart */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">Win/Loss Ratio</h3>
            {winLossData.length > 0 && winLossData.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={winLossData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {winLossData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-gray-400">
                No closed trades yet
              </div>
            )}
          </div>
        </div>

        {/* Exchange Breakdown */}
        {exchangeData.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">Trading Activity by Exchange</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={exchangeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="exchange" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                  labelStyle={{ color: '#fff' }}
                />
                <Bar dataKey="trades" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Active Positions */}
        {openPositions.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">
              Active Positions ({openPositions.length})
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-3 px-4 text-gray-300 font-medium">Bot</th>
                    <th className="text-left py-3 px-4 text-gray-300 font-medium">Exchange</th>
                    <th className="text-left py-3 px-4 text-gray-300 font-medium">Symbol</th>
                    <th className="text-left py-3 px-4 text-gray-300 font-medium">Side</th>
                    <th className="text-right py-3 px-4 text-gray-300 font-medium">Entry</th>
                    <th className="text-right py-3 px-4 text-gray-300 font-medium">Quantity</th>
                    <th className="text-right py-3 px-4 text-gray-300 font-medium">Leverage</th>
                    <th className="text-left py-3 px-4 text-gray-300 font-medium">Opened</th>
                  </tr>
                </thead>
                <tbody>
                  {openPositions.map(trade => (
                    <tr key={trade.id} className="border-b border-gray-700 hover:bg-gray-750 transition">
                      <td className="py-3 px-4 text-white">{trade.bot_name}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-sm">
                          {trade.exchange.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-white font-medium">{trade.symbol}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-sm font-semibold ${
                          trade.side === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                        }`}>
                          {trade.side.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-white">{formatCurrency(trade.entry_price)}</td>
                      <td className="py-3 px-4 text-right text-gray-300">{trade.quantity}</td>
                      <td className="py-3 px-4 text-right text-gray-300">{trade.leverage}x</td>
                      <td className="py-3 px-4 text-gray-400 text-sm">{formatDate(trade.opened_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Trade History */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-white">
              Trade History ({getFilteredTrades().length} trades)
            </h3>
            {getTotalPages() > 1 && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="p-2 bg-gray-700 hover:bg-gray-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-gray-400 text-sm">
                  Page {currentPage} of {getTotalPages()}
                </span>
                <button
                  onClick={() => setCurrentPage(Math.min(getTotalPages(), currentPage + 1))}
                  disabled={currentPage === getTotalPages()}
                  className="p-2 bg-gray-700 hover:bg-gray-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-3 px-4 text-gray-300 font-medium">Bot</th>
                  <th className="text-left py-3 px-4 text-gray-300 font-medium">Exchange</th>
                  <th className="text-left py-3 px-4 text-gray-300 font-medium">Symbol</th>
                  <th className="text-left py-3 px-4 text-gray-300 font-medium">Side</th>
                  <th className="text-right py-3 px-4 text-gray-300 font-medium">Entry</th>
                  <th className="text-right py-3 px-4 text-gray-300 font-medium">Exit</th>
                  <th className="text-right py-3 px-4 text-gray-300 font-medium">P&L</th>
                  <th className="text-right py-3 px-4 text-gray-300 font-medium">P&L %</th>
                  <th className="text-left py-3 px-4 text-gray-300 font-medium">Status</th>
                  <th className="text-left py-3 px-4 text-gray-300 font-medium">Opened</th>
                </tr>
              </thead>
              <tbody>
                {getPaginatedTrades().length > 0 ? (
                  getPaginatedTrades().map(trade => (
                    <tr key={trade.id} className="border-b border-gray-700 hover:bg-gray-750 transition">
                      <td className="py-3 px-4 text-white">{trade.bot_name}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-sm">
                          {trade.exchange.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-white font-medium">{trade.symbol}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-sm font-semibold ${
                          trade.side === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                        }`}>
                          {trade.side.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-white">{formatCurrency(trade.entry_price)}</td>
                      <td className="py-3 px-4 text-right text-white">
                        {trade.exit_price ? formatCurrency(trade.exit_price) : '-'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {trade.pnl !== null ? (
                          <span className={trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                            {formatCurrency(trade.pnl)}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {trade.pnl_percent !== null ? (
                          <span className={trade.pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}>
                            {formatPercent(trade.pnl_percent)}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          trade.status === 'open' ? 'bg-blue-500/20 text-blue-400' :
                          trade.status === 'closed' ? 'bg-green-500/20 text-green-400' :
                          'bg-gray-500/20 text-gray-400'
                        }`}>
                          {trade.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-400 text-sm">{formatDate(trade.opened_at)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={10} className="py-8 text-center text-gray-400">
                      No trades found. Start a bot to see trades here!
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  )
}
