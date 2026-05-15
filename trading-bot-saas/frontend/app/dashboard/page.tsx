'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import axios from 'axios'
import { TrendingUp, TrendingDown, Activity, DollarSign, Play, Pause, Plus, Settings, BarChart, Trophy, Copy, Bell, CreditCard, Key, PieChart, LineChart, Store, Award, Brain, User } from 'lucide-react'
import CreateBotModal from '@/components/CreateBotModal'
import OnboardingWizard from '@/components/OnboardingWizard'
import OnboardingChecklist from '@/components/OnboardingChecklist'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface User {
  id: number
  email: string
  full_name: string
  tier: string
  subscription_status: string
}

interface Bot {
  id: number
  name: string
  status: string
  exchange: string
  capital: number
  current_balance: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  total_pnl: number
  created_at: string
  last_trade_at: string | null
}

interface TradeStats {
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  total_pnl: number
}

export default function Dashboard() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [bots, setBots] = useState<Bot[]>([])
  const [stats, setStats] = useState<TradeStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [showCreateBot, setShowCreateBot] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [showChecklist, setShowChecklist] = useState(true)
  const [apiKeys, setApiKeys] = useState<any[]>([])

  // Check if first-time user
  useEffect(() => {
    const hasSeenOnboarding = localStorage.getItem('hasSeenOnboarding')
    if (!hasSeenOnboarding) {
      setShowOnboarding(true)
    }
  }, [])

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/')
      return
    }

    try {
      const headers = { Authorization: `Bearer ${token}` }

      // Load user, bots, stats, and API keys in parallel
      const [userRes, botsRes, statsRes, apiKeysRes] = await Promise.all([
        axios.get(`${API_URL}/api/auth/me`, { headers }),
        axios.get(`${API_URL}/api/bots`, { headers }),
        axios.get(`${API_URL}/api/trades/stats`, { headers }),
        axios.get(`${API_URL}/api/api-keys`, { headers })
      ])

      setUser(userRes.data)
      setBots(botsRes.data)
      setStats(statsRes.data)
      setApiKeys(apiKeysRes.data)
    } catch (err) {
      console.error('Failed to load dashboard:', err)
      localStorage.removeItem('token')
      router.push('/')
    } finally {
      setLoading(false)
    }
  }

  const toggleBot = async (botId: number, currentStatus: string) => {
    const token = localStorage.getItem('token')
    const action = currentStatus === 'active' ? 'stop' : 'start'

    try {
      await axios.post(
        `${API_URL}/api/bots/${botId}/${action}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )
      loadDashboard() // Reload
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to toggle bot')
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-white">Trading Bot Dashboard</h1>
              <p className="text-gray-400 text-sm">
                {user?.full_name} • {user?.tier.toUpperCase()} Plan
              </p>
            </div>
            <button
              onClick={logout}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-gray-800/50 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2 overflow-x-auto py-3">
            <Link
              href="/dashboard"
              className="flex items-center gap-2 px-4 py-2 text-white bg-blue-600 rounded-lg font-medium whitespace-nowrap hover:bg-blue-700 transition"
            >
              <Activity className="w-4 h-4" />
              Dashboard
            </Link>
            <Link
              href="/dashboard/trader-profile"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <User className="w-4 h-4" />
              Trader Profile
            </Link>
            <Link
              href="/dashboard/portfolio"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <PieChart className="w-4 h-4" />
              Portfolio
            </Link>
            <Link
              href="/dashboard/risk"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <Settings className="w-4 h-4" />
              Risk
            </Link>
            <Link
              href="/dashboard/backtest"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <BarChart className="w-4 h-4" />
              Backtest
            </Link>
            <Link
              href="/dashboard/leaderboard"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <Trophy className="w-4 h-4" />
              Leaderboard
            </Link>
            <Link
              href="/dashboard/competitions"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <Award className="w-4 h-4" />
              Competitions
            </Link>
            <Link
              href="/dashboard/copy-trading"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <Copy className="w-4 h-4" />
              Copy Trading
            </Link>
            <Link
              href="/dashboard/charts"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <LineChart className="w-4 h-4" />
              Charts
            </Link>
            <Link
              href="/dashboard/ai"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <Brain className="w-4 h-4" />
              AI Analysis
            </Link>
            <Link
              href="/dashboard/marketplace"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <Store className="w-4 h-4" />
              Marketplace
            </Link>
            <Link
              href="/dashboard/alerts"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <Bell className="w-4 h-4" />
              Alerts
            </Link>
            <Link
              href="/dashboard/trades"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <TrendingUp className="w-4 h-4" />
              Trades
            </Link>
            <Link
              href="/dashboard/notifications"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <Bell className="w-4 h-4" />
              Notifications
            </Link>
            <Link
              href="/dashboard/developer"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <Key className="w-4 h-4" />
              Developer
            </Link>
            <Link
              href="/dashboard/tax"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <Settings className="w-4 h-4" />
              Tax
            </Link>
            <Link
              href="/dashboard/billing"
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg font-medium whitespace-nowrap transition"
            >
              <CreditCard className="w-4 h-4" />
              Billing
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<Activity className="w-6 h-6" />}
            label="Total Trades"
            value={stats?.total_trades || 0}
            color="blue"
          />
          <StatCard
            icon={<TrendingUp className="w-6 h-6" />}
            label="Win Rate"
            value={`${stats?.win_rate || 0}%`}
            color="green"
          />
          <StatCard
            icon={<DollarSign className="w-6 h-6" />}
            label="Total PnL"
            value={`$${stats?.total_pnl.toFixed(2) || '0.00'}`}
            color={stats && stats.total_pnl >= 0 ? 'green' : 'red'}
          />
          <StatCard
            icon={<TrendingDown className="w-6 h-6" />}
            label="Active Bots"
            value={bots.filter(b => b.status === 'active').length}
            color="purple"
          />
        </div>

        {/* Onboarding Checklist - Industry Standard (75% abandon without progress indicator) */}
        {showChecklist && !loading && (
          <div className="mb-8">
            <OnboardingChecklist
              hasAPIKeys={apiKeys.length > 0}
              hasBots={bots.length > 0}
              hasActiveBots={bots.some(b => b.status === 'active')}
              hasTrades={stats ? stats.total_trades > 0 : false}
              onDismiss={() => setShowChecklist(false)}
            />
          </div>
        )}

        {/* Bots Section */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-white">Your Trading Bots</h2>
            <button
              onClick={() => setShowCreateBot(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
            >
              <Plus className="w-4 h-4" />
              Create Bot
            </button>
          </div>

          {bots.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-400 mb-4">No bots yet. Create your first trading bot!</p>
              <button
                onClick={() => setShowCreateBot(true)}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
              >
                Get Started
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {bots.map(bot => (
                <BotCard key={bot.id} bot={bot} onToggle={toggleBot} />
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <ActionCard
            title="API Keys"
            description="Manage exchange API keys"
            icon={<Settings className="w-8 h-8" />}
            onClick={() => router.push('/dashboard/api-keys')}
          />
          <ActionCard
            title="Trade History"
            description="View all past trades"
            icon={<Activity className="w-8 h-8" />}
            onClick={() => router.push('/dashboard/trades')}
          />
          <ActionCard
            title="Upgrade Plan"
            description="Unlock more features"
            icon={<TrendingUp className="w-8 h-8" />}
            onClick={() => router.push('/dashboard/billing')}
          />
        </div>
      </main>

      {/* Create Bot Modal */}
      {showCreateBot && (
        <CreateBotModal
          onClose={() => setShowCreateBot(false)}
          onSuccess={() => loadDashboard()}
        />
      )}

      {/* Onboarding Wizard - 3Commas Standard (multi-tier approach) */}
      {showOnboarding && (
        <OnboardingWizard
          onComplete={() => {
            setShowOnboarding(false)
            localStorage.setItem('hasSeenOnboarding', 'true')
          }}
          onSkip={() => {
            setShowOnboarding(false)
            localStorage.setItem('hasSeenOnboarding', 'true')
          }}
        />
      )}
    </div>
  )
}

// Stat Card Component
function StatCard({ icon, label, value, color }: any) {
  const colorClasses = {
    blue: 'bg-blue-500/10 text-blue-400',
    green: 'bg-green-500/10 text-green-400',
    red: 'bg-red-500/10 text-red-400',
    purple: 'bg-purple-500/10 text-purple-400'
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className={`w-12 h-12 rounded-lg ${colorClasses[color]} flex items-center justify-center mb-3`}>
        {icon}
      </div>
      <p className="text-gray-400 text-sm mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  )
}

// Bot Card Component
function BotCard({ bot, onToggle }: { bot: Bot; onToggle: (id: number, status: string) => void }) {
  const winRate = bot.total_trades > 0
    ? ((bot.winning_trades / bot.total_trades) * 100).toFixed(1)
    : '0.0'

  const isActive = bot.status === 'active'

  return (
    <div className="bg-gray-700 rounded-lg p-6 border border-gray-600">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">{bot.name}</h3>
          <p className="text-gray-400 text-sm">{bot.exchange.toUpperCase()}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
          isActive ? 'bg-green-500/20 text-green-400' : 'bg-gray-600 text-gray-300'
        }`}>
          {bot.status}
        </span>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Capital:</span>
          <span className="text-white font-semibold">${bot.capital.toFixed(2)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">PnL:</span>
          <span className={`font-semibold ${bot.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            ${bot.total_pnl.toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Win Rate:</span>
          <span className="text-white font-semibold">{winRate}%</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Trades:</span>
          <span className="text-white font-semibold">
            {bot.winning_trades}W / {bot.losing_trades}L
          </span>
        </div>
      </div>

      <button
        onClick={() => onToggle(bot.id, bot.status)}
        className={`w-full py-2 rounded-lg font-semibold transition flex items-center justify-center gap-2 ${
          isActive
            ? 'bg-red-600 hover:bg-red-700 text-white'
            : 'bg-green-600 hover:bg-green-700 text-white'
        }`}
      >
        {isActive ? (
          <>
            <Pause className="w-4 h-4" /> Stop Bot
          </>
        ) : (
          <>
            <Play className="w-4 h-4" /> Start Bot
          </>
        )}
      </button>
    </div>
  )
}

// Action Card Component
function ActionCard({ title, description, icon, onClick }: any) {
  return (
    <button
      onClick={onClick}
      className="bg-gray-800 hover:bg-gray-750 rounded-lg p-6 border border-gray-700 text-left transition"
    >
      <div className="text-blue-400 mb-3">{icon}</div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-400 text-sm">{description}</p>
    </button>
  )
}
