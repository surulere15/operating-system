'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Activity,
  PieChart,
  BarChart3,
  Calendar,
  Target,
  AlertTriangle,
  Award,
  Clock,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart as RechartsPie,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Bot {
  id: number;
  name: string;
  status: string;
  exchange: string;
  capital: number;
  current_balance: number;
  total_pnl: number;
  total_trades: number;
  winning_trades: number;
}

interface Trade {
  id: number;
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  opened_at: string;
  closed_at: string;
  status: string;
}

interface PortfolioMetrics {
  total_value: number;
  total_invested: number;
  total_pnl: number;
  total_pnl_percent: number;
  total_trades: number;
  win_rate: number;
  sharpe_ratio: number;
  max_drawdown: number;
  max_drawdown_percent: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  best_trade: number;
  worst_trade: number;
}

const COLORS = ['#8b5cf6', '#ec4899', '#10b981', '#f59e0b', '#3b82f6', '#ef4444'];

export default function PortfolioPage() {
  const router = useRouter();
  const [bots, setBots] = useState<Bot[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [metrics, setMetrics] = useState<PortfolioMetrics | null>(null);
  const [equityCurve, setEquityCurve] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d');

  useEffect(() => {
    fetchPortfolioData();
  }, [timeRange]);

  const fetchPortfolioData = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [botsRes, tradesRes, statsRes] = await Promise.all([
        axios.get(`${API_URL}/api/bots`, { headers }),
        axios.get(`${API_URL}/api/trades?limit=100`, { headers }),
        axios.get(`${API_URL}/api/trades/stats`, { headers })
      ]);

      setBots(botsRes.data);
      setTrades(tradesRes.data);

      // Calculate comprehensive metrics
      const calculatedMetrics = calculateMetrics(botsRes.data, tradesRes.data);
      setMetrics(calculatedMetrics);

      // Generate equity curve
      const equity = generateEquityCurve(tradesRes.data, calculatedMetrics.total_invested);
      setEquityCurve(equity);

    } catch (error: any) {
      console.error('Failed to fetch portfolio data:', error);
      if (error.response?.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const calculateMetrics = (bots: Bot[], trades: Trade[]): PortfolioMetrics => {
    const totalInvested = bots.reduce((sum, bot) => sum + bot.capital, 0);
    const totalValue = bots.reduce((sum, bot) => sum + bot.current_balance, 0);
    const totalPnL = totalValue - totalInvested;
    const totalPnLPercent = totalInvested > 0 ? (totalPnL / totalInvested) * 100 : 0;

    const closedTrades = trades.filter(t => t.status === 'closed' && t.pnl !== null);
    const winningTrades = closedTrades.filter(t => t.pnl > 0);
    const losingTrades = closedTrades.filter(t => t.pnl <= 0);

    const winRate = closedTrades.length > 0 ? (winningTrades.length / closedTrades.length) * 100 : 0;
    const avgWin = winningTrades.length > 0 ? winningTrades.reduce((sum, t) => sum + t.pnl, 0) / winningTrades.length : 0;
    const avgLoss = losingTrades.length > 0 ? losingTrades.reduce((sum, t) => sum + t.pnl, 0) / losingTrades.length : 0;

    const grossProfit = winningTrades.reduce((sum, t) => sum + t.pnl, 0);
    const grossLoss = Math.abs(losingTrades.reduce((sum, t) => sum + t.pnl, 0));
    const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : 0;

    const bestTrade = closedTrades.length > 0 ? Math.max(...closedTrades.map(t => t.pnl)) : 0;
    const worstTrade = closedTrades.length > 0 ? Math.min(...closedTrades.map(t => t.pnl)) : 0;

    // Calculate Sharpe ratio (simplified)
    const returns = closedTrades.map(t => (t.pnl / totalInvested) * 100);
    const avgReturn = returns.length > 0 ? returns.reduce((a, b) => a + b, 0) / returns.length : 0;
    const stdDev = returns.length > 0 ? Math.sqrt(returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length) : 0;
    const sharpeRatio = stdDev > 0 ? (avgReturn / stdDev) * Math.sqrt(252) : 0; // Annualized

    // Calculate max drawdown
    let peak = totalInvested;
    let maxDD = 0;
    let runningTotal = totalInvested;

    closedTrades.forEach(trade => {
      runningTotal += trade.pnl;
      if (runningTotal > peak) peak = runningTotal;
      const dd = peak - runningTotal;
      if (dd > maxDD) maxDD = dd;
    });

    const maxDDPercent = peak > 0 ? (maxDD / peak) * 100 : 0;

    return {
      total_value: totalValue,
      total_invested: totalInvested,
      total_pnl: totalPnL,
      total_pnl_percent: totalPnLPercent,
      total_trades: closedTrades.length,
      win_rate: winRate,
      sharpe_ratio: sharpeRatio,
      max_drawdown: maxDD,
      max_drawdown_percent: maxDDPercent,
      avg_win: avgWin,
      avg_loss: avgLoss,
      profit_factor: profitFactor,
      best_trade: bestTrade,
      worst_trade: worstTrade
    };
  };

  const generateEquityCurve = (trades: Trade[], initialCapital: number) => {
    const closedTrades = trades
      .filter(t => t.status === 'closed' && t.closed_at)
      .sort((a, b) => new Date(a.closed_at).getTime() - new Date(b.closed_at).getTime());

    let equity = initialCapital;
    const curve = [{ date: 'Start', equity: initialCapital, pnl: 0 }];

    closedTrades.forEach((trade, index) => {
      equity += trade.pnl;
      curve.push({
        date: new Date(trade.closed_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        equity: parseFloat(equity.toFixed(2)),
        pnl: trade.pnl
      });
    });

    return curve;
  };

  const getBotAllocation = () => {
    return bots.map(bot => ({
      name: bot.name,
      value: bot.current_balance,
      percent: metrics ? (bot.current_balance / metrics.total_value) * 100 : 0
    }));
  };

  const getExchangeAllocation = () => {
    const byExchange = bots.reduce((acc, bot) => {
      acc[bot.exchange] = (acc[bot.exchange] || 0) + bot.current_balance;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(byExchange).map(([exchange, value]) => ({
      name: exchange.toUpperCase(),
      value,
      percent: metrics ? (value / metrics.total_value) * 100 : 0
    }));
  };

  const getMonthlyReturns = () => {
    const closedTrades = trades.filter(t => t.status === 'closed' && t.closed_at);
    const byMonth: Record<string, number> = {};

    closedTrades.forEach(trade => {
      const month = new Date(trade.closed_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
      byMonth[month] = (byMonth[month] || 0) + trade.pnl;
    });

    return Object.entries(byMonth)
      .map(([month, pnl]) => ({ month, pnl: parseFloat(pnl.toFixed(2)) }))
      .slice(-12); // Last 12 months
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center text-white">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
            <p className="mt-4">Loading portfolio analytics...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  const botAllocation = getBotAllocation();
  const exchangeAllocation = getExchangeAllocation();
  const monthlyReturns = getMonthlyReturns();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <PieChart className="w-8 h-8 text-purple-400" />
            <h1 className="text-3xl font-bold text-white">Portfolio Analytics</h1>
          </div>
          <p className="text-gray-300">
            Comprehensive performance metrics and portfolio insights
          </p>
        </div>

        {/* Key Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <DollarSign className="w-6 h-6 text-purple-400" />
              </div>
              {metrics.total_pnl_percent >= 0 ? (
                <ArrowUpRight className="w-5 h-5 text-green-400" />
              ) : (
                <ArrowDownRight className="w-5 h-5 text-red-400" />
              )}
            </div>
            <div className="text-gray-400 text-sm mb-1">Portfolio Value</div>
            <div className="text-2xl font-bold text-white mb-1">
              ${metrics.total_value.toFixed(2)}
            </div>
            <div className={`text-sm font-semibold ${metrics.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {metrics.total_pnl >= 0 ? '+' : ''}${metrics.total_pnl.toFixed(2)} ({metrics.total_pnl_percent >= 0 ? '+' : ''}{metrics.total_pnl_percent.toFixed(2)}%)
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-green-500/20 rounded-lg">
                <Target className="w-6 h-6 text-green-400" />
              </div>
              <Award className="w-5 h-5 text-yellow-400" />
            </div>
            <div className="text-gray-400 text-sm mb-1">Win Rate</div>
            <div className="text-2xl font-bold text-white mb-1">
              {metrics.win_rate.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-400">
              {metrics.total_trades} trades executed
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <BarChart3 className="w-6 h-6 text-blue-400" />
              </div>
            </div>
            <div className="text-gray-400 text-sm mb-1">Sharpe Ratio</div>
            <div className={`text-2xl font-bold ${metrics.sharpe_ratio > 1 ? 'text-green-400' : metrics.sharpe_ratio > 0 ? 'text-yellow-400' : 'text-red-400'}`}>
              {metrics.sharpe_ratio.toFixed(2)}
            </div>
            <div className="text-sm text-gray-400">
              {metrics.sharpe_ratio > 1 ? 'Excellent' : metrics.sharpe_ratio > 0 ? 'Good' : 'Poor'} risk-adjusted return
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-red-500/20 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-red-400" />
              </div>
            </div>
            <div className="text-gray-400 text-sm mb-1">Max Drawdown</div>
            <div className="text-2xl font-bold text-red-400">
              {metrics.max_drawdown_percent.toFixed(2)}%
            </div>
            <div className="text-sm text-gray-400">
              ${metrics.max_drawdown.toFixed(2)} peak decline
            </div>
          </div>
        </div>

        {/* Equity Curve */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-400" />
              Equity Curve
            </h2>
            <div className="flex gap-2">
              {['7d', '30d', '90d', 'all'].map(range => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range as any)}
                  className={`px-3 py-1 rounded-lg text-sm font-semibold transition ${
                    timeRange === range
                      ? 'bg-purple-500 text-white'
                      : 'bg-white/10 text-gray-400 hover:bg-white/20'
                  }`}
                >
                  {range.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={equityCurve}>
              <defs>
                <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                labelStyle={{ color: '#fff' }}
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

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          {/* Bot Allocation */}
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <PieChart className="w-5 h-5 text-purple-400" />
              Bot Allocation
            </h2>

            <div className="flex items-center justify-center mb-6">
              <ResponsiveContainer width="100%" height={200}>
                <RechartsPie>
                  <Pie
                    data={botAllocation}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {botAllocation.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                  />
                </RechartsPie>
              </ResponsiveContainer>
            </div>

            <div className="space-y-3">
              {botAllocation.map((bot, index) => (
                <div key={bot.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span className="text-gray-300 text-sm">{bot.name}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-semibold text-sm">
                      ${bot.value.toFixed(2)}
                    </div>
                    <div className="text-gray-400 text-xs">
                      {bot.percent.toFixed(1)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Exchange Allocation */}
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-400" />
              Exchange Allocation
            </h2>

            <div className="flex items-center justify-center mb-6">
              <ResponsiveContainer width="100%" height={200}>
                <RechartsPie>
                  <Pie
                    data={exchangeAllocation}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {exchangeAllocation.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                  />
                </RechartsPie>
              </ResponsiveContainer>
            </div>

            <div className="space-y-3">
              {exchangeAllocation.map((exchange, index) => (
                <div key={exchange.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span className="text-gray-300 text-sm">{exchange.name}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-semibold text-sm">
                      ${exchange.value.toFixed(2)}
                    </div>
                    <div className="text-gray-400 text-xs">
                      {exchange.percent.toFixed(1)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Monthly Returns */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10 mb-8">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-yellow-400" />
            Monthly Returns
          </h2>

          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={monthlyReturns}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="month" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="pnl" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Advanced Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="text-gray-400 text-sm mb-1">Profit Factor</div>
            <div className={`text-xl font-bold ${metrics.profit_factor > 1 ? 'text-green-400' : 'text-red-400'}`}>
              {metrics.profit_factor.toFixed(2)}
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="text-gray-400 text-sm mb-1">Avg Win</div>
            <div className="text-xl font-bold text-green-400">
              +${metrics.avg_win.toFixed(2)}
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="text-gray-400 text-sm mb-1">Avg Loss</div>
            <div className="text-xl font-bold text-red-400">
              ${metrics.avg_loss.toFixed(2)}
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="text-gray-400 text-sm mb-1">Best Trade</div>
            <div className="text-xl font-bold text-green-400">
              +${metrics.best_trade.toFixed(2)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
